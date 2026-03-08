"""
Unit Tests for Advanced Retrieval Service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.advanced_retrieval import AdvancedRetrievalService


@pytest.fixture
def retrieval_service():
    """Create retrieval service instance."""
    with patch("app.services.advanced_retrieval.get_vector_store_service"), \
         patch("app.services.advanced_retrieval.get_llm_service"):
        return AdvancedRetrievalService()


class TestAdvancedRetrievalService:
    """Tests for AdvancedRetrievalService."""
    
    @pytest.mark.asyncio
    async def test_hybrid_search(self, retrieval_service):
        """Test hybrid search combines vector and keyword results."""
        # Mock vector search
        retrieval_service.vector_store = AsyncMock()
        retrieval_service.vector_store.similarity_search_with_score = AsyncMock(
            return_value=[
                (MagicMock(page_content="doc1", metadata={}), 0.9),
                (MagicMock(page_content="doc2", metadata={}), 0.8),
            ]
        )
        
        # Mock keyword search
        retrieval_service._keyword_search = AsyncMock(
            return_value=[
                (MagicMock(page_content="doc1", metadata={}), 0.95),
                (MagicMock(page_content="doc3", metadata={}), 0.7),
            ]
        )
        
        # Mock reranking
        retrieval_service._rerank_documents = AsyncMock(
            return_value=[
                {"content": "doc1", "score": 0.95},
                {"content": "doc2", "score": 0.85},
            ]
        )
        
        results = await retrieval_service.hybrid_search(
            query="test query",
            collection_name="test_collection",
            k=5
        )
        
        assert len(results) <= 5
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_rerank_documents(self, retrieval_service):
        """Test document reranking."""
        docs = [
            {"content": "relevant doc", "score": 0.7},
            {"content": "less relevant", "score": 0.5},
        ]
        
        # Mock LLM reranking
        retrieval_service.llm_service = AsyncMock()
        retrieval_service.llm_service.chat = AsyncMock(
            return_value='[{"index": 0, "score": 0.9}, {"index": 1, "score": 0.6}]'
        )
        
        results = await retrieval_service._rerank_documents("query", docs)
        
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_keyword_search(self, retrieval_service):
        """Test keyword-based search."""
        retrieval_service.vector_store = AsyncMock()
        retrieval_service.vector_store.search = AsyncMock(
            return_value=[
                MagicMock(page_content="keyword match", metadata={}, score=0.8)
            ]
        )
        
        results = await retrieval_service._keyword_search(
            collection_name="test",
            query="keyword",
            k=5
        )
        
        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
