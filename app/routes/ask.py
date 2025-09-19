from fastapi import APIRouter

router = APIRouter()

@router.post("/ask")
def ask_question():
  return {
    "answer": "This is a sample answer",
    "cached": False,
    "citation": [
      {"page": 1, "quote": "This is a sample content", "chunk_id": "1"}
    ]
  }