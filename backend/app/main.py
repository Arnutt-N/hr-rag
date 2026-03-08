"""HR-RAG Backend - FastAPI entry

Routers:
- /auth
- /projects
- /ingest
- /search
- /chat (SSE + WS)
- /llm
- /evaluation (RAG Evaluation)
- /admin (Admin Panel)

Run:
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.core.request_id import RequestIDMiddleware
from app.core.circuit_breaker import get_all_circuit_stats
from app.core.telemetry import setup_telemetry, shutdown_telemetry
from app.models.database import init_db
from app.services.cache import get_cache_service

from app.routers import auth, projects, ingest, chat, llm, search, evaluation, admin

settings = get_settings()

# Setup structured logging
setup_logging()
logger = get_logger(__name__)

# Setup rate limiter (IP-based)
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title=settings.app_name, debug=settings.debug)

# Add request ID middleware for distributed tracing
app.add_middleware(RequestIDMiddleware)

# Add rate limiter to app state
app.state.limiter = limiter


# Rate limit handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors with proper 429 response."""
    logger.warning(
        "rate_limit_exceeded",
        ip=get_remote_address(request),
        path=request.url.path,
        retry_after=str(exc.detail),
    )
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests",
            "retry_after": str(exc.detail)
        },
        headers={"Retry-After": str(exc.detail)}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


@app.on_event("startup")
async def on_startup():
    # For dev: create tables if not exist
    # In prod: replace with Alembic migrations.
    await init_db()
    
    # Connect to Redis cache
    cache = get_cache_service()
    await cache.connect()


@app.on_event("shutdown")
async def on_shutdown():
    # Close Redis cache connection
    cache = get_cache_service()
    await cache.disconnect()


@app.get("/health")
async def health():
    """Basic health check."""
    return {"status": "ok"}


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check with all services status."""
    from datetime import datetime
    import time
    
    health_status = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {},
        "circuit_breakers": get_all_circuit_stats()
    }
    
    # Check Redis
    try:
        cache = get_cache_service()
        start = time.time()
        await cache.ping()
        health_status["services"]["redis"] = {
            "status": "ok",
            "latency_ms": round((time.time() - start) * 1000, 2)
        }
    except Exception as e:
        health_status["services"]["redis"] = {"status": "error", "message": str(e)}
        health_status["status"] = "degraded"
    
    # Check PostgreSQL
    try:
        from sqlalchemy import text
        from app.models.database import engine
        start = time.time()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["services"]["postgres"] = {
            "status": "ok",
            "latency_ms": round((time.time() - start) * 1000, 2)
        }
    except Exception as e:
        health_status["services"]["postgres"] = {"status": "error", "message": str(e)}
        health_status["status"] = "degraded"
    
    # Check Qdrant
    try:
        import httpx
        start = time.time()
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"http://{settings.qdrant_host}:{settings.qdrant_port}/health", timeout=5.0)
            health_status["services"]["qdrant"] = {
                "status": "ok" if resp.status_code == 200 else "error",
                "latency_ms": round((time.time() - start) * 1000, 2)
            }
    except Exception as e:
        health_status["services"]["qdrant"] = {"status": "error", "message": str(e)}
        health_status["status"] = "degraded"
    
    return health_status


# Routers with API versioning
app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(llm.router, prefix="/api/v1")
app.include_router(evaluation.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
