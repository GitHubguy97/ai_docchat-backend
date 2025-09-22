from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.models import Document, Chunk, Embedding
from app.utils.chunking import smart_chunk_document
from app.utils.embeddings import generate_embeddings
from app.redis_client import redis_client
from app.utils.logger import task_logger, qdrant_logger, openai_logger, db_logger
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from typing import List, Dict
import json

@celery_app.task
def process_document(document_id: int, full_text: str):
    """
    Background task to process a document
    """
    task_logger.info(f"Starting document processing", document_id=document_id, text_length=len(full_text))
    
    # Get database session
    db = SessionLocal()
    
    # Initialize Qdrant client
    qdrant_client = QdrantClient(host="127.0.0.1", port=6333)
    
    try:
        # Get the document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            task_logger.error(f"Document not found", document_id=document_id)
            return
        
        # Update status to processing
        document.status = "processing"
        db.commit()
        db_logger.info(f"Document status updated to processing", document_id=document_id)
        
        # Update job progress in Redis
        job_key = f"job:{document_id}"
        job_data = {
            "status": "processing",
            "progress": 20,
            "message": "Starting document processing..."
        }
        redis_client.setex(job_key, 3600, json.dumps(job_data))  # 1 hour TTL
        
        # Chunk with smart page-aware strategy
        task_logger.info(f"Starting document chunking", document_id=document_id)
        chunks = smart_chunk_document(full_text)
        task_logger.info(f"Document chunking completed", document_id=document_id, chunks_created=len(chunks))
        
        # Update progress - chunking complete
        job_data["progress"] = 40
        job_data["message"] = "Document chunking complete, storing chunks..."
        redis_client.setex(job_key, 3600, json.dumps(job_data))

        # Store chunks in database and prepare for embedding generation
        chunk_ids = []
        chunk_texts = []
        
        for chunk_data in chunks:
            chunk = Chunk(
                document_id=document_id,
                ord=chunk_data['id'],
                text=chunk_data['text'],
                page_start=chunk_data['page_start'],
                page_end=chunk_data['page_end'],
                token_count=chunk_data['token_count']
            )
            db.add(chunk)
            db.flush()  # Get the chunk.id from database
            
            # Track chunk IDs and texts for embedding generation
            chunk_ids.append(chunk.id)
            chunk_texts.append(chunk_data['text'])
        
        db.commit()
        db_logger.info(f"Chunks stored in database", document_id=document_id, chunks_count=len(chunk_ids))
        
        # Update progress - chunks stored
        job_data["progress"] = 60
        job_data["message"] = "Chunks stored, generating embeddings..."
        redis_client.setex(job_key, 3600, json.dumps(job_data))
        
        # Generate embeddings for all chunks
        openai_logger.info(f"Generating embeddings", document_id=document_id, chunks_count=len(chunk_texts))
        embeddings = generate_embeddings(chunk_texts)
        openai_logger.info(f"Embeddings generated", document_id=document_id, embeddings_count=len(embeddings))
        
        # Update progress - embeddings generated
        job_data["progress"] = 80
        job_data["message"] = "Embeddings generated, storing in vector database..."
        redis_client.setex(job_key, 3600, json.dumps(job_data))
        
        # Store embeddings in Qdrant
        qdrant_logger.info(f"Storing embeddings in Qdrant", document_id=document_id, points_count=len(chunk_ids))
        try:
            points = []
            for chunk_id, embedding_vector in zip(chunk_ids, embeddings):
                point = PointStruct(
                    id=chunk_id,
                    vector=embedding_vector,
                    payload={
                        "chunk_id": chunk_id,
                        "document_id": document_id
                    }
                )
                points.append(point)
            
            qdrant_client.upsert(
                collection_name="embeddings",
                points=points
            )
            
            qdrant_logger.info(f"Embeddings stored in Qdrant", document_id=document_id, points_stored=len(points))
        except Exception as qdrant_error:
            qdrant_logger.exception(f"Qdrant storage error", document_id=document_id, error=str(qdrant_error))
            
        document.status = "ready"
        db.commit()
        db_logger.info(f"Document processing completed successfully", document_id=document_id)
        
        # Update progress - completed
        job_data["status"] = "ready"
        job_data["progress"] = 100
        job_data["message"] = "Document processing complete!"
        redis_client.setex(job_key, 3600, json.dumps(job_data))
        
        task_logger.info(f"Document processing completed", document_id=document_id)
        
    except Exception as e:
        task_logger.exception(f"Document processing failed", document_id=document_id, error=str(e))
        document.status = "failed"
        db.commit()
        
        # Update progress - failed
        job_key = f"job:{document_id}"
        job_data = {
            "status": "failed",
            "progress": 0,
            "message": f"Document processing failed: {str(e)}"
        }
        redis_client.setex(job_key, 3600, json.dumps(job_data))
    finally:
        db.close()