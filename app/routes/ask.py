from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.requests import Request
from pydantic import BaseModel
from typing import Optional
from app.utils.rate_limiting import check_rate_limit
from app.utils.format_time import format_reset_time
from app.utils.embeddings import generate_single_embedding
from app.utils.vector_search import search_similar_chunks

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
        # Generate query embedding
        print(f"Generating embedding for question: {request.question}")
        query_embedding = generate_single_embedding(request.question)
        print(f"Generated embedding with {len(query_embedding)} dimensions")
        
        # Search for similar chunks
        print(f"Searching for similar chunks in document {request.document_id}")
        similar_chunks = search_similar_chunks(
            query_embedding=query_embedding,
            top_k=6,
            document_id=request.document_id
        )
        print(f"Found {len(similar_chunks)} similar chunks")
        
        # Return the similarity results for testing
        return {
            "question": request.question,
            "document_id": request.document_id,
            "similar_chunks": similar_chunks,
            "total_chunks_found": len(similar_chunks),
            "embedding_dimensions": len(query_embedding),
            "status": "success"
        }
        
    except Exception as e:
        print(f"Error in ask endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )