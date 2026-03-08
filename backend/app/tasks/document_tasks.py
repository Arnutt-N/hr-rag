"""
Document Processing Tasks - Async Background Jobs
"""

import asyncio
from typing import Dict, Any, List
from celery import shared_task

from app.core.celery_app import celery_app
from app.core.logging import get_logger
from app.services.file_processor import FileProcessor
from app.services.embeddings import get_embedding_service
from app.services.vector_store_langchain import get_vector_store_service

logger = get_logger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document_task(self, document_id: int, file_path: str) -> Dict[str, Any]:
    """
    Process uploaded document in background.
    
    Steps:
    1. Extract text from document
    2. Split into chunks
    3. Generate embeddings
    4. Store in vector database
    """
    logger.info(f"Processing document {document_id}", document_id=document_id)
    
    try:
        # Run async processing
        result = asyncio.run(_process_document_async(document_id, file_path))
        
        logger.info(
            f"Document processed successfully",
            document_id=document_id,
            chunks=result.get("chunks", 0)
        )
        
        return {
            "status": "success",
            "document_id": document_id,
            "chunks": result.get("chunks", 0)
        }
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}", document_id=document_id)
        
        # Retry task
        raise self.retry(exc=e)


async def _process_document_async(document_id: int, file_path: str) -> Dict[str, Any]:
    """Async document processing."""
    # Process file
    processor = FileProcessor()
    chunks = await processor.process_file(file_path)
    
    # Generate embeddings
    embedding_service = get_embedding_service()
    embeddings = await embedding_service.embed_documents([c.page_content for c in chunks])
    
    # Store in vector database
    vector_store = get_vector_store_service()
    await vector_store.add_documents(
        collection_name=f"doc_{document_id}",
        documents=chunks,
        embeddings=embeddings
    )
    
    return {"chunks": len(chunks)}


@celery_app.task(bind=True)
def batch_process_documents_task(self, document_ids: List[int]) -> Dict[str, Any]:
    """
    Process multiple documents in batch.
    """
    results = []
    
    for doc_id in document_ids:
        try:
            # Queue individual processing task
            process_document_task.delay(doc_id, f"/uploads/{doc_id}")
            results.append({"document_id": doc_id, "status": "queued"})
        except Exception as e:
            results.append({"document_id": doc_id, "status": "error", "error": str(e)})
    
    return {"total": len(document_ids), "results": results}


@celery_app.task
def delete_document_vectors_task(document_id: int) -> Dict[str, Any]:
    """
    Delete document vectors from vector database.
    """
    logger.info(f"Deleting document vectors", document_id=document_id)
    
    async def _delete():
        vector_store = get_vector_store_service()
        await vector_store.delete_collection(f"doc_{document_id}")
    
    asyncio.run(_delete())
    
    return {"status": "success", "document_id": document_id}
