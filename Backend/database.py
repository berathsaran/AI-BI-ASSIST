import sqlite3
from sqlite3 import Error
from datetime import datetime
import os
import logging
import json
from sqlite3 import OperationalError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

DB_NAME = "business_data.db"
SCHEMA_VERSION = 2

def create_connection():
    """Create a database connection and initialize/migrate the schema."""
    try:
        conn = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        migrate_database(conn)
        return conn
    except Error as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def migrate_database(conn):
    """Initialize and migrate the database schema incrementally."""
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

            if current_version >= SCHEMA_VERSION:
                logger.info(f"Database schema is up-to-date at version {SCHEMA_VERSION}")
            else:
                logger.info(f"Database schema migrated to version {SCHEMA_VERSION}")

    except Error as e:
        logger.error(f"Error migrating database: {e}")
        raise

def insert_upload(conn, filename, filepath, file_hash=None, metadata=None):
    """Insert a new upload with optional hash and metadata."""
    try:
        with conn:
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

def get_upload_by_id(conn, file_id):
    """Retrieve file details by ID, only active records."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM uploads WHERE id = ? AND status = 'active'", (file_id,))
        result = cursor.fetchone()
        if result:
            return dict(result)
        logger.warning(f"No active file found with ID {file_id}")
        return None
    except Error as e:
        logger.error(f"Error retrieving file: {e}")
        return None

def delete_upload(conn, file_id, hard_delete=False):
    """Soft-delete or hard-delete an upload."""
    try:
        with conn:
            if hard_delete:
                cursor = conn.execute("DELETE FROM uploads WHERE id = ?", (file_id,))
                action = "Hard-deleted"
            else:
                cursor = conn.execute(
                    "UPDATE uploads SET status = 'deleted' WHERE id = ? AND status = 'active'",
                    (file_id,)
                )
                action = "Soft-deleted"

            if cursor.rowcount > 0:
                logger.info(f"{action} file with ID {file_id}")
                return True
            logger.warning(f"No active file found with ID {file_id} to delete")
            return False
    except Error as e:
        logger.error(f"Error deleting file: {e}")
        conn.rollback()
        return False

def list_uploads(conn, limit=100, offset=0, status='active'):
    """List uploads with pagination and status filter."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM uploads WHERE status = ? ORDER BY uploaded_at DESC LIMIT ? OFFSET ?",
            (status, limit, offset)
        )
        results = [dict(row) for row in cursor.fetchall()]
        logger.info(f"Retrieved {len(results)} {status} uploads")
        return results
    except Error as e:
        logger.error(f"Error listing uploads: {e}")
        return []

def get_database_stats(conn):
    """Retrieve database statistics."""
    try:
        cursor = conn.cursor()
        stats = {}
        cursor.execute("SELECT COUNT(*) as total FROM uploads WHERE status = 'active'")
        stats['total_active_uploads'] = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM uploads WHERE status = 'deleted'")
        stats['total_deleted_uploads'] = cursor.fetchone()['total']
        cursor.execute("SELECT SUM(file_size) as total_size FROM uploads WHERE status = 'active'")
        stats['total_size_bytes'] = cursor.fetchone()['total_size'] or 0
        logger.info(f"Retrieved database stats: {stats}")
        return stats
    except Error as e:
        logger.error(f"Error retrieving stats: {e}")
        return {}

if __name__ == "__main__":
    conn = create_connection()
    if conn:
        logger.info("Database initialized successfully.")
        conn.close()