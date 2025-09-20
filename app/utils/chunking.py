import tiktoken
import re
from typing import List, Dict

def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[Dict]:
    """
    Split text into chunks with overlap
    """
    # Initialize tokenizer
    encoding = tiktoken.get_encoding("cl100k_base")
    
    # Split text into sentences (rough approximation)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = ""
    current_tokens = 0
    chunk_id = 0
    
    for sentence in sentences:
        sentence_tokens = len(encoding.encode(sentence))
        
        # If adding this sentence would exceed chunk size
        if current_tokens + sentence_tokens > chunk_size and current_chunk:
            # Save current chunk
            chunks.append({
                "id": chunk_id,
                "text": current_chunk.strip(),
                "token_count": current_tokens
            })
            
            # Start new chunk with overlap
            overlap_text = get_overlap_text(current_chunk, overlap, encoding)
            current_chunk = overlap_text + " " + sentence
            current_tokens = len(encoding.encode(current_chunk))
            chunk_id += 1
        else:
            current_chunk += " " + sentence if current_chunk else sentence
            current_tokens += sentence_tokens
    
    # Add final chunk
    if current_chunk:
        chunks.append({
            "id": chunk_id,
            "text": current_chunk.strip(),
            "token_count": current_tokens
        })
    
    return chunks

def get_overlap_text(text: str, overlap_tokens: int, encoding) -> str:
    """
    Get the last N tokens of text for overlap
    """
    tokens = encoding.encode(text)
    if len(tokens) <= overlap_tokens:
        return text
    
    overlap_tokens_list = tokens[-overlap_tokens:]
    return encoding.decode(overlap_tokens_list)