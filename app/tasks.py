from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.models import Document, Chunk
from app.utils.chunking import smart_chunk_document
from app.utils.embeddings import generate_embeddings
from app.redis_client import redis_client
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from app.qdrant_setup import setup_qdrant_collection
from typing import List, Dict
import json

@celery_app.task
def process_document(document_id: int, full_text: str):
    """
    Background task to process a document
    """
    print(f"Starting to process document {document_id}")
    
    # Ensure Qdrant collection exists
    setup_qdrant_collection()

    # Get database session
    db = SessionLocal()
    
    # Initialize Qdrant client
    qdrant_client = QdrantClient(host="127.0.0.1", port=6333)
    
    try:
        # Get the document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            print(f"Document {document_id} not found")
            return
        
        # Update status to processing
        document.status = "processing"
        db.commit()
        
        # Update job progress in Redis
        job_key = f"job:{document_id}"
        job_data = {
            "status": "processing",
            "progress": 20,
            "message": "Starting document processing..."
        }
        redis_client.setex(job_key, 3600, json.dumps(job_data))  # 1 hour TTL
        
        # Chunk with smart page-aware strategy
        print("Chunking document with smart page-aware strategy...")
        chunks = smart_chunk_document(full_text)
        print(f"Created {len(chunks)} chunks")
        
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
        print("Chunks added to database")
        
        # Update progress - chunks stored
        job_data["progress"] = 60
        job_data["message"] = "Chunks stored, generating embeddings..."
        redis_client.setex(job_key, 3600, json.dumps(job_data))
        
        # Generate embeddings for all chunks
        print(f"Generating embeddings for {len(chunk_texts)} chunks...")
        embeddings = generate_embeddings(chunk_texts)
        print(f"Generated {len(embeddings)} embeddings")
        
        # Update progress - embeddings generated
        job_data["progress"] = 80
        job_data["message"] = "Embeddings generated, storing in vector database..."
        redis_client.setex(job_key, 3600, json.dumps(job_data))
        
        # Store embeddings in Qdrant
        print("Storing embeddings in Qdrant...")
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
            
            print(f"Points: {points}")
            print(f"Stored {len(embeddings)} embeddings in Qdrant")
        except Exception as qdrant_error:
            print(f"Qdrant error: {qdrant_error}")
            
        document.status = "ready"
        db.commit()
        print(f"Document {document_id} processing completed successfully")
        
        # Update progress - completed
        job_data["status"] = "ready"
        job_data["progress"] = 100
        job_data["message"] = "Document processing complete!"
        redis_client.setex(job_key, 3600, json.dumps(job_data))
        
    except Exception as e:
        print(f"Document processing failed: {str(e)}")
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