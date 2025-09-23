from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.database import SessionLocal
from app.models.models import Chunk
from typing import List, Dict, Tuple
import json

def search_similar_chunks(query_embedding: List[float], top_k: int = 6, document_id: int = None) -> List[Dict]:
    """
    Search for similar chunks using vector similarity in Qdrant.
    
    Args:
        query_embedding: The query vector (1536 dimensions for OpenAI embeddings)
        top_k: Number of top similar chunks to retrieve
        document_id: Document ID to filter results (required for document-specific search)
    
    Returns:
        List of dictionaries containing:
        - chunk_id: The chunk ID from database
        - similarity_score: Cosine similarity score (0-1, higher is more similar)
        - text: The chunk text content (for LLM input)
        - page_start: Starting page number (for citations)
        - page_end: Ending page number (for citations)
        - token_count: Number of tokens in the chunk (for cost tracking)
    """
    try:
        # Connect to Qdrant
        qdrant_client = QdrantClient(host="127.0.0.1", port=6333)
        
        # Prepare search parameters
        search_params = {
            "collection_name": "embeddings",
            "query_vector": query_embedding,
            "limit": top_k,
            "with_payload": True,  # Include metadata (chunk_id, document_id)
            "with_vectors": False  # Don't return vectors (we have them in query)
        }
        
        # Add document filter if specified
        if document_id is not None:
            search_params["query_filter"] = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        
        # Perform vector search in Qdrant
        search_results = qdrant_client.search(**search_params)
        
        # Get database session to fetch only needed chunk data
        db = SessionLocal()
        
        results = []
        for result in search_results:
            chunk_id = result.id
            similarity_score = result.score
            
            # Get only the essential fields from PostgreSQL
            chunk = db.query(Chunk.text, Chunk.page_start, Chunk.page_end, Chunk.token_count).filter(Chunk.id == chunk_id).first()
            
            if chunk:
                results.append({
                    "chunk_id": chunk_id,
                    "similarity_score": similarity_score,
                    "text": chunk.text,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "token_count": chunk.token_count
                })
        
        db.close()
        return results
        
    except Exception as e:
        print(f"Vector search error: {e}")
        return []
