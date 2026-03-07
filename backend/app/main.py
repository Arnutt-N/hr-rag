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
    return {"status": "ok"}


# Routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(llm.router)
app.include_router(evaluation.router)
app.include_router(admin.router)
