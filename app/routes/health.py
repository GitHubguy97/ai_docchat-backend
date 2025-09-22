from fastapi import APIRouter


router = APIRouter()

@router.get("/health")
def healthz():
  return {"status": "healthy"}

