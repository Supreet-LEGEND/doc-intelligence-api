from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, File, HTTPException, UploadFile
from app.database import create_document, list_documents
from app.schemas.documents import DocumentResponse, DocumentListResponse

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
