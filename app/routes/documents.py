from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, File, HTTPException, UploadFile
from app.database import create_document, list_documents, get_document, save_chunks
from app.schemas.documents import DocumentResponse, DocumentListResponse, DocumentTextResponse
from app.services.text_extraction import extract_text
from app.services.text_processing import clean_text, chunk_text

router = APIRouter()

# Project root: ai-document-intelligence/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Directory for uploaded files
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"

# Maximum allowed upload size: 25 MiB
MAX_FILE_SIZE = 25 * 1024 * 1024

# Extension-to-content-type mapping
ALLOWED_TYPES = {
    ".pdf": {"application/pdf"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    },
    ".txt": {"text/plain"},
}


@router.get("/",response_model=DocumentListResponse)
def get_documents():
    return {"documents": list_documents()}


@router.post("/", status_code=201,response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    # 1. Check that a filename was provided
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A filename is required.",
        )

    # 2. Extract the extension and normalize its case
    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Upload PDF, DOCX, or TXT.",
        )

    # 3. Check the declared content type
    if file.content_type not in ALLOWED_TYPES[extension]:
        raise HTTPException(
            status_code=415,
            detail="The file content type does not match the extension.",
        )

    # 4. Create the upload directory if necessary
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # 5. Create a unique ID and a server-controlled filename
    document_id = str(uuid4())
    saved_path = UPLOAD_DIR / f"{document_id}{extension}"

    size = 0

    try:
        # 6. Copy the upload in chunks, enforcing the size limit
        with saved_path.open("wb") as destination:
            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                size += len(chunk)

                if size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds the {MAX_FILE_SIZE // (1024 * 1024)} MiB upload limit.",
                    )

                destination.write(chunk)

    except Exception:
        # Remove incomplete files if saving fails
        saved_path.unlink(missing_ok=True)
        raise

    finally:
        await file.close()

    # Store the document metadata in the database
    
    created_at = create_document(
    document_id=document_id,
    filename=Path(file.filename).name,
    stored_filename=saved_path.name,
    content_type=file.content_type,
    size_bytes=size,
)

    # 7. Return information about the uploaded file
    return {
        "document_id": document_id,
        "filename": Path(file.filename).name,
        "content_type": file.content_type,
        "size_bytes": size,
        "status": "uploaded",
        "created_at": created_at,
    }



@router.post(
    "/{document_id}/extract",
    response_model=DocumentTextResponse,
)
def extract_document(document_id: str):
    record = get_document(document_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    stored_path = UPLOAD_DIR / record["stored_filename"]

    print("Document ID:", document_id)
    print("Stored filename:", record["stored_filename"])
    print("Upload directory:", UPLOAD_DIR.resolve())
    print("Full file path:", stored_path.resolve())
    print("File exists:", stored_path.is_file())

    print(f"Extracting text from {stored_path}...")

    try:
        result = extract_text(stored_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Stored document file not found.",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="Could not read this document.",
        )

    text = result["text"]

    return {
        "document_id": record["document_id"],
        "filename": record["filename"],
        "page_count": result["page_count"],
        "character_count": len(text),
        "text": text,
    }



@router.post("/{document_id}/process")
def process_document(document_id: str):
    # 1. Find the uploaded document in SQLite.
    record = get_document(document_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    # 2. Locate the actual stored file.
    stored_path = UPLOAD_DIR / record["stored_filename"]

    # 3. Extract its text.
    try:
        extracted = extract_text(stored_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Stored document file not found.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from this document.",
        ) from exc

    # 4. Clean the extracted text.
    cleaned_text = clean_text(extracted["text"])

    if not cleaned_text:
        raise HTTPException(
            status_code=422,
            detail="No extractable text was found in this document.",
        )

    # 5. Split the text using LangChain.
    chunks = chunk_text(
        cleaned_text,
        chunk_size=1000,
        overlap=150,
    )

    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="No text chunks could be created.",
        )

    # 6. Save the chunks in SQLite.
    save_chunks(document_id, chunks)

    # 7. Return processing details for testing.
    return {
        "document_id": document_id,
        "filename": record["filename"],
        "page_count": extracted["page_count"],
        "character_count": len(cleaned_text),
        "chunk_count": len(chunks),
        "chunk_preview": chunks[:3],  # Return only the first 3 chunks for preview
        "status": "processed",
    }
