"""
HR-RAG Backend - Embedding Service
Thai language embedding support using BAAI/bge-m3 or intfloat/multilingual-e5-large
"""

import numpy as np
from typing import List, Optional
import asyncio
from sentence_transformers import SentenceTransformer
from functools import lru_cache

from app.core.config import get_settings

settings = get_settings()


class EmbeddingService:
    """Embedding service for Thai language support"""

    def __init__(self):
        self.model_name = settings.embedding_model
        self.device = settings.embedding_device
        self.batch_size = settings.embedding_batch_size
        self._model = None
        self._model_lock = asyncio.Lock()

    @property
    def model(self):
        """Lazy load model (sync access — use _ensure_model in async context)"""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model

    async def _ensure_model(self):
        """Thread-safe lazy model initialisation."""
        if self._model is None:
            async with self._model_lock:
                if self._model is None:
                    loop = asyncio.get_running_loop()
                    self._model = await loop.run_in_executor(
                        None,
                        lambda: SentenceTransformer(self.model_name, device=self.device)
                    )
    
    async def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            numpy array of embeddings with shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])

        await self._ensure_model()
        loop = asyncio.get_running_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=len(texts) > 10,
                convert_to_numpy=True
            )
        )
        return embeddings
    
    async def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query
        
        Args:
            query: Query string
            
        Returns:
            numpy array of embedding
        """
        return await self.embed_texts([query])
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding model"""
        return self.model.get_sentence_embedding_dimension()
    
    async def compute_similarity(
        self, 
        embeddings1: np.ndarray, 
        embeddings2: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarity between two sets of embeddings
        
        Args:
            embeddings1: First set of embeddings
            embeddings2: Second set of embeddings
            
        Returns:
            Array of similarity scores
        """
        # Normalize embeddings
        norm1 = embeddings1 / np.linalg.norm(embeddings1, axis=1, keepdims=True)
        norm2 = embeddings2 / np.linalg.norm(embeddings2, axis=1, keepdims=True)
        
        # Compute cosine similarity
        return np.dot(norm1, norm2.T)


# Global singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get the global embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


async def generate_embeddings(texts: List[str]) -> np.ndarray:
    """Convenience function to generate embeddings"""
    service = get_embedding_service()
    return await service.embed_texts(texts)


async def generate_query_embedding(query: str) -> np.ndarray:
    """Convenience function to generate query embedding"""
    service = get_embedding_service()
    return await service.embed_query(query)
