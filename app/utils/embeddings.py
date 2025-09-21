import openai
from app.config import settings
import json
from typing import List

# Set OpenAI API key
openai.api_key = settings.openai_api_key

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts
    """
    try:
        response = openai.embeddings.create(
            model=settings.embedding_model,
            input=texts
        )
        return [embedding.embedding for embedding in response.data]
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        # Return dummy embeddings for testing
        return [[0.0] * 1536 for _ in texts]

def generate_single_embedding(text: str) -> List[float]:
    """
    Generate embedding for a single text
    """
    return generate_embeddings([text])[0]