import os
import csv
import json
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
from google.generativeai import GenerativeModel, configure
from dotenv import load_dotenv
from database import create_connection, insert_upload
import sqlite3

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})  # Allow requests from localhost:3000
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helper function to extract data without pandas
def extract_data(filepath, sample_size=1000):
    try:
        if filepath.endswith(".csv"):
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                data = list(reader)
                sampled_data = data[:sample_size]
                # Convert sampled data to text for Gemini API
                text_data = "\n".join([",".join(row.values()) for row in sampled_data])
                # Infer column types
                dtypes = {}
                if data:
                    first_row = data[0]
                    for key, value in first_row.items():
                        try:
                            float(value)
                            dtypes[key] = "float64"
                        except ValueError:
                            dtypes[key] = "object"
                return data, text_data, dtypes
        elif filepath.endswith(".json"):
            with open(filepath, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    sampled_data = data[:sample_size]
                    text_data = json.dumps(sampled_data)
                    dtypes = {}
                    if data:
                        first_row = data[0]
                        for key, value in first_row.items():
                            if isinstance(value, (int, float)):
                                dtypes[key] = "float64"
                            else:
                                dtypes[key] = "object"
                    return data, text_data, dtypes
                else:
                    return [], json.dumps(data), {}
        else:
            raise ValueError("Unsupported file type: Only CSV and JSON are supported")
    except Exception as e:
        raise ValueError(f"Error processing file: {str(e)}")

# Helper function to get dataset summary without pandas
def get_dataset_summary(data, dtypes, max_rows_for_stats=10000):
    if not data:
        return {"summary": "Empty or non-tabular data"}
    
    data_limited = data[:max_rows_for_stats]
    summary = {
        "num_rows": len(data),
        "num_columns": len(data[0]) if data else 0,
        "columns": {}
    }
    
    if not data:
        return summary
    
    # Infer column stats
    columns = list(data[0].keys())
    for col in columns:
        values = [row[col] for row in data_limited]
        unique_values = len(set(values))
        missing_values = values.count("") + values.count(None)
        summary["columns"][col] = {
            "type": dtypes.get(col, "unknown"),
            "unique_values": unique_values,
            "missing_values": missing_values,
        }
        if dtypes.get(col) == "float64":
            numeric_values = [float(v) for v in values if v and v != ""]
            if numeric_values:
                mean = sum(numeric_values) / len(numeric_values)
                variance = sum((x - mean) ** 2 for x in numeric_values) / len(numeric_values)
                std = variance ** 0.5
                summary["columns"][col]["mean"] = mean
                summary["columns"][col]["std"] = std
        else:
            # Find the most common value
            value_counts = {}
            for v in values:
                value_counts[v] = value_counts.get(v, 0) + 1
            top_value = max(value_counts.items(), key=lambda x: x[1])[0] if value_counts else "N/A"
            summary["columns"][col]["top_value"] = top_value
    
    return summary

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)
    
    conn = create_connection()
    file_id = insert_upload(conn, file.filename, filepath)
    conn.close()
    
    return jsonify({"message": "File uploaded", "file_id": file_id, "filename": file.filename})

@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    file_id = data.get("file_id")
    question = data.get("question")
    
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filepath FROM uploads WHERE id = ?", (file_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return jsonify({"error": "File not found"}), 404
    
    filepath = result[0]
    
    try:
        data, text_data, dtypes = extract_data(filepath)
        summary = get_dataset_summary(data, dtypes)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    model = GenerativeModel("gemini-1.5-pro")
    
    try:
        prompt = f"Dataset Summary: {json.dumps(summary)}\n\nSample Data (first 1000 rows):\n{text_data}\n\nQuestion: {question}"
        response = model.generate_content([prompt])
        return jsonify({"answer": response.text})
    except Exception as e:
        return jsonify({"error": f"Error with Gemini API: {str(e)}"}), 500

@app.route("/data/<int:file_id>", methods=["GET"])
def get_data(file_id):
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 1000))
    
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filepath FROM uploads WHERE id = ?", (file_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return jsonify({"error": "File not found"}), 404
    
    filepath = result[0]
    
    try:
        data, _, dtypes = extract_data(filepath)
        summary = get_dataset_summary(data, dtypes)
        
        # Paginate the data
        start = (page - 1) * per_page
        end = start + per_page
        paginated_data = data[start:end]
        
        return jsonify({
            "data": paginated_data,
            "summary": summary,
            "total_rows": len(data),
            "page": page,
            "per_page": per_page
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True, port=5000)