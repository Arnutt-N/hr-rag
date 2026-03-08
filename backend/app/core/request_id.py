"""
Request ID Middleware - Distributed Tracing Support

Adds unique request ID to every request for easier debugging.
"""

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)

# Header name for request ID
REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds unique request ID to every request.
    
    Flow:
    1. Check if request already has X-Request-ID header
    2. If not, generate new UUID
    3. Add to request state and response headers
    4. Include in all logs
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate request ID
        request_id = request.headers.get(REQUEST_ID_HEADER)
        
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store in request state for access in handlers
        request.state.request_id = request_id
        
        # Log request start
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None
        )
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers[REQUEST_ID_HEADER] = request_id
        
        # Log request complete
        logger.info(
            "request_completed",
            request_id=request_id,
            status_code=response.status_code
        )
        
        return response


def get_request_id(request: Request) -> str:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", "unknown")
