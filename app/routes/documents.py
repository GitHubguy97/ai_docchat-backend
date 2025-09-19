from fastapi import APIRouter

router = APIRouter()

@router.get("/documents/{document_id}")
def get_document(document_id: str):
  return {
    "id": document_id,
    "title": "Sample Document",
    "pages": 10,
    "bytes": 50000,
    "status": "ready"
  }