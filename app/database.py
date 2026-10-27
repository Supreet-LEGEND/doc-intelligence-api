import sqlite3
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "documents.db"

def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def init_db():
    """Initialize the database and create tables if they don't exist."""

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

    
    connection.execute("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,

            FOREIGN KEY (document_id)
                REFERENCES documents(document_id),

            UNIQUE (document_id, chunk_index)
        )
    """)



def create_document(
    document_id: str,
    filename: str,
    stored_filename: str,
    content_type: str,
    size_bytes: int,
):
    """Create a new document record."""

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
    """Retrieve all document records, ordered by creation time (newest first)."""
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



def get_document(document_id: str):
    """Retrieve a document record by its ID."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM documents
            WHERE document_id = ?
            """,
            (document_id,),
        ).fetchone()

    return dict(row) if row else None



def save_chunks(document_id: str, chunks: list[str]) -> None:
    """Replace the stored chunks for one document."""

    with get_connection() as connection:
        # Remove any previous chunks for this document.
        connection.execute(
            """
            DELETE FROM document_chunks
            WHERE document_id = ?
            """,
            (document_id,),
        )

        # Insert the new chunks in their original order.
        connection.executemany(
            """
            INSERT INTO document_chunks (
                document_id,
                chunk_index,
                chunk_text
            )
            VALUES (?, ?, ?)
            """,
            [
                (document_id, index, chunk)
                for index, chunk in enumerate(chunks)
            ],
        )


def get_chunks(document_id: str) -> list[dict]:
    """Retrieve a document's chunks in their original order."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                chunk_id,
                document_id,
                chunk_index,
                chunk_text
            FROM document_chunks
            WHERE document_id = ?
            ORDER BY chunk_index
            """,
            (document_id,),
        ).fetchall()

    return [dict(row) for row in rows]



init_db()
