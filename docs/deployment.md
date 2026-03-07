# Deployment Guide (HR-RAG)

## Overview

This guide describes recommended deployment patterns for the HR-RAG system.

**Current stack assumptions (from backend config):**
- Backend: FastAPI (Python)
- Frontend: Next.js (or similar React SPA)
- Relational DB: **TiDB Cloud** (MySQL-compatible) via SQLAlchemy `mysql+pymysql://...`
- Vector DB: **Qdrant** (self-hosted or Qdrant Cloud)
- Embeddings: `BAAI/bge-m3` via `sentence-transformers`
- LLM providers: OpenAI / Anthropic / Google / Ollama

> Note: Web research tool was unavailable in this environment; vendor free-tier details may change. Treat the “free tier” section as guidance and re-check pricing pages before production.

---

## 1) Environment Variables

Create a `.env` file for backend (never commit it):

```bash
# App
DEBUG=false
CORS_ORIGINS=http://localhost:3000

# Database (TiDB Cloud)
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:4000/hr_rag

# JWT
JWT_SECRET_KEY=change-me-long-random
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=hr_documents

# Embeddings
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cpu
EMBEDDING_BATCH_SIZE=32

# LLM Providers
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...

# Ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2

# Upload
MAX_FILE_SIZE=10485760
```

Frontend env (example):

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## 2) Local Development (Docker Compose)

### Recommended compose services
- `frontend`: Next.js dev server
- `backend`: FastAPI (uvicorn)
- `qdrant`: vector database
- Optional: `ollama`: local LLM runtime

Example `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    volumes:
      - ./backend:/app
    depends_on:
      - qdrant

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
    depends_on:
      - backend

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage

  # Optional local LLM
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama:/root/.ollama

volumes:
  qdrant_storage:
  ollama:
```

Run:

```bash
docker compose up --build
```

---

## 3) Production Deployment Options

### Option A: “Mostly Managed” (Recommended)
- **Frontend**: Vercel
- **Backend**: Render / Railway / Fly.io (container)
- **Relational DB**: TiDB Cloud (serverless)
- **Vector DB**: Qdrant Cloud (managed)
- **Cache/Rate limit** (optional): Upstash Redis

Pros: minimal ops, quick to ship.

Checklist:
- [ ] Force HTTPS (Vercel/Render provide this)
- [ ] Set `CORS_ORIGINS` to your production domain only
- [ ] Store secrets in platform secret manager (NOT in env files committed)
- [ ] Enable logging + alerting

### Option B: Self-Hosted VPS
- Nginx/Caddy reverse proxy + TLS
- Docker Compose or systemd services
- Qdrant on the same machine (or separate)
- TiDB Cloud stays managed, or self-host MySQL-compatible DB

Pros: cheaper at small scale, more control.
Cons: you own ops/security.

### Option C: Kubernetes (Enterprise)
- Horizontal scaling for `backend`
- Dedicated node pool for embeddings (CPU/GPU)
- Qdrant cluster (or managed)
- External secrets management (Vault / cloud secrets)

---

## 4) Vector Database Selection (with free/low-cost options)

For RAG, prioritize:
- filtering by metadata (project_id, doc_id)
- good recall/latency
- operational simplicity

### Common options
- **Qdrant**: excellent OSS choice; cloud offering available.
- **Weaviate**: OSS + cloud.
- **Chroma**: simplest local/dev.
- **Postgres + pgvector**: great if you already run Postgres; supports filters well.
- **Milvus** / **Zilliz Cloud**: strong at scale.
- **Pinecone**: managed; great DX.
- **TiDB Cloud Vector Search**: attractive if you want one DB for OLTP + vectors (check current availability/limits).

Recommendation for HR-RAG v1:
- Dev: Chroma or Qdrant local
- Prod: Qdrant Cloud or Postgres+pgvector (if Postgres is already a requirement)

---

## 5) Thai RAG Optimization (Deployment-Sensitive)

- Run embeddings on **CPU initially**; move to GPU if ingestion is heavy.
- Batch embeddings (`EMBEDDING_BATCH_SIZE`) and cache.
- Consider **hybrid retrieval** (semantic + keyword) for Thai mixed-content queries.

---

## 6) Observability

Minimum recommended:
- Structured logs (JSON)
- Request IDs
- LLM latency + token usage metrics
- Vector search latency + top_k

Suggested tools:
- OpenTelemetry + Grafana/Loki
- Sentry for frontend/backend

---

## 7) Release Checklist

- [ ] Secrets stored in secret manager
- [ ] CORS restricted
- [ ] RBAC enabled
- [ ] Rate limiting enabled
- [ ] PII masking strategy decided (log + prompts)
- [ ] Backup strategy for relational DB + vector DB
- [ ] Incident response: key rotation runbook

