# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HR-RAG is a Thai-language HR knowledge management system with advanced RAG (Retrieval-Augmented Generation). It ingests HR documents (PDFs, DOCX, TXT), extracts Thai-aware chunks, embeds them into Qdrant, and answers queries using a LangGraph-orchestrated chat workflow backed by multiple LLM providers.

## Commands

### Development (Local)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in values (note: .env.example doesn't exist - see README.md or core/config.py for required vars)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Qdrant (standalone)
docker run -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant:latest
```

### Docker (Full Stack)

```bash
docker-compose up -d           # start all services
docker-compose ps              # check status
docker-compose logs -f backend # tail logs for a service
docker-compose down            # stop all
```

### Database Migrations (Alembic)

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
alembic history
```

### Background Workers (Celery)

```bash
# In a separate terminal after activating the venv
cd backend
celery -A app.core.celery_app worker --loglevel=info
celery -A app.core.celery_app beat --loglevel=info  # periodic tasks
```

### Testing

```bash
cd backend
pytest
pytest --cov=app
pytest tests/path/to/test_file.py::test_function  # single test
```

### Type Checking & Lint

```bash
cd backend
mypy app/
cd frontend && npm run lint
```

## Architecture

### Backend (`backend/app/`)

All routes are versioned under `/api/v1`. The `main.py` registers routers, rate limiter (slowapi), CORS, security headers, and OpenTelemetry.

**Layers:**

| Directory | Purpose |
|-----------|---------|
| `core/` | Config (`config.py` via pydantic-settings), structured logging (structlog), circuit breaker, Celery, OpenTelemetry, Prometheus metrics |
| `models/` | SQLAlchemy async ORM (`database.py`) + Pydantic schemas (`schemas.py`). DB: PostgreSQL via `asyncpg`. |
| `routers/` | FastAPI routers: `auth`, `projects`, `documents`, `ingest`, `search`, `search_chat`, `chat`, `llm`, `evaluation`, `admin`, `skills`, `swarm`, `notebook`, `ocr`, `graph_rag`, `observability` |
| `services/` | Business logic — see key services below |
| `agents/` | LangGraph agent definitions |
| `tasks/` | Celery async tasks: document processing, embedding, reports, maintenance |
| `mcp/` | MCP server (`server.py`) for tool integrations |

**Key Services:**

- `services/llm/` — Factory pattern (`factory.py`) producing provider-specific clients (OpenAI, Anthropic, Google, Ollama, Kimi, GLM, MiniMax, Qwen, DeepSeek, Custom). `langchain_service.py` wraps them for LangChain compatibility.
- `services/rag_chain.py` — LangChain RAG pipeline; Thai system prompt included.
- `services/chat_graph.py` + `chat_nodes.py` + `chat_state.py` — LangGraph stateful chat workflow. `ChatState` is a `TypedDict` threaded through graph nodes; short-term memory from Redis, long-term from DB.
- `services/vector_store.py` / `vector_store_langchain.py` — Qdrant integration for vector search.
- `services/thai_chunking.py` — `ThaiSemanticChunker`: Thai-aware sentence/section boundaries, configurable min/max chunk size and overlap.
- `services/advanced_retrieval.py` — Hybrid search (vector + BM25 keyword), re-ranking.
- `services/graph_rag.py` + `neo4j_graph.py` — Knowledge graph via Neo4j; entity/relationship extraction.
- `services/embeddings.py` — Embedding generation using `BAAI/bge-m3` (multilingual, Thai support).
- `services/cache.py` — Redis cache for search results and chat history.
- `services/agent_swarm.py` — Multi-agent collaborative system (Coordinator, Researcher, Writer, Critic, Executor, Specialist roles).
- `services/observability.py` — OpenTelemetry tracing helpers.
- `core/circuit_breaker.py` — Circuit breaker decorator for external service calls.
- `services/knowledge_base.py` — Unified knowledge base abstraction layer.
- `services/memory/` — Long-term memory storage and retrieval.
- `services/multi_hop_rag.py` — Multi-hop reasoning over knowledge graph.
- `services/human_in_the_loop.py` — Human verification/feedback integration.

