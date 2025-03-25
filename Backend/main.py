import os
import json
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.generativeai import GenerativeModel, configure
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from database import create_connection, insert_upload
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
configure(api_key=GEMINI_API_KEY)

# Initialize Flask app
app = Flask(__name__)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")  # Default to Vite port
CORS(app, resources={r"/*": {"origins": FRONTEND_URL}})

# Configure upload settings
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB limit
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
SUPPORTED_EXTENSIONS = {".csv", ".json", ".xlsx", ".parquet"}

def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in SUPPORTED_EXTENSIONS

def extract_data(filepath, sample_size=100):
    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(filepath)
        elif ext == ".json":
            df = pd.read_json(filepath)
        elif ext == ".xlsx":
            df = pd.read_excel(filepath)
        elif ext == ".parquet":
            df = pd.read_parquet(filepath)
        else:
            return None, None, None, f"Unsupported file type: {ext}"

        sampled_df = df.head(sample_size)
        text_data = sampled_df.to_csv(index=False) if ext == ".csv" else sampled_df.to_json(orient="records")
        dtypes = df.dtypes.apply(lambda x: str(x)).to_dict()
        return df.to_dict(orient="records"), text_data, dtypes, None
    except Exception as e:
        return None, None, None, f"Error processing file: {str(e)}"

def get_dataset_summary(data, dtypes):
    if not data:
        return {"summary": "Empty or non-tabular data"}

    df = pd.DataFrame(data)
    summary = {
        "num_rows": df.shape[0],
        "num_columns": df.shape[1],
        "columns": {},
        "trends": [],
        "key_takeaways": []
    }

    numerical_cols = [col for col, dtype in dtypes.items() if "float" in dtype or "int" in dtype and "id" not in col.lower()]
    categorical_cols = [col for col, dtype in dtypes.items() if "object" in dtype or "category" in dtype]
    sales_col = next((col for col in numerical_cols if "amount" in col.lower() or "sales" in col.lower() or "revenue" in col.lower()), None)

    for col in df.columns:
        col_data = df[col].dropna()
        unique_values = col_data.nunique()
        missing_values = df[col].isna().sum()
        column_summary = {
            "type": dtypes.get(col, "unknown"),
            "unique_values": int(unique_values),
            "missing_values": int(missing_values),
        }
        if "float" in dtypes.get(col, "") or "int" in dtypes.get(col, ""):
            if not col_data.empty:
                column_summary["mean"] = float(col_data.mean())
                column_summary["std"] = float(col_data.std())
                column_summary["max"] = float(col_data.max())
                column_summary["min"] = float(col_data.min())
                if "date" in col.lower() and len(col_data) > 1:
                    trend = "increasing" if col_data.iloc[-1] > col_data.iloc[0] else "decreasing"
                    summary["trends"].append(f"{col} shows an {trend} trend.")
        else:
            column_summary["top_value"] = col_data.mode()[0] if not col_data.empty else "N/A"
        summary["columns"][col] = column_summary

    if sales_col:
        total_sales = df[sales_col].sum()
        summary["key_takeaways"].append(f"Total {sales_col}: ${total_sales:,.2f}")
        if "Category" in df.columns:
            top_category = df.groupby("Category")[sales_col].sum().idxmax()
            top_category_sales = df.groupby("Category")[sales_col].sum().max()
            summary["key_takeaways"].append(f"Top Category: '{top_category}' with ${top_category_sales:,.2f} in sales")
        if "Gender" in df.columns:
            male_sales = df[df["Gender"] == "Male"][sales_col].sum()
            female_sales = df[df["Gender"] == "Female"][sales_col].sum()
            summary["key_takeaways"].append(f"Male Spending: ${male_sales:,.2f} vs Female Spending: ${female_sales:,.2f}")
    if "Frequency of Purchases" in df.columns:
        top_freq = df["Frequency of Purchases"].mode()[0]
        summary["key_takeaways"].append(f"Most Common Purchase Frequency: '{top_freq}'")
    if "Review Rating" in df.columns:
        avg_rating = df["Review Rating"].mean()
        summary["key_takeaways"].append(f"Average Review Rating: {avg_rating:.2f} out of 5")
    if "Subscription Status" in df.columns:
        sub_rate = df["Subscription Status"].value_counts(normalize=True).get("Yes", 0) * 100
        summary["key_takeaways"].append(f"Subscription Rate: {sub_rate:.1f}% of customers")

    return summary

def generate_visualization_suggestions(summary, dtypes):
    df = pd.DataFrame.from_dict(summary.get("data", []))
    categorical_cols = [col for col, dtype in dtypes.items() if "object" in dtype or "category" in dtype]
    numerical_cols = [col for col, dtype in dtypes.items() if "float" in dtype or "int" in dtype and "id" not in col.lower()]
    date_cols = [col for col in df.columns if "date" in col.lower()]
    suggestions = []

    sales_col = next((col for col in numerical_cols if "amount" in col.lower() or "sales" in col.lower() or "revenue" in col.lower()), numerical_cols[0] if numerical_cols else None)

    try:
        model = GenerativeModel("gemini-1.0-pro")
        prompt = (
            f"Dataset Summary: {json.dumps(summary, indent=2)}\n\n"
            "Suggest the most effective chart types (e.g., Bar, Pie, Line, Doughnut) and specific columns to use for visualizations "
            "that provide actionable business insights. Focus on sales, revenue, or purchase trends. "
            "Format each suggestion as 'Use a <chart> chart for '<col1>' vs '<col2>' or '<col>'. "
            "Avoid using identifier columns like 'Customer ID' for numerical values."
        )
        response = model.generate_content([prompt])
        suggestions = response.text.split("\n")
    except Exception as e:
        logger.error(f"Visualization suggestion generation failed: {str(e)}")
        if categorical_cols and sales_col:
            suggestions.append(f"Use a Bar chart for 'Category' vs '{sales_col}'")
            suggestions.append(f"Use a Pie chart for 'Gender' vs '{sales_col}'")
            suggestions.append(f"Use a Doughnut chart for 'Category'")
        if date_cols and sales_col:
            suggestions.append(f"Use a Line chart for '{date_cols[0]}' vs '{sales_col}'")
        if categorical_cols and numerical_cols:
            suggestions.append(f"Use a Bar chart for 'Gender' vs 'Previous Purchases'")
        suggestions = [s for s in suggestions if s]

    return "\n".join(suggestions) if suggestions else "No suitable columns found for visualizations."

