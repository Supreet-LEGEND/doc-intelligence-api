from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import List
import os
import uuid
from datetime import datetime

from app.models.schemas import DocumentUploadResponse, DocumentMetadata, ErrorResponse
from app.services.pdf_service import extract_text_from_pdf
from app.services.chunking import chunk_text
from app.services.embedding import generate_embeddings
from app.services.vector_store import add_to_index, save_index
from app.config import settings


router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    document_id = str(uuid.uuid4())
    file_path = os.path.join(settings.upload_dir, f"{document_id}.pdf")
    
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        text = extract_text_from_pdf(file_path)
        
        if not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract text from PDF"
            )
        
        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        
        embeddings = generate_embeddings(chunks)
        
        chunk_ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        metadata = [
            {
                "document_id": document_id,
                "filename": file.filename,
                "chunk_index": i,
                "chunk_id": chunk_ids[i]
            }
            for i in range(len(chunks))
        ]
        
        add_to_index(embeddings, chunk_ids, metadata)
        save_index()
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            status="success",
            chunks_created=len(chunks),
            message=f"Document processed successfully. Created {len(chunks)} chunks."
        )
    
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@router.get("/list", response_model=List[DocumentMetadata])
async def list_documents():
    return []


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str):
    return