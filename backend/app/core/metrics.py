"""
Prometheus Metrics Configuration

Exposes metrics for monitoring with Prometheus and Grafana.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_fastapi_instrumentator import Instrumentator

# Custom metrics
REQUEST_COUNT = Counter(
    "hr_rag_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "hr_rag_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

DOCUMENT_UPLOADS = Counter(
    "hr_rag_document_uploads_total",
    "Total number of document uploads",
    ["status"]
)

CHAT_MESSAGES = Counter(
    "hr_rag_chat_messages_total",
    "Total number of chat messages",
    ["provider"]
)

LLM_REQUESTS = Counter(
    "hr_rag_llm_requests_total",
    "Total number of LLM API requests",
    ["provider", "model", "status"]
)

LLM_LATENCY = Histogram(
    "hr_rag_llm_latency_seconds",
    "LLM request latency in seconds",
    ["provider", "model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

EMBEDDING_REQUESTS = Counter(
    "hr_rag_embedding_requests_total",
    "Total number of embedding requests",
    ["model", "status"]
)

VECTOR_SEARCH_LATENCY = Histogram(
    "hr_rag_vector_search_latency_seconds",
    "Vector search latency in seconds",
    ["collection"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

ACTIVE_USERS = Gauge(
    "hr_rag_active_users",
    "Number of active users"
)

DOCUMENTS_TOTAL = Gauge(
    "hr_rag_documents_total",
    "Total number of documents"
)

VECTOR_COUNT = Gauge(
    "hr_rag_vectors_total",
    "Total number of vectors in database"
)

APP_INFO = Info(
    "hr_rag_app",
    "Application information"
)


def setup_metrics(app):
    """
    Setup Prometheus metrics for the application.
    
    Adds /metrics endpoint for Prometheus scraping.
    """
    # Setup FastAPI instrumentator
    Instrumentator().instrument(app).expose(app)
    
    # Set app info
    APP_INFO.info({
        "version": "1.0.0",
        "service": "hr-rag-backend"
    })
    
    return app


def track_request(method: str, endpoint: str, status: int, latency: float):
    """Track HTTP request metrics."""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)


def track_document_upload(status: str = "success"):
    """Track document upload."""
    DOCUMENT_UPLOADS.labels(status=status).inc()


def track_chat_message(provider: str):
    """Track chat message."""
    CHAT_MESSAGES.labels(provider=provider).inc()


def track_llm_request(provider: str, model: str, status: str, latency: float):
    """Track LLM API request."""
    LLM_REQUESTS.labels(provider=provider, model=model, status=status).inc()
    LLM_LATENCY.labels(provider=provider, model=model).observe(latency)


def track_embedding_request(model: str, status: str = "success"):
    """Track embedding request."""
    EMBEDDING_REQUESTS.labels(model=model, status=status).inc()


def track_vector_search(collection: str, latency: float):
    """Track vector search."""
    VECTOR_SEARCH_LATENCY.labels(collection=collection).observe(latency)


def update_active_users(count: int):
    """Update active users gauge."""
    ACTIVE_USERS.set(count)


def update_documents_total(count: int):
    """Update documents total gauge."""
    DOCUMENTS_TOTAL.set(count)


def update_vector_count(count: int):
    """Update vector count gauge."""
    VECTOR_COUNT.set(count)
