"""
Tests for Chat Graph Service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.chat_graph import ChatGraphService
from app.services.chat_state import create_initial_state


class TestChatGraphService:
    """Tests for Chat Graph Service"""
    
    @pytest.mark.asyncio
    async def test_create_initial_state(self):
        """Test initial state creation"""
        state = create_initial_state(
            message="Hello",
            user_id=1,
            session_id="test-session"
        )
        
        assert state["user_id"] == 1
        assert state["session_id"] == "test-session"
        assert len(state["messages"]) == 1
        assert state["messages"][0].content == "Hello"
    
    @pytest.mark.asyncio
    async def test_intent_classification_greeting(self):
        """Test greeting intent classification"""
        from app.services.chat_nodes import ChatNodes
        
        nodes = ChatNodes()
        
        # Test greeting
        intent = nodes._classify_intent_rules("สวัสดีค่ะ")
        assert intent == "greeting"
        
        intent = nodes._classify_intent_rules("Hello")
        assert intent == "greeting"
    
    @pytest.mark.asyncio
    async def test_intent_classification_question(self):
        """Test question intent classification"""
        from app.services.chat_nodes import ChatNodes
        
        nodes = ChatNodes()
        
        # Test question
        intent = nodes._classify_intent_rules("นโยบายการลางานเป็นอย่างไร?")
        assert intent == "question"
        
        intent = nodes._classify_intent_rules("How do I request leave?")
        assert intent == "question"
    
    @pytest.mark.asyncio
    async def test_quality_score_calculation(self):
        """Test quality score calculation"""
        from app.services.chat_nodes import ChatNodes
        
        nodes = ChatNodes()
        
        # Good answer
        score = nodes._calculate_quality_score(
            answer="นโยบายการลางานคือพนักงานมีสิทธิ์ลาป่วยได้ 30 วันต่อปี",
            context=["พนักงานมีสิทธิ์ลาป่วย"]
        )
        assert score >= 0.7
        
        # Empty answer
        score = nodes._calculate_quality_score(answer="", context=[])
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_chat_mock(self):
        """Test chat with mocked services"""
        service = ChatGraphService(use_checkpointer=False)
        
        # Mock the nodes
        service.nodes.load_memory = AsyncMock(side_effect=lambda s: s)
        service.nodes.classify_intent = AsyncMock(side_effect=lambda s: {**s, "intent": "greeting"})
        service.nodes.handle_greeting = AsyncMock(side_effect=lambda s: {
            **s, 
            "final_answer": "สวัสดีค่ะ",
            "messages": s["messages"] + [MagicMock(content="สวัสดีค่ะ")]
        })
        service.nodes.save_memory = AsyncMock(side_effect=lambda s: s)
        
        result = await service.chat(
            message="สวัสดี",
            user_id=1,
            session_id="test"
        )
        
        assert "answer" in result
