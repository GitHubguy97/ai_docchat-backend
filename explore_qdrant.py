#!/usr/bin/env python3
"""
Quick script to explore Qdrant collections and data
"""

from qdrant_client import QdrantClient

def explore_qdrant():
    """Explore Qdrant collections and data"""
    try:
        # Connect to Qdrant
        client = QdrantClient(host="127.0.0.1", port=6333)
        
        # Get all collections
        collections = client.get_collections()
        print("📁 Collections:")
        for collection in collections.collections:
            print(f"  - {collection.name}")
        
        # Get embeddings collection info
        collection_info = client.get_collection("embeddings")
        print(f"\n📊 Embeddings Collection Info:")
        print(f"  - Points count: {collection_info.points_count}")
        print(f"  - Vector size: {collection_info.config.params.vectors.size}")
        print(f"  - Distance metric: {collection_info.config.params.vectors.distance}")
        
        # Get a few sample points
        print(f"\n🔍 Sample Points:")
        points = client.scroll(
            collection_name="embeddings",
            limit=3
        )[0]  # Get first 3 points
        
        for i, point in enumerate(points):
            print(f"\n  Point {i+1}:")
            print(f"    ID: {point.id}")
            print(f"    Vector dimensions: {len(point.vector)}")
            print(f"    Payload: {point.payload}")
            print(f"    Vector preview: {point.vector[:5]}...")  # First 5 dimensions
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    explore_qdrant()
