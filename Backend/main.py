from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import sqlite3
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
import os
import time
from dotenv import load_dotenv
import google.generativeai as genai
import json
import re
import charset_normalizer

app = FastAPI()
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class Query(BaseModel):
    text: str

def get_db_connection():
    conn = sqlite3.connect("business_data.db", timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize an empty database; schema will be set dynamically on upload."""
    try:
        with get_db_connection() as conn:
            # Drop existing table to start fresh
            conn.execute("DROP TABLE IF EXISTS business_data")
            print("Dropped existing business_data table (if any).")
            # Table will be created dynamically on upload
            conn.commit()
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise

@app.on_event("startup")
async def startup_event():
    init_db()

def fetch_dashboard_data(dashboard, limit=1000):
    """Fetch and format data for a dashboard dynamically."""
    x_col = dashboard["x"]
    y_col = dashboard["y"]
    # Check if columns exist in the table
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(business_data)")
        columns = [row["name"] for row in cursor.fetchall()]
        if x_col not in columns or y_col not in columns:
            print(f"Invalid columns for dashboard: {x_col}, {y_col} not in {columns}")
            return []

    query = f"SELECT {x_col}, SUM({y_col}) as value FROM business_data GROUP BY {x_col} LIMIT {limit}"
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = [dict(row) for row in cursor.fetchall()]
        data = [{"name": row[x_col], "value": row["value"]} for row in results]
        print(f"Dashboard data for {dashboard['title']}: {data[:10]}... (limited to {limit})")
        return data
    except Exception as e:
        print(f"Error fetching dashboard data: {str(e)}")
        return []

def detect_encoding(file_path):
    """Detect the file's encoding."""
    with open(file_path, 'rb') as f:
        result = charset_normalizer.detect(f.read(10000))
    encoding = result['encoding'] or 'utf-8'
    print(f"Detected encoding for {file_path}: {encoding}")
    return encoding

def analyze_dataset(df):
    """Analyze a sample of the dataset dynamically."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    sample_df = df.sample(n=min(100, len(df)), random_state=42)
    columns = list(df.columns)
    prompt = f"""
    You are an AI analyst. Given a dataset sample with columns {columns}, provide:
    1. A summary of key insights based on this sample (e.g., totals, trends, top values).
    2. Suggested dashboards based on the columns (e.g., bar chart, line chart).
    Return a valid JSON object with 'insights' (text) and 'dashboards' (list of {{type, x, y, title}}).
    Ensure the response is strictly formatted as JSON, e.g., {{"insights": "text", "dashboards": [...]}}.
    Note: This is a sample of a larger dataset; extrapolate trends where possible.
    Dataset sample:\n{sample_df.describe().to_string()}\n{sample_df.head().to_string()}
    """
    try:
        response = model.generate_content(prompt)
        raw_response = response.text.strip()
        print(f"Raw Gemini response (analyze_dataset): {raw_response}")
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            print(f"Extracted JSON: {json_str}")
            analysis = json.loads(json_str)
            for dash in analysis["dashboards"]:
                dash["data"] = fetch_dashboard_data(dash)
            return analysis
        else:
            print("No JSON found in response")
            return {"insights": "Failed to analyze dataset.", "dashboards": []}
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}")
        return {"insights": "Failed to analyze dataset due to AI response formatting.", "dashboards": []}
    except Exception as e:
        print(f"Gemini error: {str(e)}")
        raise

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Uploads and analyzes any dataset dynamically."""
    try:
        timestamp = int(time.time())
        file_name = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        print(f"Saving file to {file_path}")
        with open(file_path, "wb") as f:
            f.write(await file.read())

        print(f"Reading file: {file_name}")
        chunk_size = 10000
        encoding = detect_encoding(file_path)
        try:
            if file_name.endswith(".csv"):
                df_chunks = pd.read_csv(file_path, chunksize=chunk_size, encoding=encoding)
            elif file_name.endswith(".xlsx"):
                df_chunks = pd.read_excel(file_path, chunksize=chunk_size)
            elif file_name.endswith(".json"):
                df_chunks = pd.read_json(file_path, chunksize=chunk_size, encoding=encoding)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format")
        except UnicodeDecodeError:
            print(f"UTF-8 failed, trying 'latin1' for {file_name}")
            encoding = 'latin1'
            if file_name.endswith(".csv"):
                df_chunks = pd.read_csv(file_path, chunksize=chunk_size, encoding=encoding)
            elif file_name.endswith(".xlsx"):
                df_chunks = pd.read_excel(file_path, chunksize=chunk_size)
            elif file_name.endswith(".json"):
                df_chunks = pd.read_json(file_path, chunksize=chunk_size, encoding=encoding)

        first_chunk = True
        sample_df = None
        with get_db_connection() as conn:
            for chunk in df_chunks:
                chunk.columns = [col.lower().replace(" ", "_") for col in chunk.columns]
                print(f"Processing chunk with {len(chunk)} rows")
                if first_chunk:
                    # Dynamically create table based on first chunk's schema
                    chunk.to_sql("business_data", conn, if_exists="replace", index=False)
                    sample_df = chunk
                    first_chunk = False
                    # Create indexes dynamically based on common column types
                    for col in chunk.columns:
                        if chunk[col].dtype in ['object', 'string']:  # Index categorical columns
                            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{col} ON business_data ({col})")
                    conn.commit()
                    print(f"Created table with columns: {list(chunk.columns)}")
                else:
                    chunk.to_sql("business_data", conn, if_exists="append", index=False)

        print("Analyzing with Gemini")
        analysis = analyze_dataset(sample_df)
        return {"message": f"File uploaded and saved at {file_path}", "analysis": analysis}
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

def interpret_query(query_text):
    """Converts natural language queries to SQL dynamically."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    # Get current table schema
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(business_data)")
        columns = [row["name"] for row in cursor.fetchall()]
    
    prompt = f"""
    You are an AI analyst for a table 'business_data' with columns: {columns}.
    For the query "{query_text}":
    1. Generate a SQL query that returns results in the format: [{{"column1": value, "column2": value}}, ...].
       For example, if columns include 'product' and 'sales', "What were total sales by product?" should return:
       [{{"product": "value", "total_sales": value}}, ...]
    2. Suggest a dashboard based on the columns (e.g., {{type: 'bar', x: 'column1', y: 'column2', title: 'Title'}}).
    Return a valid JSON object with 'sql' (string) and 'dashboard' (object).
    Ensure the response is strictly formatted as JSON, e.g., {{"sql": "query", "dashboard": {{...}}}}.
    Do not include any text outside the JSON structure.
    """
    try:
        response = model.generate_content(prompt)
        raw_response = response.text.strip()
        print(f"Raw Gemini response (interpret_query): {raw_response}")
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            print(f"Extracted JSON: {json_str}")
            result = json.loads(json_str)
            result["dashboard"]["data"] = fetch_dashboard_data(result["dashboard"])
            return result
        else:
            print("No JSON found in response")
            # Fallback with dynamic columns
            x_col = columns[0]  # First column as x
            y_col = columns[1] if len(columns) > 1 else columns[0]  # Second or first as y
            return {
                "sql": f"SELECT {x_col}, SUM({y_col}) as total_{y_col} FROM business_data GROUP BY {x_col}",
                "dashboard": {
                    "type": "bar",
                    "x": x_col,
                    "y": y_col,
                    "title": f"{y_col.capitalize()} by {x_col.capitalize()}",
                    "data": fetch_dashboard_data({"x": x_col, "y": y_col, "title": f"{y_col.capitalize()} by {x_col.capitalize()}"})
                }
            }
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}")
        x_col = columns[0]
        y_col = columns[1] if len(columns) > 1 else columns[0]
        return {
            "sql": f"SELECT {x_col}, SUM({y_col}) as total_{y_col} FROM business_data GROUP BY {x_col}",
            "dashboard": {
                "type": "bar",
                "x": x_col,
                "y": y_col,
                "title": f"{y_col.capitalize()} by {x_col.capitalize()}",
                "data": fetch_dashboard_data({"x": x_col, "y": y_col, "title": f"{y_col.capitalize()} by {x_col.capitalize()}"})
            }
        }
    except Exception as e:
        print(f"Gemini error: {str(e)}")
        raise

@app.post("/query")
async def process_query(query: Query):
    try:
        result = interpret_query(query.text)
        sql_query = result["sql"]
        print(f"Generated SQL: {sql_query}")
        if "DROP" in sql_query.upper() or "DELETE" in sql_query.upper():
            raise HTTPException(status_code=400, detail="Unsafe SQL query detected")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            results = [dict(row) for row in cursor.fetchall()]
        
        return {"answer": results, "dashboard": result["dashboard"]}
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Backend is running"}