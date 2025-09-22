from typing import List, Dict, Tuple, Optional
from openai import OpenAI
from app.config import settings
from app.redis_client import redis_client
from pydantic import BaseModel
import json
import hashlib
import re

class Citation(BaseModel):
    text: str
    page_start: int
    page_end: int
    chunk_id: int
    exact_text: str
    search_pages: List[int]

def normalize_question(question: str) -> str:
    """
    Normalize a question for consistent caching.
    - Convert to lowercase
    - Remove extra whitespace
    - Remove punctuation variations
    - Sort words for order independence
    """
    # Convert to lowercase and strip
    normalized = question.lower().strip()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove common punctuation variations
    normalized = normalized.replace('?', '').replace('.', '').replace(',', '')
    normalized = normalized.replace('"', '').replace("'", '')
    
    # Optional: Sort words for order independence (uncomment if desired)
    # words = normalized.split()
    # normalized = ' '.join(sorted(words))
    
    return normalized

def get_cached_answer(question: str) -> Optional[Dict]:
    """
    Check Redis cache for a cached answer to the normalized question.
    
    Args:
        question: The user's question
        
    Returns:
        Cached answer dict if found, None otherwise
    """
    try:
        normalized = normalize_question(question)
        question_hash = hashlib.md5(normalized.encode()).hexdigest()
        cache_key = f"answer:{question_hash}"
        
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        return None
        
    except Exception as e:
        print(f"Error checking cache: {str(e)}")
        return None

def cache_answer(question: str, answer: str, citations: List[Citation], document_id: int, ttl: int = 3600):
    """
    Cache the answer in Redis with a TTL.
    
    Args:
        question: The original question
        answer: The generated answer
        citations: List of citations
        document_id: Document ID
        ttl: Time to live in seconds (default 1 hour)
    """
    try:
        normalized = normalize_question(question)
        question_hash = hashlib.md5(normalized.encode()).hexdigest()
        cache_key = f"answer:{question_hash}"
        
        # Convert citations to dict for JSON serialization
        citations_dict = [citation.dict() for citation in citations]
        
        cache_data = {
            "answer": answer,
            "citations": citations_dict,
            "document_id": document_id,
            "cached_at": json.dumps(None),  # We could add timestamp if needed
        }
        
        redis_client.setex(cache_key, ttl, json.dumps(cache_data))
        print(f"Cached answer for question hash: {question_hash}")
        
    except Exception as e:
        print(f"Error caching answer: {str(e)}")

def generate_answer_with_citations(question: str, chunks: List[Dict], document_id: int) -> Tuple[str, List[Citation]]:
    """
    Generate an answer using GPT-4o-mini and extract citations with exact text quotes.
    Includes caching for consistent responses.
    
    Args:
        question: The user's question
        chunks: List of relevant chunks from vector search
        document_id: Document ID for caching
        
    Returns:
        Tuple of (answer, citations)
    """
    # Cache check is now handled at the endpoint level for efficiency
    # Prepare context from chunks
    context_parts = []
    citations = []
    
    for i, chunk in enumerate(chunks):
        context_parts.append(f"[Context {i+1}]\n{chunk['text']}")
        
        # Create search pages list (start with page_start, add page_end if different)
        search_pages = [chunk['page_start']]
        if chunk['page_end'] != chunk['page_start']:
            search_pages.append(chunk['page_end'])
        
        # Create citation for this chunk
        citation = Citation(
            text=chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text'],
            page_start=chunk['page_start'],
            page_end=chunk['page_end'],
            chunk_id=chunk['chunk_id'],
            exact_text="",  # Will be filled by LLM response parsing
            search_pages=search_pages
        )
        citations.append(citation)
    
    context = "\n\n".join(context_parts)
    
    # Create the prompt
    prompt = f"""You are an expert at answering questions based on provided context. 

Question: {question}

Context:
{context}

Instructions:
1. Answer the question based ONLY on the information provided in the context above.
2. If the context doesn't contain enough information to answer the question, say "I cannot find sufficient information to answer this question."
3. Be precise and cite specific details from the context.
4. Use clear, professional language.
5. If the question has multiple parts, address each part systematically.
6. IMPORTANT: For each key claim in your answer, identify the exact quote from the context that supports it.

Format your response as:
ANSWER: [Your complete answer here]

CITATIONS: [List each exact quote that supports your answer, one per line]

Example:
ANSWER: The President appoints ambassadors and Supreme Court justices with Senate approval.

CITATIONS: 
"The President shall appoint Ambassadors, other public Ministers and Consuls, Judges of the supreme Court"
"by and with the Advice and Consent of the Senate"

Answer:"""

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context. Always be accurate and cite specific information when possible. Follow the exact format requested."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.1
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse the response to extract answer and citations
        answer, exact_quotes = parse_llm_response(response_text)
        
        # Update citations with exact quotes
        for i, quote in enumerate(exact_quotes):
            if i < len(citations):
                citations[i].exact_text = quote
        
        # Cache the answer for future use
        cache_answer(question, answer, citations, document_id)
        
        return answer, citations
        
    except Exception as e:
        print(f"Error generating answer: {str(e)}")
        return f"Error generating answer: {str(e)}", citations

def parse_llm_response(response_text: str) -> Tuple[str, List[str]]:
    """
    Parse the LLM response to extract answer and exact quotes.
    
    Args:
        response_text: Raw response from LLM
        
    Returns:
        Tuple of (answer, list_of_exact_quotes)
    """
    try:
        # Split by ANSWER: and CITATIONS: sections
        if "ANSWER:" in response_text and "CITATIONS:" in response_text:
            parts = response_text.split("CITATIONS:")
            answer_part = parts[0].replace("ANSWER:", "").strip()
            citations_part = parts[1].strip() if len(parts) > 1 else ""
            
            # Extract exact quotes (one per line)
            exact_quotes = []
            for line in citations_part.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    # Remove quotes if present
                    quote = line.strip('"').strip("'").strip()
                    if quote:
                        exact_quotes.append(quote)
            
            return answer_part, exact_quotes
        else:
            # Fallback: treat entire response as answer
            return response_text, []
            
    except Exception as e:
        print(f"Error parsing LLM response: {str(e)}")
        return response_text, []
