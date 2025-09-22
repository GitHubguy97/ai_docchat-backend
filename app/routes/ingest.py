from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.models.models import Document
from app.dependencies import get_db
from app.redis_client import redis_client
from app.tasks import process_document
from app.utils.logger import api_logger
import PyPDF2
import io
import hashlib


router = APIRouter()

@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
  api_logger.info(f"Document upload started", 
                 filename=file.filename, 
                 content_type=file.content_type, 
                 size=file.size)

  if file.content_type != "application/pdf":
    api_logger.warning(f"Invalid file type", filename=file.filename, content_type=file.content_type)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a PDF")

  content = await file.read()
  MAX_FILE_SIZE = 10 * 1024 * 1024 # 10MB

  if len(content) > MAX_FILE_SIZE:
    api_logger.warning(f"File too large", filename=file.filename, size=len(content), max_size=MAX_FILE_SIZE)
    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File size exceeds the maximum allowed size of 10MB")

  content_hash = hashlib.sha256(content).hexdigest()
  api_logger.info(f"File validated", filename=file.filename, content_hash=content_hash[:16])

  #Idempotency check
  #Check Redis cache fist
  cached_doc_id = redis_client.get(f"doc:hash:{content_hash}")


  if cached_doc_id:
    api_logger.info(f"Document found in cache", document_id=cached_doc_id, content_hash=content_hash[:16])
    doc = db.query(Document).filter(Document.id == cached_doc_id).first()
    return {
      "document_id": int(cached_doc_id),
      "status": doc.status,
      "message": "Document already ingested Cached"
    }

  #Check database second
  existing_document = db.query(Document).filter(Document.content_hash == content_hash).first()

  if existing_document:
    api_logger.info(f"Document found in database", document_id=existing_document.id, content_hash=content_hash[:16])
    return {
      "document_id": existing_document.id,
      "status": "already_ingested db",
      "content_hash": content_hash
    }

  #If not in cache or db, process new the PDF file
  try:
    api_logger.info(f"Processing new PDF", filename=file.filename, content_hash=content_hash[:16])
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
    
    # Create concatenated text with inline page markers
    full_text = ""
    for page_num, page in enumerate(pdf_reader.pages):
      page_text = page.extract_text()
      if page_text.strip():  # Only add non-empty pages
        full_text += f"[PAGE:{page_num + 1}] {page_text}\n\n"
    
    api_logger.info(f"PDF text extracted", 
                   filename=file.filename, 
                   pages=len(pdf_reader.pages), 
                   text_length=len(full_text))
    
  except Exception as e:
    api_logger.exception(f"Failed to read PDF", filename=file.filename, error=str(e))
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

  api_logger.info(f"Document created in database", 
                 document_id=document.id, 
                 title=document.title, 
                 pages=document.pages)

  #Cache the document ID in Redis
  redis_client.setex(f"doc:hash:{content_hash}", 30*24*3600, str(document.id)) #Cache for 1 hour

  #Queue the document for processing
  process_document.delay(document.id, full_text)
  
  api_logger.info(f"Document queued for processing", document_id=document.id)

  return {
    "document_id": document.id,
    "status": document.status,
    "pages": document.pages,
    "text_length": len(full_text),
    "content_hash": document.content_hash,
    "file_size": document.bytes
  }