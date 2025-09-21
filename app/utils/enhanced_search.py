#!/usr/bin/env python3
"""
Enhanced search functionality using structured question decomposition.
"""

import json
from typing import List, Dict
from openai import OpenAI
from app.config import settings
from app.utils.embeddings import generate_embeddings
from app.utils.vector_search import search_similar_chunks

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)

def split_question_structured(question: str) -> Dict:
    """
    Use OpenAI function calling to parse a legal question into structured data.
    Returns complexity analysis and essential sub-questions.
    """
    functions = [
        {
            "name": "analyze_question_complexity",
            "description": "Analyze question complexity and extract essential sub-questions",
            "parameters": {
                "type": "object",
                "properties": {
                    "complexity": {
                        "type": "string",
                        "enum": ["simple", "medium", "complex"],
                        "description": "Question complexity level"
                    },
                    "sub_questions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Essential sub-questions needed to answer the original question"
                    },
                    "reasoning": {
                        "type": "string", 
                        "description": "Brief explanation of why these sub-questions were selected"
                    }
                },
                "required": ["complexity", "sub_questions", "reasoning"]
            }
        }
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert at analyzing questions and breaking them down into essential components. Analyze the given question and break it down into the most essential sub-questions needed to provide a complete answer. Focus on distinct aspects that require separate consideration."
                },
                {
                    "role": "user", 
                    "content": f"Analyze this question: '{question}'"
                }
            ],
            functions=functions,
            function_call={"name": "analyze_question_complexity"}
        )
        
        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "analyze_question_complexity":
            return json.loads(function_call.arguments)
        else:
            return {"error": "No function call returned"}
            
    except Exception as e:
        return {"error": f"OpenAI API error: {str(e)}"}

def deduplicate_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    Remove duplicate chunks based on chunk_id while preserving order.
    """
    seen_ids = set()
    unique_chunks = []
    
    for chunk in chunks:
        chunk_id = chunk.get('chunk_id')
        if chunk_id not in seen_ids:
            seen_ids.add(chunk_id)
            unique_chunks.append(chunk)
    
    return unique_chunks

def enhanced_search(question: str, document_id: int) -> List[Dict]:
    """
    Enhanced search using structured question decomposition.
    
    Args:
        question: The user's question
        document_id: Document ID to search within
    
    Returns:
        List of relevant chunks with deduplication
    """
    try:
        # 1. Parse question into structured sub-questions
        parsed = split_question_structured(question)
        
        if "error" in parsed:
            print(f"Question parsing failed: {parsed['error']}")
            # Fallback to simple search
            return search_similar_chunks(
                generate_embeddings([question])[0],
                top_k=8,
                document_id=document_id
            )
        
        # 2. Search each sub-question
        all_chunks = []
        sub_questions = parsed.get('sub_questions', [])
        
        # Limit to reasonable number of sub-questions to control cost
        max_sub_questions = 6
        if len(sub_questions) > max_sub_questions:
            sub_questions = sub_questions[:max_sub_questions]
        
        for sub_q in sub_questions:
            try:
                # Generate embedding for sub-question
                sub_embedding = generate_embeddings([sub_q])[0]
                
                # Search with small top_k per sub-question
                chunks = search_similar_chunks(
                    sub_embedding,
                    top_k=3,  # Increased for better coverage per sub-question
                    document_id=document_id
                )
                all_chunks.extend(chunks)
                
            except Exception as e:
                print(f"Error searching sub-question '{sub_q}': {e}")
                continue
        
        # 3. Deduplicate and return top chunks
        unique_chunks = deduplicate_chunks(all_chunks)
        
        # Sort by similarity score and return top-8
        unique_chunks.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        # Ensure we have enough chunks, fallback to simple search if needed
        if len(unique_chunks) < 3:
            print("Enhanced search returned too few chunks, falling back to simple search")
            return search_similar_chunks(
                generate_embeddings([question])[0],
                top_k=8,
                document_id=document_id
            )
        
        return unique_chunks[:8]
        
    except Exception as e:
        print(f"Enhanced search error: {e}")
        # Fallback to simple search
        try:
            return search_similar_chunks(
                generate_embeddings([question])[0],
                top_k=8,
                document_id=document_id
            )
        except Exception as fallback_error:
            print(f"Fallback search also failed: {fallback_error}")
            return []

def get_search_strategy_info(question: str) -> Dict:
    """
    Get information about the search strategy that would be used for a question.
    Useful for debugging and monitoring.
    """
    parsed = split_question_structured(question)
    
    if "error" in parsed:
        return {
            "strategy": "simple_fallback",
            "reason": parsed["error"],
            "sub_questions": [],
            "complexity": "unknown"
        }
    
    return {
        "strategy": "enhanced",
        "complexity": parsed.get("complexity", "unknown"),
        "sub_questions": parsed.get("sub_questions", []),
        "reasoning": parsed.get("reasoning", ""),
        "total_sub_questions": len(parsed.get("sub_questions", []))
    }
