import sqlite3

def init_db():
    conn = sqlite3.connect("business_data.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS business_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT,
            sales INTEGER,
            revenue REAL,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")