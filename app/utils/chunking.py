import tiktoken
import re
from typing import List, Dict

def smart_chunk_document(text: str, chunk_size: int = 900, overlap: int = 150) -> List[Dict]:
    """
    Main chunking function that takes text with inline page markers and creates chunks.
    
    Input: Text with [PAGE:N] markers like "[PAGE:1] First page content [PAGE:2] Second page content"
    Output: List of chunks with accurate page tracking
    """
    if not text.strip():
        return []
    
    encoding = tiktoken.get_encoding("cl100k_base")
    
    # Split text into sentences, preserving page markers
    sentences = re.split(r'(?<=[.!?])\s+|(?=\[PAGE:\d+\])', text)
    
    chunks = []
    current_chunk = ""
    current_tokens = 0
    chunk_id = 0
    current_page = 1
    pages_in_chunk = set()
    
    for sentence in sentences:
        # Check if this sentence is a page marker
        page_match = re.match(r'\[PAGE:(\d+)\]', sentence.strip())
        if page_match:
            current_page = int(page_match.group(1))
            continue
        
        # Skip empty sentences
        if not sentence.strip():
            continue
            
        sentence_tokens = len(encoding.encode(sentence))
        
        # If adding this sentence would exceed chunk size and we have content
        if current_tokens + sentence_tokens > chunk_size and current_chunk.strip():
            # Create chunk from current content
            chunk_data = {
                "id": chunk_id,
                "text": current_chunk.strip(),
                "token_count": current_tokens,
                "page_start": min(pages_in_chunk) if pages_in_chunk else current_page,
                "page_end": max(pages_in_chunk) if pages_in_chunk else current_page
            }
            chunks.append(chunk_data)
            
            # Start new chunk with overlap
            overlap_text = get_overlap_text(current_chunk, overlap, encoding)
            current_chunk = overlap_text + " " + sentence if overlap_text else sentence
            current_tokens = len(encoding.encode(current_chunk))
            
            # Reset page tracking for new chunk
            pages_in_chunk = {current_page}
            chunk_id += 1
        else:
            # Add sentence to current chunk
            if current_chunk:
                current_chunk += " " + sentence
                current_tokens += sentence_tokens
            else:
                current_chunk = sentence
                current_tokens = sentence_tokens
            
            # Track which pages this chunk spans
            pages_in_chunk.add(current_page)
    
    # Add final chunk
    if current_chunk.strip():
        chunk_data = {
            "id": chunk_id,
            "text": current_chunk.strip(),
            "token_count": current_tokens,
            "page_start": min(pages_in_chunk) if pages_in_chunk else current_page,
            "page_end": max(pages_in_chunk) if pages_in_chunk else current_page
        }
        chunks.append(chunk_data)
    
    return chunks

def get_overlap_text(text: str, overlap_tokens: int, encoding) -> str:
    """
    Get the last N tokens of text for overlap between chunks
    """
    tokens = encoding.encode(text)
    if len(tokens) <= overlap_tokens:
        return text
    
    overlap_tokens_list = tokens[-overlap_tokens:]
    return encoding.decode(overlap_tokens_list)