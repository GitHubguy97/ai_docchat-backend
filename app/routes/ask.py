from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.requests import Request
from pydantic import BaseModel
from typing import Optional
from app.utils.rate_limiting import check_rate_limit
from app.utils.format_time import format_reset_time
from app.utils.enhanced_search import enhanced_search

router = APIRouter()

class AskRequest(BaseModel):
    question: str
    document_id: int

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
        # Use enhanced search with structured question decomposition
        print(f"Processing question with enhanced search: {request.question}")
        similar_chunks = enhanced_search(
            question=request.question,
            document_id=request.document_id
        )
        print(f"Enhanced search found {len(similar_chunks)} similar chunks")
        
        # Return the similarity results for testing
        return {
            "question": request.question,
            "document_id": request.document_id,
            "similar_chunks": similar_chunks,
            "total_chunks_found": len(similar_chunks),
            "status": "success"
        }
        
    except Exception as e:
        print(f"Error in ask endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )