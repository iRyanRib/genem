"""
Utility functions for generating embeddings using OpenAI API.
"""

import os
from typing import List, Optional
from openai import OpenAI

from app.core.logging_config import get_logger
from app.utils.serializers import normalize_text

logger = get_logger(__name__)

# Configurações dos embeddings
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 512


class EmbeddingService:
    """Service for generating embeddings using OpenAI API"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key, timeout=30)
    
    def generate_embedding(self, text: str, normalize: bool = True) -> Optional[List[float]]:
        """
        Generate embedding for a given text using OpenAI API.
        
        Args:
            text: Input text to generate embedding for
            normalize: Whether to normalize text before generating embedding
            
        Returns:
            List of floats representing the embedding, or None if error occurred
        """
        if not self.client:
            logger.error("OpenAI client not initialized - check OPENAI_API_KEY")
            return None
        
        if not text or not isinstance(text, str):
            logger.warning("Invalid text provided for embedding generation")
            return None
        
        try:
            # Normalize text if requested
            if normalize:
                processed_text = normalize_text(text)
                logger.debug(f"Normalized text: '{text}' -> '{processed_text}'")
            else:
                processed_text = text
            
            # Limit text length to avoid API errors
            if len(processed_text) > 8000:
                processed_text = processed_text[:8000]
                logger.warning(f"Text truncated to 8000 characters for embedding generation")
            
            # Generate embedding using OpenAI API
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=processed_text,
                dimensions=EMBEDDING_DIMENSIONS
            )
            
            embedding = response.data[0].embedding
            
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str], normalize: bool = True) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to generate embeddings for
            normalize: Whether to normalize texts before generating embeddings
            
        Returns:
            List of embeddings (may contain None for failed generations)
        """
        if not self.client:
            logger.error("OpenAI client not initialized - check OPENAI_API_KEY")
            return [None] * len(texts)
        
        if not texts:
            return []
        
        try:
            # Process texts
            processed_texts = []
            for text in texts:
                if not text or not isinstance(text, str):
                    processed_texts.append("")
                    continue
                
                if normalize:
                    processed_text = normalize_text(text)
                else:
                    processed_text = text
                
                # Limit text length
                if len(processed_text) > 8000:
                    processed_text = processed_text[:8000]
                
                processed_texts.append(processed_text)
            
            # Generate embeddings in batch
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=processed_texts,
                dimensions=EMBEDDING_DIMENSIONS
            )
            
            embeddings = [data.embedding for data in response.data]
            
            logger.debug(f"Generated {len(embeddings)} embeddings in batch")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings batch: {e}")
            return [None] * len(texts)


# Singleton instance
embedding_service = EmbeddingService()


def generate_description_embedding(description: str) -> Optional[List[float]]:
    """
    Generate embedding for exam description.
    
    This is a convenience function that normalizes the description text
    and generates an embedding using the embedding service.
    
    Args:
        description: Exam description in natural language
        
    Returns:
        List of floats representing the embedding, or None if error occurred
        
    Example:
        >>> embedding = generate_description_embedding("questões de matemática sobre funções")
        >>> len(embedding)
        512
    """
    return embedding_service.generate_embedding(description, normalize=True)