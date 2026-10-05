from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    chunks_created: int
    message: str


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    upload_time: datetime
    chunk_count: int
    file_size: int


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    similarity_threshold: Optional[float] = 0.7


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int


class QuestionRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5


class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: List[SearchResult]
    confidence: float


class ErrorResponse(BaseModel):
    detail: str