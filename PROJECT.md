# HR-RAG (HR Knowledge Management + RAG)

## Summary

HR-RAG is a Retrieval-Augmented Generation system focused on **Thai language HR documents** (policies, handbooks, announcements). The system ingests documents, builds a vector index, retrieves relevant context, and generates grounded answers via an LLM.

This `PROJECT.md` provides a single place to understand:
- features and scope
- tech stack
- setup instructions
- deployment options
- recommended best practices (Thai RAG + security)

Docs folder: `docs/`
- `docs/architecture.md`
- `docs/thai-embedding-guide.md`
- `docs/security.md`
- `docs/deployment.md`
- `docs/api-reference.md`

---

## Features (Planned / In Progress)

### Core RAG
- Document upload (PDF/DOC/DOCX/TXT)
- Text extraction + Thai-aware chunking
- Embedding generation (default: `BAAI/bge-m3`)
- Vector indexing + similarity search (default: Qdrant)
- Context assembly + answer generation
- Streaming responses (SSE/WebSocket style)

### Workspace / Multi-tenant
- Projects (separate vector collections / metadata isolation)
- Per-project settings (top_k, chunk size, prompt templates)

### Chat
- Sessions
- Message history
- Context citations (store retrieved docs as `context_docs`)

### Admin & Ops
- Health endpoint
- Re-index / ingest operations
- Rate limiting (recommended)
- Audit logs (recommended)

### Security
- JWT authentication
- RBAC (admin/member/user)
- PII detection & masking (recommended)

---

## Tech Stack

### Backend
- **FastAPI** (Python)
- **Pydantic** schemas (`backend/app/models/schemas.py`)
- **SQLAlchemy** (implied by `database_url` usage; DB module exists)
- **TiDB Cloud** as relational DB (MySQL-compatible)
- **Qdrant** as vector database
- **sentence-transformers** for embeddings

### Frontend
- `frontend/` present (implementation details depend on current state)

### LLM Providers
Supported provider enum:
- OpenAI
- Anthropic
- Google
- Ollama (local)

---

## Repository Layout (current)

```
hr-rag/
  backend/
    app/
      core/
      models/
      services/
      main.py
  frontend/
  database/
  docs/
  PROJECT.md
```

> Note: `backend/app/api/*` router modules are referenced in `main.py` but not present in the current snapshot; API routes are therefore “intended contract” in `docs/api-reference.md`.

---

## Setup (Local Development)

### 1) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env
cp .env.example .env  # if you add it; otherwise create manually

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3) Qdrant

```bash
docker run -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant:latest
```

---

## Deployment Options

See `docs/deployment.md` for detailed patterns.

Quick summary:
- **Managed**: Vercel (frontend) + Render/Railway (backend) + Qdrant Cloud + TiDB Cloud
- **Self-hosted**: Docker Compose on VPS with reverse proxy (Caddy/Nginx)
- **Enterprise**: Kubernetes + managed DBs

---

## Thai Language RAG Best Practices (Short)

1. **Thai tokenization / sentence splitting** improves chunk boundaries.
2. Use **multilingual embeddings** proven to work on Thai (start with `bge-m3`).
3. Prefer **sentence-based chunking** + overlap.
4. Consider **hybrid retrieval** (semantic + keyword) for mixed Thai/English HR docs.
5. Evaluate retrieval with Thai test queries (precision/recall@k) and track regressions.

Details: `docs/thai-embedding-guide.md`

---

## Security Best Practices (Short)

- Restrict CORS origins in production.
- JWT secrets must be long random strings; rotate regularly.
- Enforce RBAC; HR docs are sensitive.
- Add rate limiting to chat + upload endpoints.
- Mask PII in logs and in LLM prompt context when possible.

Details: `docs/security.md`

---

## Next Implementation Milestones

1. Implement missing router modules under `backend/app/api/`:
   - `auth.py`, `projects.py`, `documents.py`, `chat.py`, `keys.py`
2. Wire DB models + migrations (Alembic)
3. Implement ingestion pipeline (extract → chunk → embed → upsert)
4. Add hybrid retrieval (optional)
5. Add tests (unit + integration)

