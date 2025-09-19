from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.models.models import Document
from app.dependencies import get_db
import PyPDF2
import io
import hashlib


router = APIRouter()

@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...), db: Session = Depends(get_db)):

  if file.content_type != "application/pdf":
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a PDF")

  content = await file.read()
  MAX_FILE_SIZE = 10 * 1024 * 1024 # 10MB

  if len(content) > MAX_FILE_SIZE:
    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File size exceeds the maximum allowed size of 10MB")

  content_hash = hashlib.sha256(content).hexdigest()

  existing_document = db.query(Document).filter(Document.content_hash == content_hash).first()

  if existing_document:
    return {
      "document_id": existing_document.id,
      "status": "already_ingested",
      "content_hash": content_hash
    }

  try:
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
    text = ""
    for page in pdf_reader.pages:
      text += page.extract_text()
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"Failed to read PDF file: {str(e)}")

  document = Document(
    content_hash=content_hash,
    title=file.filename or "Untitled Document",
    pages=len(pdf_reader.pages),
    bytes=len(content),
    status="queued"
  )

  db.add(document)
  db.commit()
  db.refresh(document)

  return {
    "document_id": document.id,
    "status": document.status,
    "pages": document.pages,
    "text_length": len(text),
    "content_hash": document.content_hash,
    "file_size": document.bytes
  }