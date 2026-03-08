"""
Tests for LangChain LLM Service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.llm.langchain_service import LangChainLLMService, get_llm_service


class TestLangChainLLMService:
    """Tests for LangChain LLM Service"""
    
    @pytest.mark.asyncio
    async def test_convert_messages(self):
        """Test message conversion"""
        service = LangChainLLMService(provider="openai")
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "system", "content": "You are helpful"}
        ]
        
        lc_messages = service.convert_messages(messages)
        
        assert len(lc_messages) == 3
        assert lc_messages[0].type == "human"
        assert lc_messages[1].type == "ai"
        assert lc_messages[2].type == "system"
    
    @pytest.mark.asyncio
    async def test_chat_mock(self):
        """Test chat with mocked LLM"""
        service = LangChainLLMService(provider="openai")
        
        # Mock the LLM
        service.llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        service.llm.ainvoke = AsyncMock(return_value=mock_response)
        
        messages = [{"role": "user", "content": "Hello"}]
        response = await service.chat(messages)
        
        assert response == "Test response"
        service.llm.ainvoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_llm_service_singleton(self):
        """Test singleton pattern"""
        service1 = get_llm_service()
        service2 = get_llm_service()
        
        assert service1 is service2
