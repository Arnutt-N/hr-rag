"""
LangChain Vector Store Service - Qdrant integration via LangChain
"""

from typing import List, Optional, Dict, Any
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings


class LangChainVectorStoreService:
    """
    Vector store service using LangChain Qdrant integration.
    Provides unified interface for document indexing and retrieval.
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        api_key: Optional[str] = None,
        url: Optional[str] = None
    ):
        """
        Initialize vector store service.
        
        Args:
            host: Qdrant host
            port: Qdrant port
            api_key: Qdrant API key
            url: Qdrant URL (for cloud)
        """
        # Initialize Qdrant client
        if url:
            # Qdrant Cloud
            self.client = QdrantClient(url=url, api_key=api_key)
        else:
            # Local Qdrant
            self.client = QdrantClient(
                host=host or getattr(settings, "qdrant_host", "localhost"),
                port=port or getattr(settings, "qdrant_port", 6333),
                api_key=api_key or getattr(settings, "qdrant_api_key", None)
            )
        
        self._embeddings = None
        self._vector_stores: Dict[str, QdrantVectorStore] = {}
    
    @property
    def embeddings(self):
        """Get embeddings instance (lazy load)."""
        if self._embeddings is None:
            from langchain_openai import OpenAIEmbeddings
            
            self._embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=getattr(settings, "openai_api_key", None) or os.environ.get("OPENAI_API_KEY")
            )
        
        return self._embeddings
    
    def get_vector_store(self, collection_name: str) -> QdrantVectorStore:
        """
        Get or create vector store for collection.
        
        Args:
            collection_name: Collection name
        
        Returns:
            QdrantVectorStore instance
        """
        if collection_name not in self._vector_stores:
            self._vector_stores[collection_name] = QdrantVectorStore(
                client=self.client,
                collection_name=collection_name,
                embedding=self.embeddings
            )
        
        return self._vector_stores[collection_name]
    
    async def create_collection(
        self,
        collection_name: str,
        vector_size: int = 1536,
        recreate: bool = False
    ) -> bool:
        """
        Create collection in Qdrant.
        
        Args:
            collection_name: Collection name
            vector_size: Embedding vector size
            recreate: Delete existing collection if exists
        
        Returns:
            True if successful
        """
        try:
            # Check if exists
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            
            if exists and recreate:
                self.client.delete_collection(collection_name)
                exists = False
            
            if not exists:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE
                    )
                )
            
            return True
            
        except Exception as e:
            print(f"Error creating collection: {e}")
            return False
    
    async def add_documents(
        self,
        collection_name: str,
        documents: List[Document],
        batch_size: int = 100
    ) -> List[str]:
        """
        Add documents to vector store.
        
        Args:
            collection_name: Collection name
            documents: Documents to add
            batch_size: Batch size for indexing
        
        Returns:
            List of document IDs
        """
        vector_store = self.get_vector_store(collection_name)
        
        # Add in batches
        all_ids = []
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            if hasattr(vector_store, 'aadd_documents'):
                ids = await vector_store.aadd_documents(batch)
            else:
                ids = vector_store.add_documents(batch)
            
            all_ids.extend(ids)
        
        return all_ids
    
    async def similarity_search(
        self,
        collection_name: str,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None
    ) -> List[Document]:
        """
        Search for similar documents.
        
        Args:
            collection_name: Collection name
            query: Query text
            k: Number of results
            filter_dict: Metadata filter
            score_threshold: Minimum similarity score
        
        Returns:
            List of similar documents
        """
        vector_store = self.get_vector_store(collection_name)
        
        search_kwargs = {"k": k}
        
        if filter_dict:
            search_kwargs["filter"] = filter_dict
        
        if score_threshold:
            # Use similarity search with score
            results = await vector_store.asimilarity_search_with_score(
                query,
                **search_kwargs
            )
            return [doc for doc, score in results if score >= score_threshold]
        
        # Regular similarity search
        return await vector_store.asimilarity_search(query, **search_kwargs)
    
    async def similarity_search_with_score(
        self,
        collection_name: str,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[tuple]:
        """
        Search with similarity scores.
        
        Args:
            collection_name: Collection name
            query: Query text
            k: Number of results
            filter_dict: Metadata filter
        
        Returns:
            List of (document, score) tuples
        """
        vector_store = self.get_vector_store(collection_name)
        
        search_kwargs = {"k": k}
        if filter_dict:
            search_kwargs["filter"] = filter_dict
        
        return await vector_store.asimilarity_search_with_score(query, **search_kwargs)
    
    async def delete_documents(
        self,
        collection_name: str,
        document_ids: List[str]
    ) -> bool:
        """
        Delete documents by IDs.
        
        Args:
            collection_name: Collection name
            document_ids: Document IDs to delete
        
        Returns:
            True if successful
        """
        try:
            vector_store = self.get_vector_store(collection_name)
            vector_store.delete(document_ids)
            return True
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False
    
    async def get_retriever(
        self,
        collection_name: str,
        search_type: str = "similarity",
        search_kwargs: Optional[Dict[str, Any]] = None
    ):
        """
        Get retriever for collection.
        
        Args:
            collection_name: Collection name
            search_type: Search type (similarity, mmr, similarity_score_threshold)
            search_kwargs: Search arguments
        
        Returns:
            Retriever instance
        """
        vector_store = self.get_vector_store(collection_name)
        
        return vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs or {"k": 5}
        )


# Singleton instance
_vector_store_service: Optional[LangChainVectorStoreService] = None


def get_vector_store_service() -> LangChainVectorStoreService:
    """Get or create vector store service singleton."""
    global _vector_store_service
    
    if _vector_store_service is None:
        _vector_store_service = LangChainVectorStoreService()
    
    return _vector_store_service
