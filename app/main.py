from fastapi import FastAPI
from app.api import documents, search
from app.config import settings

app = FastAPI(
    title="AI Document Intelligence & Semantic Search API",
    description="API for document ingestion, semantic search, and question answering",
    version="1.0.0"
)

app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])

@app.get("/")
async def root():
    return {"message": "AI Document Intelligence & Semantic Search API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}