### Frontend (`frontend/`)

Next.js 16 / React 19 app with TypeScript. Key pages: `auth` (login/register), `chat`, `dashboard`, `projects`, `admin`, `evaluation`, `settings`, `guest`. State: Zustand. Data-fetching: TanStack Query. UI: Tailwind CSS + framer-motion. Charts: recharts. Provider configuration in `providers.tsx`.

### Infrastructure

- **PostgreSQL** — relational data (users, projects, documents, sessions, messages)
- **Qdrant** — vector index (`hr_documents` collection by default)
- **Neo4j** — knowledge graph for entity/relationship-based retrieval
- **Redis** — cache (TTL 1h default, 5m for chat), Celery broker/backend
- **Nginx** — reverse proxy + SSL termination (Let's Encrypt via certbot)
- **Prometheus + Grafana** — metrics at `/metrics`, dashboards in `monitoring/`

### API Versioning

All endpoints are prefixed `/api/v1`. Health checks at `/health` (basic) and `/health/detailed` (checks Redis, PostgreSQL, Qdrant + circuit breaker stats).

## Key Configuration Notes

- `core/config.py` uses `pydantic-settings`; all env vars map to `Settings` fields. Call `get_settings()` (LRU-cached) everywhere instead of reading `os.environ` directly.
- `CORS_ORIGINS` is a comma-separated string in `.env` parsed into a list by `Settings.cors_origins` property.
- In dev mode, missing `DATABASE_URL` and `JWT_SECRET_KEY` fall back to insecure defaults with `UserWarning` — never ship this to production.
- `DEFAULT_LLM_PROVIDER` controls which provider the LLM factory selects; per-user override is stored in `User.preferred_llm_provider`.
- Embedding model defaults to `BAAI/bge-m3`; set `EMBEDDING_DEVICE=cuda` to use GPU.
- Celery timezone is `Asia/Bangkok`; periodic tasks (cleanup, daily stats) run via Celery Beat.
- No `.env.example` file exists — refer to `README.md` environment variables table or `core/config.py` `Settings` class for available options.

## Documentation

Additional documentation available in `docs/` directory:
- `deployment.md` / `DEPLOYMENT.md` — Production deployment guides
- `security.md` — Security features and hardening
- `evaluation.md` — RAG evaluation framework
- `thai-embedding-guide.md` — Thai language embedding setup
- `admin-panel.md` — Admin panel features
- `api-reference.md` — API endpoint documentation

## Thai Language Specifics

- Use `ThaiSemanticChunker` (not generic splitters) when ingesting Thai documents — it respects Thai sentence-ending particles and section markers.
- Hybrid retrieval (vector + BM25) is important for Thai/English mixed documents.
- The system prompt in `rag_chain.py` is Thai and instructs the LLM to answer only from retrieved context.
- `pythainlp` is installed for additional Thai NLP support.

## Recent Critical Fixes (2026-03-08 Audit)

The following issues were fixed and should be maintained:
- `vector_store.py`: All Qdrant calls use `AsyncQdrantClient` with `await`
- `chat.py`: SSE generator opens its own `AsyncSessionLocal`; WebSocket auth via first message `{"type": "auth", "token": "..."}`
- `evaluation.py`: Router prefix is `/evaluation` (not `/api/evaluation`) to avoid double prefixing
- `admin.py`: Requires `require_admin` helper for protected routes
- `advanced_retrieval.py`: No bare `except:` clauses; use `hashlib.sha256` not `hash()`
- `embeddings.py`: Use `get_running_loop()` not `get_event_loop()`; async Lock for model init
- `ingest.py`: Content-Length check before reading body; vector upsert failure deletes DB record
- Circular imports: `database.py → schemas.py` is safe (schemas has no DB imports)
