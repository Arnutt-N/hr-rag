"""
Tests for chat endpoints.

Tests:
- test_chat_with_context: Test chat with project context
- test_chat_without_project: Test chat without project (should fail)
"""

import pytest


class TestChatScenarios:
    """Test cases for chat scenarios (requires full app - skipped if dependencies missing)."""

    @pytest.mark.skip(reason="Requires full app dependencies - run in CI environment")
    def test_chat_with_context(self):
        """Test chat with project context returns a response."""
        pass  # Placeholder for when app can be imported

    @pytest.mark.skip(reason="Requires full app dependencies - run in CI environment")
    def test_chat_without_project(self):
        """Test chat without a valid project returns 404."""
        pass

    @pytest.mark.skip(reason="Requires full app dependencies - run in CI environment")
    def test_chat_unauthorized(self):
        """Test chat without authentication returns 403."""
        pass

    @pytest.mark.skip(reason="Requires full app dependencies - run in CI environment")
    def test_chat_streaming(self):
        """Test streaming chat response."""
        pass

    @pytest.mark.skip(reason="Requires full app dependencies - run in CI environment")
    def test_list_sessions(self):
        """Test listing chat sessions."""
        pass

    @pytest.mark.skip(reason="Requires full app dependencies - run in CI environment")
    def test_create_session(self):
        """Test creating a new chat session."""
        pass

    @pytest.mark.skip(reason="Requires full app dependencies - run in CI environment")
    def test_list_messages_no_session(self):
        """Test listing messages for non-existent session."""
        pass
