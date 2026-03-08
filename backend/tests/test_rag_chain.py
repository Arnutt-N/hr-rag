"""
Tests for RAG Chain Service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.rag_chain import RAGChainService


class TestRAGChainService:
    """Tests for RAG Chain Service"""
    
    @pytest.mark.asyncio
    async def test_format_docs(self):
        """Test document formatting"""
        from langchain_core.documents import Document
        
        service = RAGChainService()
        
        docs = [
            Document(page_content="Content 1", metadata={"source": "doc1.pdf"}),
            Document(page_content="Content 2", metadata={"source": "doc2.pdf"})
        ]
        
        formatted = service._format_docs(docs)
        
        assert "Content 1" in formatted
        assert "Content 2" in formatted
        assert "doc1.pdf" in formatted
    
    @pytest.mark.asyncio
    async def test_answer_mock(self):
        """Test answer with mocked services"""
        service = RAGChainService()
        
        # Mock LLM
        service.llm_service = MagicMock()
        service.llm_service.llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test answer"
        service.llm_service.llm.ainvoke = AsyncMock(return_value=mock_response)
        
        # Mock vector store
        service.vector_store = MagicMock()
        service.vector_store.get_vector_store = MagicMock()
        service.vector_store.similarity_search = AsyncMock(return_value=[])
        
        result = await service.answer(
            question="What is the policy?",
            return_sources=False
        )
        
        assert "answer" in result
