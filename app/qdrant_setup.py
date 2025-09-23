#!/usr/bin/env python3
"""
Helper script to set up Qdrant collection for embeddings
Run this after starting the Qdrant container
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import sys

def setup_qdrant_collection():
    """Create the embeddings collection in Qdrant"""
    try:
        # Connect to Qdrant
        client = QdrantClient(host="localhost", port=6333)
        
        # Create collection for embeddings
        collection_name = "embeddings"
        
        # Check if collection already exists
        collections = client.get_collections()
        if collection_name in [col.name for col in collections.collections]:
            print(f"Collection '{collection_name}' already exists")
            return
        
        # Create collection with 1536 dimensions (text-embedding-3-small)
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=1536,  # OpenAI text-embedding-3-small dimensions
                distance=Distance.COSINE
            )
        )
        
        print(f"✅ Collection '{collection_name}' created successfully!")
        print(f"   - Dimensions: 1536")
        print(f"   - Distance: COSINE")
        print(f"   - Ready for vector search!")
        
    except Exception as e:
        print(f"❌ Error setting up Qdrant: {e}")
        print("Make sure Qdrant is running on localhost:6333")
        sys.exit(1)

if __name__ == "__main__":
    setup_qdrant_collection()
