#!/usr/bin/env python3
"""
Test script for vector search functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.vector_search import search_similar_chunks, search_similar_chunks_simple
from app.utils.embeddings import generate_single_embedding

def test_vector_search():
    """Test vector search with sample questions"""
    
    # Sample questions to test
    test_questions = [
        "What are the powers of Congress?",
        "How is the president elected?",
        "What are the rights of citizens?",
        "How can the Constitution be amended?",
        "What is the role of the Supreme Court?"
    ]
    
    print("🔍 Testing Vector Search")
    print("=" * 50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Question {i}: {question}")
        print("-" * 40)
        
        try:
            # Generate embedding for the question
            print("Generating query embedding...")
            query_embedding = generate_single_embedding(question)
            print(f"✅ Query embedding generated ({len(query_embedding)} dimensions)")
            
            # Search for similar chunks
            print("Searching for similar chunks...")
            results = search_similar_chunks(query_embedding, top_k=5)
            
            if results:
                print(f"✅ Found {len(results)} similar chunks:")
                for j, result in enumerate(results, 1):
                    similarity_score = result["similarity_score"]
                    
                    print(f"\n  📄 Chunk {j} (Score: {similarity_score:.4f}):")
                    print(f"    📖 Pages: {result['page_start']}-{result['page_end']}")
                    print(f"    🆔 Chunk ID: {result['chunk_id']}")
                    print(f"    📊 Tokens: {result['token_count']}")
                    print(f"    📝 Text preview: {result['text'][:150]}...")
            else:
                print("❌ No similar chunks found")
                
        except Exception as e:
            print(f"❌ Error testing question: {e}")
        
        print("\n" + "=" * 50)

def test_simple_search():
    """Test simple search without database lookup"""
    print("\n🔍 Testing Simple Vector Search")
    print("=" * 50)
    
    question = "What are the powers of Congress?"
    print(f"📝 Question: {question}")
    
    try:
        query_embedding = generate_single_embedding(question)
        results = search_similar_chunks_simple(query_embedding, top_k=3)
        
        if results:
            print(f"✅ Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"\n  Result {i}:")
                print(f"    Chunk ID: {result['chunk_id']}")
                print(f"    Score: {result['similarity_score']:.4f}")
                print(f"    Payload: {result['payload']}")
        else:
            print("❌ No results found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Full vector search test (with database lookup)")
    print("2. Simple vector search test (Qdrant only)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_vector_search()
    elif choice == "2":
        test_simple_search()
    else:
        print("Invalid choice. Running full test...")
        test_vector_search()
