import sqlite3
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "documents.db"


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def create_document(
    document_id: str,
    filename: str,
    stored_filename: str,
    content_type: str,
    size_bytes: int,
):
    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (
                document_id,
                filename,
                stored_filename,
                content_type,
                size_bytes,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                filename,
                stored_filename,
                content_type,
                size_bytes,
                "uploaded",
                created_at,
            ),
        )

    return created_at


def list_documents():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                document_id,
                filename,
                content_type,
                size_bytes,
                status,
                created_at
            FROM documents
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


init_db()
