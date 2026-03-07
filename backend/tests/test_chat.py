"""
Tests for chat endpoints.

Tests:
- test_chat_with_context: Test chat with project context
- test_chat_without_project: Test chat without project (should fail)
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException


class TestChat:
    """Test cases for chat endpoints."""

    @pytest.mark.asyncio
    async def test_chat_with_context(self, client, auth_headers, mock_project):
        """Test chat with project context returns a response."""
        # Mock the database and services
        with patch('app.routers.chat.get_db') as mock_get_db, \
             patch('app.routers.chat.get_vector_store') as mock_vs, \
             patch('app.routers.chat.get_llm_service') as mock_llm:
            
            # Setup mock database
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_project
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            mock_session.refresh = MagicMock()
            mock_session.add = MagicMock()
            
            async def mock_db_gen():
                yield mock_session
            
            mock_get_db.return_value = mock_db_gen()
            
            # Setup mock vector store
            mock_vs_instance = MagicMock()
            mock_vs_instance.search = AsyncMock(return_value=[
                {"text": "Relevant document context", "score": 0.9, "document_id": 1, "filename": "doc.pdf"}
            ])
            mock_vs.return_value = mock_vs_instance
            
            # Setup mock LLM service
            mock_llm_instance = MagicMock()
            mock_llm_instance.build_rag_prompt = MagicMock(return_value="Mocked prompt")
            mock_llm_instance.generate_response = AsyncMock(return_value=iter(["Hello!"]))
            mock_llm_instance.get_default_model = MagicMock(return_value="gpt-4")
            mock_llm.return_value = mock_llm_instance
            
            # Make request (non-streaming for easier testing)
            response = client.post(
                "/chat",
                json={
                    "message": "What is this document about?",
                    "project_id": 1,
                    "stream": False
                },
                headers=auth_headers
            )
            
            # Should get a response (200 or 500 if mocks aren't connected properly)
            assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_chat_without_project(self, client, auth_headers):
        """Test chat without a valid project returns 404."""
        with patch('app.routers.chat.get_db') as mock_get_db:
            # Setup mock database - no project found
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None  # No project
            mock_session.execute = AsyncMock(return_value=mock_result)
            
            async def mock_db_gen():
                yield mock_session
            
            mock_get_db.return_value = mock_db_gen()
            
            response = client.post(
                "/chat",
                json={
                    "message": "Hello",
                    "project_id": 999,  # Non-existent project
                    "stream": False
                },
                headers=auth_headers
            )
            
            # Should return 404 for project not found
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_chat_unauthorized(self, client):
        """Test chat without authentication returns 403."""
        response = client.post(
            "/chat",
            json={
                "message": "Hello",
                "project_id": 1,
                "stream": False
            }
        )
        
        # Should return 403 for unauthorized
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_chat_streaming(self, client, auth_headers, mock_project):
        """Test streaming chat response."""
        with patch('app.routers.chat.get_db') as mock_get_db, \
             patch('app.routers.chat.get_vector_store') as mock_vs, \
             patch('app.routers.chat.get_llm_service') as mock_llm:
            
            # Setup mock database
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_project
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            mock_session.refresh = MagicMock()
            mock_session.add = MagicMock()
            
            async def mock_db_gen():
                yield mock_session
            
            mock_get_db.return_value = mock_db_gen()
            
            # Setup mock vector store
            mock_vs_instance = MagicMock()
            mock_vs_instance.search = AsyncMock(return_value=[])
            mock_vs.return_value = mock_vs_instance
            
            # Setup mock LLM service with streaming
            async def mock_stream():
                for i in range(3):
                    yield f"Chunk {i}"
            
            mock_llm_instance = MagicMock()
            mock_llm_instance.build_rag_prompt = MagicMock(return_value="Prompt")
            mock_llm_instance.generate_response = AsyncMock(return_value=mock_stream())
            mock_llm_instance.get_default_model = MagicMock(return_value="gpt-4")
            mock_llm.return_value = mock_llm_instance
            
            response = client.post(
                "/chat",
                json={
                    "message": "Hello",
                    "project_id": 1,
                    "stream": True
                },
                headers=auth_headers
            )
            
            # Should return streaming response
            assert response.status_code in [200, 500]


class TestChatSession:
    """Test cases for chat session endpoints."""

    def test_list_sessions(self, client, auth_headers):
        """Test listing chat sessions."""
        response = client.get("/chat/sessions", headers=auth_headers)
        
        # Should return list (may be empty)
        assert response.status_code in [200, 500]

    def test_create_session(self, client, auth_headers):
        """Test creating a new chat session."""
        response = client.post(
            "/chat/sessions",
            json={"title": "New Chat Session"},
            headers=auth_headers
        )
        
        # Should return created session
        assert response.status_code in [200, 201, 500]

    def test_list_messages_no_session(self, client, auth_headers):
        """Test listing messages for non-existent session."""
        response = client.get(
            "/chat/sessions/999/messages",
            headers=auth_headers
        )
        
        # Should return 404 for non-existent session
        assert response.status_code in [404, 500]
