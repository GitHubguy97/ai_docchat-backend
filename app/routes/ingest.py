from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.models.models import Document
from app.dependencies import get_db
from app.redis_client import redis_client
from app.tasks import process_document
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

  #Idempotency check
  #Check Redis cache fist
  cached_doc_id = redis_client.get(f"doc:hash:{content_hash}")

  print(cached_doc_id)

  if cached_doc_id:
    doc = db.query(Document).filter(Document.id == cached_doc_id).first()
    return {
      "document_id": int(cached_doc_id),
      "status": doc.status,
      "message": "Document already ingested Cached"
    }

  #Check database second
  existing_document = db.query(Document).filter(Document.content_hash == content_hash).first()

  if existing_document:
    return {
      "document_id": existing_document.id,
      "status": "already_ingested db",
      "content_hash": content_hash
    }

  #If not in cache or db, process new the PDF file
  try:
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
    text = ""
    for page in pdf_reader.pages:
      text += page.extract_text()
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"Failed to read PDF file: {str(e)}")

  #Create new document record for database
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

  #Cache the document ID in Redis
  redis_client.setex(f"doc:hash:{content_hash}", 30*24*3600, str(document.id)) #Cache for 1 hour

  #Queue the document for processing
  process_document.delay(document.id, text)

  return {
    "document_id": document.id,
    "status": document.status,
    "pages": document.pages,
    "text_length": len(text),
    "content_hash": document.content_hash,
    "file_size": document.bytes
  }