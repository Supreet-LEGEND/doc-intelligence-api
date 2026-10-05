from fastapi import APIRouter, HTTPException, status
from typing import List

from app.models.schemas import SearchRequest, SearchResponse, QuestionRequest, QuestionResponse, SearchResult
from app.services.embedding import generate_embeddings
from app.services.vector_store import search_index
from app.services.retrieval import generate_answer
from app.config import settings


router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    try:
        query_embedding = generate_embeddings([request.query])[0]
        
        results = search_index(
            query_embedding,
            top_k=request.top_k or settings.top_k,
            similarity_threshold=request.similarity_threshold or settings.similarity_threshold
        )
        
        search_results = [
            SearchResult(
                chunk_id=r["chunk_id"],
                document_id=r["metadata"]["document_id"],
                content=r["content"],
                score=r["score"],
                metadata=r["metadata"]
            )
            for r in results
        ]
        
        return SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search error: {str(e)}"
        )


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    try:
        query_embedding = generate_embeddings([request.question])[0]
        
        results = search_index(
            query_embedding,
            top_k=request.top_k or settings.top_k,
            similarity_threshold=settings.similarity_threshold
        )
        
        if not results:
            return QuestionResponse(
                question=request.question,
                answer="I couldn't find any relevant information to answer your question.",
                sources=[],
                confidence=0.0
            )
        
        answer, confidence = generate_answer(request.question, results)
        
        sources = [
            SearchResult(
                chunk_id=r["chunk_id"],
                document_id=r["metadata"]["document_id"],
                content=r["content"][:500] + "..." if len(r["content"]) > 500 else r["content"],
                score=r["score"],
                metadata=r["metadata"]
            )
            for r in results
        ]
        
        return QuestionResponse(
            question=request.question,
            answer=answer,
            sources=sources,
            confidence=confidence
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating answer: {str(e)}"
        )