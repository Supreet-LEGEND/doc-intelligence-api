import sqlite3

from app.database import save_chunks, get_chunks


def test_save_and_get_chunks(tmp_path, monkeypatch):
    from app import database

    # Use a temporary database, not your real project database.
    test_db = tmp_path / "test_documents.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)

    with sqlite3.connect(test_db) as connection:
        connection.execute("""
            CREATE TABLE documents (
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
            CREATE TABLE document_chunks (
                chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                FOREIGN KEY (document_id)
                    REFERENCES documents(document_id),
                UNIQUE (document_id, chunk_index)
            )
        """)
        connection.execute(
            """
            INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "doc-1", "sample.txt", "doc-1.txt",
                "text/plain", 100, "uploaded",
                "2026-01-01T00:00:00+00:00",
            ),
        )

    save_chunks("doc-1", ["First chunk", "Second chunk"])

    chunks = get_chunks("doc-1")

    assert len(chunks) == 2
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["chunk_text"] == "First chunk"
    assert chunks[1]["chunk_index"] == 1
    assert chunks[1]["chunk_text"] == "Second chunk"

    # Saving again should replace, not duplicate, the chunks.
    save_chunks("doc-1", ["Updated chunk"])

    chunks = get_chunks("doc-1")

    assert len(chunks) == 1
    assert chunks[0]["chunk_text"] == "Updated chunk"
