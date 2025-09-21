from fastapi import APIRouter, HTTPException,status, Depends
from fastapi.requests import Request
from app.utils.rate_limiting import check_rate_limit
from app.utils.format_time import format_reset_time

router = APIRouter()

def get_client_ip(request: Request):
  print(request.client.host)
  return request.client.host

@router.post("/ask")
def ask_question(ip_address: str = Depends(get_client_ip)):

  rate_limit_result = check_rate_limit(ip_address)

  if not rate_limit_result["allowed"]:
    raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Rate limit exceeded. Please try again in {format_reset_time( rate_limit_result['reset_time'] )} seconds.")

  return {
    "answer": "This is a sample answer",
    "cached": False,
    "citation": [
      {"page": 1, "quote": "This is a sample content", "chunk_id": "1"}
    ]
  }