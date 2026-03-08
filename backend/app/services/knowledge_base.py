"""
Knowledge Base Service - Central RAG Repository Management

Handles:
- Document upload and processing
- Vector indexing to Qdrant
- Category management
- Search and retrieval
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.database import KnowledgeDocument, KnowledgeCategory, User
from app.services.vector_store import VectorStoreService
from app.services.embeddings import EmbeddingService
from app.services.file_processor import FileProcessor
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class KnowledgeBaseService:
    """Service for managing central knowledge base"""
    
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.embeddings = EmbeddingService()
        self.file_processor = FileProcessor()
        self.upload_dir = Path(settings.upload_dir) / "knowledge_base"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def upload_document(
        self,
        file: UploadFile,
        title: str,
        description: Optional[str],
        category_id: Optional[int],
        doc_type: Optional[str],
        department: Optional[str],
        tags: List[str],
        created_by: int,
        db: AsyncSession
    ) -> KnowledgeDocument:
        """Upload and process a knowledge base document"""
        
        # Validate file type
        allowed_extensions = settings.allowed_extensions.split(",")
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type '{file_ext}' not allowed. Allowed: {allowed_extensions}"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        storage_filename = f"{file_id}.{file_ext}"
        file_path = self.upload_dir / storage_filename
        
        # Save file
        content = await file.read()
        file_size = len(content)
        
        # Check file size
        max_size = settings.max_file_size_mb * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.max_file_size_mb}MB"
            )
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Extract text content
        try:
            extracted_text = await self.file_processor.extract_text(str(file_path), file_ext)
        except Exception as e:
            logger.error("text_extraction_failed", filename=file.filename, error=str(e))
            extracted_text = None
        
        # Create database record
        doc = KnowledgeDocument(
            title=title,
            description=description,
            filename=storage_filename,
            original_filename=file.filename,
            file_type=file_ext,
            file_size=file_size,
            file_path=str(file_path),
            content=extracted_text,
            category_id=category_id,
            tags=tags,
            doc_type=doc_type,
            department=department,
            created_by=created_by,
            is_indexed=False,
            chunk_count=0,
            language=self._detect_language(extracted_text) if extracted_text else "th"
        )
        
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        
        logger.info(
            "knowledge_document_uploaded",
            document_id=doc.id,
            title=title,
            category_id=category_id,
            file_size=file_size
        )
        
        return doc
    
    async def index_document(
        self,
        document_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Index document to vector database"""
        
        result = await db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
        doc = result.scalar_one_or_none()
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if not doc.content:
            raise HTTPException(status_code=400, detail="Document has no content to index")
        
        # Delete existing vectors if any
        if doc.vector_ids:
            try:
                await self.vector_store.delete_vectors(
                    collection_name=doc.vector_collection,
                    vector_ids=doc.vector_ids
                )
            except Exception as e:
                logger.warning("failed_to_delete_old_vectors", error=str(e))
        
        # Chunk the content
        chunks = self._chunk_text(doc.content, chunk_size=500, overlap=50)
        
        # Generate embeddings and store
        vector_ids = []
        for i, chunk in enumerate(chunks):
            try:
                embedding = await self.embeddings.get_embedding(chunk)
                vector_id = str(uuid.uuid4())
                
                # Store in Qdrant
                await self.vector_store.upsert_vector(
                    collection_name=doc.vector_collection,
                    vector_id=vector_id,
                    vector=embedding,
                    payload={
                        "document_id": doc.id,
                        "title": doc.title,
                        "content": chunk,
                        "chunk_index": i,
                        "category_id": doc.category_id,
                        "doc_type": doc.doc_type,
                        "department": doc.department,
                        "tags": doc.tags,
                        "source": "knowledge_base"
                    }
                )
                vector_ids.append(vector_id)
                
            except Exception as e:
                logger.error("embedding_failed", chunk_index=i, error=str(e))
                continue
        
        # Update document status
        doc.vector_ids = vector_ids
        doc.chunk_count = len(vector_ids)
        doc.is_indexed = len(vector_ids) > 0
        doc.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(
            "document_indexed",
            document_id=doc.id,
            chunks_indexed=len(vector_ids)
        )
        
        return {
            "document_id": doc.id,
            "chunks_indexed": len(vector_ids),
            "is_indexed": doc.is_indexed
        }
    
    async def search_knowledge_base(
        self,
        query: str,
        category_id: Optional[int] = None,
        doc_type: Optional[str] = None,
        department: Optional[str] = None,
        limit: int = 5,
        user_role: str = "user"
    ) -> List[Dict[str, Any]]:
        """Search knowledge base using vector similarity"""
        
        # Generate query embedding
        query_embedding = await self.embeddings.get_embedding(query)
        
        # Build filter
        filter_conditions = {"source": "knowledge_base"}
        if category_id:
            filter_conditions["category_id"] = category_id
        if doc_type:
            filter_conditions["doc_type"] = doc_type
        if department:
            filter_conditions["department"] = department
        
        # Search vectors
        results = await self.vector_store.search_vectors(
            collection_name="knowledge_base",
            query_vector=query_embedding,
            limit=limit,
            filter_conditions=filter_conditions
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "document_id": result.payload.get("document_id"),
                "title": result.payload.get("title"),
                "content": result.payload.get("content"),
                "chunk_index": result.payload.get("chunk_index"),
                "score": result.score,
                "category_id": result.payload.get("category_id"),
                "doc_type": result.payload.get("doc_type"),
                "department": result.payload.get("department"),
                "tags": result.payload.get("tags", [])
            })
        
        return formatted_results
    
    async def reindex_all_documents(
        self,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Reindex all knowledge base documents"""
        
        result = await db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.content.isnot(None))
        )
        documents = result.scalars().all()
        
        indexed_count = 0
        failed_count = 0
        
        for doc in documents:
            try:
                await self.index_document(doc.id, db)
                indexed_count += 1
            except Exception as e:
                logger.error("reindex_failed", document_id=doc.id, error=str(e))
                failed_count += 1
        
        return {
            "total_documents": len(documents),
            "indexed": indexed_count,
            "failed": failed_count
        }
    
    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """Split text into overlapping chunks"""
        if not text:
            return []
        
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            
            # Try to break at sentence boundary
            if end < text_len:
                # Look for sentence endings
                for i in range(min(end, text_len - 1), start, -1):
                    if text[i] in ".!?" and (i + 1 >= text_len or text[i + 1].isspace()):
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= end:
                start = end
        
        return chunks
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection (th or en)"""
        if not text:
            return "th"
        
        # Count Thai characters
        thai_chars = sum(1 for c in text if '\u0e00' <= c <= '\u0e7f')
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return "th"
        
        thai_ratio = thai_chars / total_chars
        return "th" if thai_ratio > 0.3 else "en"


# Singleton instance
knowledge_base_service = KnowledgeBaseService()