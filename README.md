# AI Document Intelligence & Semantic Search API

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)
![LangChain](https://img.shields.io/badge/LangChain-Integration-1C3C3C)
![FAISS](https://img.shields.io/badge/Vector_Store-FAISS-0467DF)
![SQLite](https://img.shields.io/badge/Database-SQLite_WAL-003B57)
![Tests](https://img.shields.io/badge/Tests-Pytest-brightgreen)

A modular FastAPI backend for multi-format document ingestion, recursive semantic chunking, dense vector embeddings, and low-latency similarity search using **LangChain**, **Hugging Face Sentence Transformers**, **FAISS**, and **SQLite**.

Built with a hybrid engineering approach: pairing foundational implementations (custom text normalization, custom cosine similarity verification, and concurrency-hardened SQLite in WAL mode) with production AI orchestration components (`RecursiveCharacterTextSplitter`, `HuggingFaceEmbeddings`, and `FAISS`).

---

## System Architecture

```text
[ Upload Document (.pdf / .docx / .txt) ]
                    │
                    ▼
      app/services/text_extraction.py
   (PyMuPDF, python-docx, UTF-8 parser)
                    │
                    ▼
      app/services/text_processing.py
 (Regex cleaning + LangChain RecursiveCharacterTextSplitter)
                    │
                    ├─────────────────────────────────────────┐
                    ▼                                         ▼
     app/database.py (SQLite + WAL)            app/services/embeddings.py
  Stores document metadata & raw chunks     (sentence-transformers/all-MiniLM-L6-v2)
                    │                                         │
                    │                                         ▼
                    └──────────────────────────► app/services/retrieval.py
                                                 (FAISS Vector Indexing & Search)
                                                              │
                                                              ▼
                                                [ GET /api/v1/documents/search ]
                                                (Top-K Chunks + Cosine Similarity)
```

---

## Key Engineering Highlights

* **Multi-Format Document Ingestion:** Supports `.pdf` (via PyMuPDF), `.docx` (via `python-docx`), and `.txt` files with strict file validation and format-honest metadata tracking.
* **Boundary-Aware Text Splitting:** Cleans raw text artifacts and splits documents using LangChain's `RecursiveCharacterTextSplitter` (`chunk_size=1000`, `chunk_overlap=150`), prioritizing paragraph and sentence boundaries over arbitrary character cuts.
* **Concurrency-Hardened SQLite Storage:** Configured with **Write-Ahead Logging (`PRAGMA journal_mode = WAL`)**, foreign-key enforcement, and a 15-second busy timeout so concurrent API reads never block bulk chunk insertions.
* **Normalized Dense Embeddings:** Generates 384-dimensional unit-normalized vectors using `sentence-transformers/all-MiniLM-L6-v2`, cached in memory via `@lru_cache` with automatic CUDA/CPU device detection.
* **Idempotent FAISS Vector Indexing:** Maps FAISS $L_2^2$ distance on unit vectors directly to exact Cosine Similarity ($\text{CosineSim} = 1 - \frac{L_2^2}{2}$) and automatically deduplicates existing document vectors upon re-processing.
* **Automated Test Suite:** Unit and integration tests covering text splitting edge cases, embedding dimensions, semantic ranking vs. keyword matching, and isolated FAISS persistence using `pytest` `tmp_path` fixtures.

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **API Framework** | FastAPI, Uvicorn, Pydantic |
| **Orchestration & Splitting** | LangChain (`langchain-core`, `langchain-text-splitters`, `langchain-community`) |
| **Embedding Model** | Hugging Face `sentence-transformers/all-MiniLM-L6-v2` (`langchain-huggingface`) |
| **Vector Store** | FAISS (`faiss-cpu`) |
| **Database** | SQLite3 (WAL Mode enabled) |
| **Document Parsers** | PyMuPDF (`fitz`), `python-docx` |
| **Testing** | Pytest |

---

## Project Structure

```text
AI-Document-Intelligence-API/
├── app/
│   ├── main.py                    # FastAPI app entrypoint
│   ├── database.py                # SQLite WAL setup, schema init, and CRUD helpers
│   ├── routes/
│   │   └── documents.py           # /upload, /{id}/process, and /search endpoints
│   ├── schemas/
│   │   └── documents.py           # Pydantic request/response schemas
│   └── services/
│       ├── text_extraction.py     # PDF, DOCX, and TXT text extraction
│       ├── text_processing.py     # Custom text cleaning & LangChain chunking
│       ├── embeddings.py          # Cached HuggingFace embeddings & cosine similarity
│       └── retrieval.py           # FAISS index persistence, deduplication, and search
├── data/
│   ├── uploads/                   # Local storage for uploaded documents
│   └── indexes/                   # Persisted FAISS index files (index.faiss, index.pkl)
├── tests/
│   ├── test_chunking.py           # Unit tests for cleaning and text splitting
│   ├── test_embeddings.py         # Unit tests for vector dimensions and semantic ranking
│   └── test_retrieval.py          # Integration tests for FAISS indexing and search
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Quickstart & Installation

### 1. Clone the Repository
```bash
git clone [https://github.com/](https://github.com/)<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### 2. Create and Activate a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (Git Bash):**
```bash
python -m venv .venv
source .venv/Scripts/activate
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
python -m pip install -U pip
pip install fastapi uvicorn[standard] pymupdf python-docx langchain-core langchain-text-splitters langchain-community langchain-huggingface sentence-transformers faiss-cpu pytest
```
*(Or run `pip install -r requirements.txt` if `requirements.txt` is present)*.

### 4. Start the API Server
```bash
uvicorn app.main:app --reload
```
* **Swagger UI (Interactive Docs):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## API Endpoints

### 1. Upload a Document
`POST /api/v1/documents/upload`

Uploads a `.pdf`, `.docx`, or `.txt` file, validates the extension, stores the file in `data/uploads/`, and records metadata in SQLite.

### 2. Process & Index a Document
`POST /api/v1/documents/{document_id}/process`

Extracts text, normalizes formatting, splits text into overlapping chunks, saves chunks to the `document_chunks` table, generates 384-d embeddings, and updates the local FAISS index.

**Sample Response:**
```json
{
  "document_id": "7bdfa8b1-2ce4-4bf8-b2ef-343513a89012",
  "status": "processed_and_indexed",
  "character_count": 4820,
  "chunk_count": 6,
  "indexed_vectors": 6,
  "chunk_preview": [
    "Employees receive 24 days of paid annual leave per calendar year...",
    "All customers are eligible for a full refund within 30 days of purchase..."
  ]
}
```

### 3. Semantic Search
`GET /api/v1/documents/search`

Embeds a natural language query and retrieves the top-$k$ most semantically similar chunks from FAISS.

**Query Parameters:**
* `query` *(string, required)*: Natural language search query (minimum 2 characters).
* `top_k` *(int, optional, default=5)*: Number of results to return (`1` to `20`).
* `document_id` *(string, optional)*: Filter search results to a single document.

**Sample Response:**
```json
{
  "query": "How do I get my money back?",
  "top_k": 2,
  "document_id_filter": null,
  "result_count": 1,
  "results": [
    {
      "document_id": "7bdfa8b1-2ce4-4bf8-b2ef-343513a89012",
      "filename": "company_policy.pdf",
      "chunk_id": 2,
      "chunk_index": 1,
      "similarity_score": 0.6842,
      "chunk_text": "All customers are eligible for a full refund within 30 days of purchase."
    }
  ]
}
```

---

## Running Automated Tests

Execute the entire test suite from the project root:

```bash
python -m pytest -v
```

Run individual test modules:
```bash
python -m pytest tests/test_chunking.py -v
python -m pytest tests/test_embeddings.py -v -s
python -m pytest tests/test_retrieval.py -v
```

---

## Project Roadmap

- [x] **Phase 1:** Document upload, multi-format extraction (`.pdf`, `.docx`, `.txt`), cleaning, and LangChain recursive chunking.
- [x] **Phase 2:** Sentence-Transformers embedding service and custom cosine similarity verification.
- [x] **Phase 3:** Persistent FAISS vector indexing, deduplication, and `/search` endpoint.
- [ ] **Phase 4:** Retrieval-Augmented Generation (`POST /api/v1/documents/ask`) connecting retrieved context to an LLM with grounded source citations.
- [ ] **Phase 5:** Evaluation harness comparing retrieval recall, latency, and citation accuracy.

---

## License

This project is licensed under the MIT License.
