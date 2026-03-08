"""
HR-RAG Backend - Vector Store Service
Qdrant integration for vector storage and retrieval
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
import numpy as np
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from app.core.config import get_settings
from app.services.embeddings import get_embedding_service

settings = get_settings()
logger = logging.getLogger(__name__)


class VectorStore:
    """Qdrant vector database for storing and retrieving document embeddings"""

    def __init__(self):
        self.client = AsyncQdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        self.embedding_service = get_embedding_service()
    
    def _get_collection_name(self, project_id: int) -> str:
        """Get collection name for a project"""
        return f"hr_project_{project_id}"
    
    async def create_collection(self, project_id: int) -> bool:
        """
        Create a new collection for a project
        
        Args:
            project_id: Project ID
            
        Returns:
            True if created successfully
        """
        collection_name = self._get_collection_name(project_id)
        embedding_dim = self.embedding_service.get_embedding_dimension()
        
        # Check if collection exists
        collections = (await self.client.get_collections()).collections
        exists = any(c.name == collection_name for c in collections)

        if not exists:
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=embedding_dim,
                    distance=Distance.COSINE
                )
            )
        return True
    
    async def delete_collection(self, project_id: int) -> bool:
        """Delete collection for a project"""
        collection_name = self._get_collection_name(project_id)
        try:
            await self.client.delete_collection(collection_name=collection_name)
        except Exception as e:
            logger.warning("delete_collection_failed", collection=collection_name, error=str(e))
        return True
    
    async def upsert_documents(
        self,
        project_id: int,
        chunks: List[str],
        metadata: List[Dict[str, Any]],
        doc_ids: Optional[List[int]] = None
    ) -> List[str]:
        """
        Insert document chunks with embeddings
        
        Args:
            project_id: Project ID
            chunks: List of text chunks
            metadata: List of metadata dicts for each chunk
            doc_ids: Optional document IDs
            
        Returns:
            List of vector IDs
        """
        collection_name = self._get_collection_name(project_id)
        
        # Ensure collection exists
        await self.create_collection(project_id)
        
        # Generate embeddings
        embeddings = await self.embedding_service.embed_texts(chunks)
        
        # Create points - batch insert for better performance
        vector_ids = []
        points = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            vector_id = str(uuid.uuid4())
            vector_ids.append(vector_id)
            
            point = PointStruct(
                id=vector_id,
                vector=emb.tolist(),
                payload={
                    "text": chunk,
                    "chunk_index": i,
                    "document_id": doc_ids[i] if doc_ids else metadata[i].get("document_id"),
                    "filename": metadata[i].get("filename", ""),
                    **metadata[i]
                }
            )
            points.append(point)
        
        # Single batch upsert instead of one-by-one
        if points:
            await self.client.upsert(
                collection_name=collection_name,
                points=points
            )
        
        return vector_ids
    
    async def search(
        self,
        project_id: int,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            project_id: Project ID
            query: Query string
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results with text, score, and metadata
        """
        collection_name = self._get_collection_name(project_id)
        
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_query(query)
        
        # Search
        results = await self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding[0].tolist(),
            limit=top_k,
            score_threshold=score_threshold
        )
        
        search_results = []
        for result in results:
            search_results.append({
                "text": result.payload.get("text", ""),
                "score": result.score,
                "document_id": result.payload.get("document_id"),
                "filename": result.payload.get("filename", ""),
                "chunk_index": result.payload.get("chunk_index", 0),
                "vector_id": result.id
            })
        
        return search_results
    
    async def delete_by_document_id(
        self,
        project_id: int,
        document_id: int
    ) -> bool:
        """Delete all vectors for a specific document"""
        collection_name = self._get_collection_name(project_id)
        
        from qdrant_client.models import FilterSelector

        # Delete by filter
        await self.client.delete(
            collection_name=collection_name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )
        return True
    
    async def get_collection_info(self, project_id: int) -> Dict[str, Any]:
        """Get collection information"""
        collection_name = self._get_collection_name(project_id)
        try:
            info = await self.client.get_collection(collection_name=collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.warning("get_collection_info_failed", collection=collection_name, error=str(e))
            return {
                "name": collection_name,
                "vectors_count": 0,
                "points_count": 0,
                "status": "not_found"
            }


# Global singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get the global vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
