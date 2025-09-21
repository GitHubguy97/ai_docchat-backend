from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.models import Document, Chunk, Embedding
from app.utils.chunking import smart_chunk_document
from app.utils.embeddings import generate_embeddings
from typing import List, Dict
import json

@celery_app.task
def process_document(document_id: int, full_text: str):
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
        
        # Chunk with smart page-aware strategy
        print("Chunking document with smart page-aware strategy...")
        chunks = smart_chunk_document(full_text)
        print(f"Created {len(chunks)} chunks")

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
        
        # Generate embeddings for all chunks
        print(f"Generating embeddings for {len(chunk_texts)} chunks...")
        embeddings = generate_embeddings(chunk_texts)
        print(f"Generated {len(embeddings)} embeddings")
        
        # Store embeddings in database
        print("Storing embeddings in database...")
        for chunk_id, embedding_vector in zip(chunk_ids, embeddings):
            embedding = Embedding(
                chunk_id=chunk_id,
                vector_data=json.dumps(embedding_vector)
            )
            db.add(embedding)
        
        db.commit()
        print(f"Stored {len(embeddings)} embeddings in database")
        
        document.status = "ready"
        db.commit()
        
        print(f"Document {document_id} processed successfully")
        
    except Exception as e:
        print(f"Error processing document {document_id}: {e}")
        document.status = "failed"
        db.commit()
    finally:
        db.close()