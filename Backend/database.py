import sqlite3
from sqlite3 import Error
from datetime import datetime
import os
import logging
import json
from sqlite3 import OperationalError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = "business_data.db"
SCHEMA_VERSION = 2

def create_connection():
    try:
        conn = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        migrate_database(conn)
        return conn
    except Error as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def migrate_database(conn):
    try:
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor = conn.execute("SELECT MAX(version) as current FROM schema_version")
            current_version = cursor.fetchone()['current'] or 0
            logger.info(f"Current schema version: {current_version}")

            if current_version < 1:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS uploads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        filepath TEXT NOT NULL UNIQUE,
                        uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        file_size INTEGER,
                        status TEXT DEFAULT 'active' CHECK (status IN ('active', 'deleted'))
                    )
                ''')
                conn.execute("INSERT INTO schema_version (version) VALUES (1)")
                logger.info("Applied schema migration to version 1")

            column_check = conn.execute("PRAGMA table_info(uploads)").fetchall()
            column_names = [col[1] for col in column_check]
            if "file_size" not in column_names:
                logger.warning("Column 'file_size' is missing in 'uploads'. Adding it now...")
                conn.execute("ALTER TABLE uploads ADD COLUMN file_size INTEGER")

            if current_version < 2:
                try:
                    conn.execute("ALTER TABLE uploads ADD COLUMN file_hash TEXT")
                except OperationalError as e:
                    if "duplicate column name" not in str(e):
                        raise
                try:
                    conn.execute("ALTER TABLE uploads ADD COLUMN metadata TEXT")
                except OperationalError as e:
                    if "duplicate column name" not in str(e):
                        raise
                conn.execute("INSERT INTO schema_version (version) VALUES (2)")
                logger.info("Applied schema migration to version 2")

            logger.info(f"Database schema is up-to-date at version {SCHEMA_VERSION}")

    except Error as e:
        logger.error(f"Error migrating database: {e}")
        raise

def insert_upload(conn, filename, filepath, file_hash=None, metadata=None):
    try:
        cursor = conn.execute("SELECT id FROM uploads WHERE filepath = ?", (filepath,))
        existing = cursor.fetchone()

        if existing:
            logger.warning(f"File '{filename}' already exists with ID {existing['id']}.")
            return existing['id']

        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else None
        metadata_json = json.dumps(metadata) if metadata else None
        cursor = conn.execute(
            "INSERT INTO uploads (filename, filepath, file_size, file_hash, metadata) VALUES (?, ?, ?, ?, ?)",
            (filename, filepath, file_size, file_hash, metadata_json)
        )
        conn.commit()
        logger.info(f"Inserted file '{filename}' with ID {cursor.lastrowid}")
        return cursor.lastrowid
    except Error as e:
        logger.error(f"Error inserting file: {e}")
        conn.rollback()
        return None

if __name__ == "__main__":
    with create_connection() as conn:
        if conn:
            logger.info("Database initialized successfully.")