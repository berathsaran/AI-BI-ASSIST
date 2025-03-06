import sqlite3
from sqlite3 import Error

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect("business_data.db")
        # Create the uploads table if it doesn't exist
        create_table(conn)
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL
            )
        ''')
        conn.commit()
    except Error as e:
        print(f"Error creating table: {e}")

def insert_upload(conn, filename, filepath):
    sql = '''INSERT INTO uploads (filename, filepath) VALUES (?, ?)'''
    cursor = conn.cursor()
    cursor.execute(sql, (filename, filepath))
    conn.commit()
    return cursor.lastrowid

if __name__ == "__main__":
    conn = create_connection()
    if conn:
        conn.close()