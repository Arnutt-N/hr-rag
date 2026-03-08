"""
Unit Tests for Request ID Middleware
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.core.request_id import (
    RequestIDMiddleware,
    REQUEST_ID_HEADER,
    get_request_id
)


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/test")
    async def test_endpoint(request: Request):
        return {
            "request_id": get_request_id(request),
            "message": "ok"
        }
    
    @app.get("/check-header")
    async def check_header(request: Request):
        return {
            "request_id": get_request_id(request),
            "has_header": REQUEST_ID_HEADER in request.headers
        }
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestRequestIDMiddleware:
    """Tests for RequestIDMiddleware."""
    
    def test_generates_request_id(self, client):
        """Should generate unique request ID."""
        response = client.get("/test")
        
        assert response.status_code == 200
        assert REQUEST_ID_HEADER in response.headers
        assert response.json()["request_id"] is not None
    
    def test_request_id_is_unique(self, client):
        """Each request should have unique ID."""
        response1 = client.get("/test")
        response2 = client.get("/test")
        
        id1 = response1.headers[REQUEST_ID_HEADER]
        id2 = response2.headers[REQUEST_ID_HEADER]
        
        assert id1 != id2
    
    def test_accepts_existing_request_id(self, client):
        """Should accept existing request ID from header."""
        existing_id = "test-request-id-12345"
        
        response = client.get(
            "/check-header",
            headers={REQUEST_ID_HEADER: existing_id}
        )
        
        assert response.status_code == 200
        assert response.headers[REQUEST_ID_HEADER] == existing_id
        assert response.json()["request_id"] == existing_id
    
    def test_request_id_in_response(self, client):
        """Response should include request ID in header."""
        response = client.get("/test")
        
        assert REQUEST_ID_HEADER in response.headers
        request_id = response.headers[REQUEST_ID_HEADER]
        
        # UUID format check
        assert len(request_id) == 36  # UUID format
        assert request_id.count("-") == 4
    
    def test_request_state_has_id(self, client):
        """Request state should contain request ID."""
        response = client.get("/test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["request_id"] is not None


class TestGetRequestID:
    """Tests for get_request_id helper."""
    
    def test_gets_id_from_state(self, client):
        """Should get request ID from request state."""
        response = client.get("/test")
        
        assert response.json()["request_id"] is not None
    
    def test_returns_unknown_if_no_state(self):
        """Should return 'unknown' if no request state."""
        from starlette.requests import Request
        
        # Create request without state
        scope = {
            "type": "http",
            "method": "GET",
            "headers": [],
            "query_string": b"",
            "path": "/test"
        }
        request = Request(scope)
        
        result = get_request_id(request)
        assert result == "unknown"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
