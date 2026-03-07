"""
Pytest configuration and fixtures for HR-RAG Backend Tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# Set up test environment variables before importing app
import os
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-unit-tests-only"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"
os.environ["DATABASE_URL"] = "mysql+aiomysql://test:test@localhost/test_db"


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with patch('app.main.init_db') as mock_init:
        mock_init.return_value = AsyncMock()
        with patch('app.services.cache.get_cache_service') as mock_cache:
            mock_cache_instance = MagicMock()
            mock_cache_instance.connect = AsyncMock()
            mock_cache_instance.disconnect = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            from app.main import app
            return TestClient(app)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.add = MagicMock()
    return mock_session


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    from app.models.database import User, UserRole
    user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        hashed_password="$2b$12$mocked_hash",
        full_name="Test User",
        role=UserRole.USER,
        is_member=True,
        is_active=True
    )
    return user


@pytest.fixture
def mock_project():
    """Create a mock project for testing."""
    from app.models.database import Project
    project = Project(
        id=1,
        name="Test Project",
        description="A test project",
        owner_id=1,
        is_public=False,
        settings={},
        vector_collection="test_collection"
    )
    return project


@pytest.fixture
def auth_headers():
    """Create authentication headers with a mock token."""
    from app.core.security import create_access_token
    token = create_access_token({"sub": "1"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_cache():
    """Create a mock cache service."""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()
    return mock


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store service."""
    mock = MagicMock()
    mock.search = AsyncMock(return_value=[
        {"text": "Sample document text", "score": 0.9, "document_id": 1, "filename": "test.pdf"}
    ])
    return mock
