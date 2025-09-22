from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.requests import Request
from pydantic import BaseModel
from typing import Optional, List
from app.utils.rate_limiting import check_rate_limit
from app.utils.format_time import format_reset_time
from app.utils.enhanced_search import enhanced_search
from app.utils.answer_generation import generate_answer_with_citations, Citation

router = APIRouter()

class AskRequest(BaseModel):
    question: str
    document_id: int

class AskResponse(BaseModel):
    question: str
    answer: str
    citations: List[Citation]
    total_chunks_found: int
    status: str

def get_client_ip(request: Request):
    print(request.client.host)
    return request.client.host

@router.post("/ask")
def ask_question(request: AskRequest, ip_address: str = Depends(get_client_ip)):
    
    rate_limit_result = check_rate_limit(ip_address)

    if not rate_limit_result["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
            detail=f"Rate limit exceeded. Please try again in {format_reset_time(rate_limit_result['reset_time'])} seconds."
        )

    try:
        # Check cache first before doing any expensive operations
        from app.utils.answer_generation import get_cached_answer, Citation
        
        cached_result = get_cached_answer(request.question)
        if cached_result:
            print(f"Returning cached answer for question: {request.question[:50]}...")
            citations = [Citation(**citation_dict) for citation_dict in cached_result["citations"]]
            return AskResponse(
                question=request.question,
                answer=cached_result["answer"],
                citations=citations,
                total_chunks_found=len(citations),
                status="success"
            )
        
        # Cache miss - proceed with enhanced search and LLM generation
        print(f"Cache miss - processing question with enhanced search: {request.question}")
        similar_chunks = enhanced_search(
            question=request.question,
            document_id=request.document_id
        )
        print(f"Enhanced search found {len(similar_chunks)} similar chunks")
        
        # Generate answer with citations
        answer, citations = generate_answer_with_citations(request.question, similar_chunks, request.document_id)
        
        return AskResponse(
            question=request.question,
            answer=answer,
            citations=citations,
            total_chunks_found=len(similar_chunks),
            status="success"
        )
        
    except Exception as e:
        print(f"Error in ask endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )