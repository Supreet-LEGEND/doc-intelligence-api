from fastapi import FastAPI
from app.routes.documents import router as documents_router

app = FastAPI(
    title="AI Document Intelligence & Semantic Search API",
    description="API for document ingestion, semantic search, and question answering",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "AI Document Intelligence & Semantic Search API"}

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy",
            "version": "1.0",}

app.include_router(
    documents_router, 
    prefix="/api/v1/documents",
    tags=["Documents"]
    )