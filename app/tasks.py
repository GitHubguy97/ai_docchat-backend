from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.models import Document, Chunk
from app.utils.chunking import chunk_text

@celery_app.task
def process_document(document_id: int, text: str):
    """
    Background task to process a document
    """
    print(f"Starting to process document {document_id}")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get the document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            print(f"Document {document_id} not found")
            return
        
        # Update status to processing
        document.status = "processing"
        db.commit()
        
        # Simulate some work
        print("chunking document.....")
        chunks = chunk_text(text)
        print(f" created {len(chunks)} chunks")

        for chunk_data in chunks:
            chunk = Chunk(
                document_id=document_id,
                ord = chunk_data['id'],
                text=chunk_data['text'],
                page_start=1,
                page_end=1,
                token_count=chunk_data['token_count']
            )
            db.add(chunk)

        
        # Update status to ready
        
        db.commit()
        print ("Chunks added to database")
        
        document.status = "ready"
        db.commit()
        
        print(f"Document {document_id} processed successfully")
        
    except Exception as e:
        print(f"Error processing document {document_id}: {e}")
        document.status = "failed"
        db.commit()
    finally:
        db.close()