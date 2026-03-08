"""
Embedding Generation Tasks
"""

import asyncio
from typing import List, Dict, Any
from celery import shared_task

from app.core.celery_app import celery_app
from app.core.logging import get_logger
from app.services.embeddings import get_embedding_service

logger = get_logger(__name__)


@celery_app.task(bind=True, max_retries=3, rate_limit="10/m")
def generate_embeddings_task(self, texts: List[str]) -> Dict[str, Any]:
    """
    Generate embeddings for a list of texts.
    
    Rate limited to 10 calls per minute to avoid API limits.
    """
    logger.info(f"Generating embeddings for {len(texts)} texts")
    
    try:
        embedding_service = get_embedding_service()
        embeddings = asyncio.run(embedding_service.embed_documents(texts))
        
        return {
            "status": "success",
            "count": len(embeddings),
            "dimension": len(embeddings[0]) if embeddings else 0
        }
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(bind=True)
def batch_generate_embeddings_task(self, texts: List[str], batch_size: int = 32) -> Dict[str, Any]:
    """
    Generate embeddings in batches by calling the embedding service directly
    (rather than dispatching sub-tasks which would lose results).
    """
    total_count = 0
    total_batches = (len(texts) + batch_size - 1) // batch_size

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_num = i // batch_size + 1
        logger.info(f"Processing batch {batch_num}/{total_batches}")

        try:
            embedding_service = get_embedding_service()
            embeddings = asyncio.run(embedding_service.embed_texts(batch))
            total_count += len(embeddings)
        except Exception as e:
            logger.error(f"Batch {batch_num} embedding failed: {e}")

    return {
        "status": "success",
        "total_embeddings": total_count,
    }