# Root route for health check
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to AI-BI Backend", "status": "running"}), 200

# Error handler for file size limit
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File too large. Max size is 16MB."}), 413

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": f"Unsupported file type. Allowed: {', '.join(SUPPORTED_EXTENSIONS)}"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    with create_connection() as conn:
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        try:
            file_id = insert_upload(conn, filename, filepath)
            return jsonify({"message": "File uploaded successfully", "file_id": file_id, "filename": filename})
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            return jsonify({"error": f"Database error: {str(e)}"}), 500

@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    file_id = data.get("file_id")
    question = data.get("question")

    if not file_id or not question:
        return jsonify({"error": "Missing file_id or question"}), 400

    with create_connection() as conn:
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT filepath FROM uploads WHERE id = ?", (file_id,))
            result = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    if not result:
        return jsonify({"error": "File not found"}), 404

    filepath = result[0]
    data, text_data, dtypes, error = extract_data(filepath)
    if error:
        return jsonify({"error": error}), 400

    summary = get_dataset_summary(data, dtypes)
    df = pd.DataFrame(data)

    try:
        model = GenerativeModel("gemini-1.0-pro")
        prompt = (
            f"Dataset Summary: {json.dumps(summary, indent=2)}\n\n"
            f"Sample Data (first 100 rows):\n{text_data}\n\n"
            f"Question: {question}"
        )
        response = model.generate_content([prompt])
        return jsonify({"answer": response.text})
    except Exception as e:
        logger.error(f"Gemini API failed: {str(e)}")
        question_lower = question.lower()
        numerical_cols = [col for col, dtype in dtypes.items() if "float" in dtype or "int" in dtype and "id" not in col.lower()]
        categorical_cols = [col for col, dtype in dtypes.items() if "object" in dtype or "category" in dtype]

        if "total" in question_lower:
            for col in numerical_cols:
                if col.lower() in question_lower or "sales" in question_lower:
                    total = df[col].sum()
                    return jsonify({"answer": f"The total {col} is ${total:.2f}."}), 200
            return jsonify({"answer": f"No numerical column found to compute total for '{question}'."}), 200

        if "top" in question_lower or "best" in question_lower:
            target_col = next((col for col in df.columns if any(word in col.lower() for word in question_lower.split())), None)
            if not target_col and "sales" in question_lower:
                target_col = next((col for col in numerical_cols if "sales" in col.lower() or "amount" in col.lower() or "revenue" in col.lower()), numerical_cols[0] if numerical_cols else None)

            if target_col:
                if target_col in numerical_cols:
                    top_value = df[target_col].max()
                    return jsonify({"answer": f"The highest {target_col} is ${top_value:.2f}."}), 200
                elif target_col in categorical_cols:
                    if numerical_cols:
                        sales_col = next((col for col in numerical_cols if "sales" in col.lower() or "amount" in col.lower() or "revenue" in col.lower()), numerical_cols[0])
                        top_cat = df.groupby(target_col)[sales_col].sum().idxmax()
                        top_sales = df.groupby(target_col)[sales_col].sum().max()
                        return jsonify({"answer": f"The top {target_col} is '{top_cat}' with ${top_sales:.2f} in {sales_col}."}), 200
                    else:
                        top_cat = df[target_col].mode()[0]
                        return jsonify({"answer": f"The most frequent {target_col} is '{top_cat}'."}), 200
            return jsonify({"answer": f"Unable to determine target column for '{question}'."}), 200

        return jsonify({"answer": f"AI processing unavailable. Please try again later."}), 200

@app.route("/data/<int:file_id>", methods=["GET"])
def get_data(file_id):
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 1000, type=int)

    if page < 1 or per_page < 1:
        return jsonify({"error": "Invalid page or per_page value"}), 400

    with create_connection() as conn:
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT filepath FROM uploads WHERE id = ?", (file_id,))
            result = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    if not result:
        return jsonify({"error": "File not found"}), 404

    filepath = result[0]
    data, _, dtypes, error = extract_data(filepath)
    if error:
        return jsonify({"error": error}), 400

    summary = get_dataset_summary(data, dtypes)
    total_rows = len(data)
    start = (page - 1) * per_page
    end = min(start + per_page, total_rows)
    paginated_data = data[start:end]

    visualization_suggestions = generate_visualization_suggestions(summary, dtypes)

    return jsonify({
        "data": paginated_data,
        "summary": summary,
        "total_rows": total_rows,
        "page": page,
        "per_page": per_page,
        "total_pages": (total_rows + per_page - 1) // per_page,
        "visualization_suggestions": visualization_suggestions
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)