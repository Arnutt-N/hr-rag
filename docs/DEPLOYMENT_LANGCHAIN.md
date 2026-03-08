# HR-RAG Deployment Guide

## LangChain + LangGraph + FastMCP Integration

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Using uv (Recommended - 10-100x faster)
curl -LsSf https://astral.sh/uv/install.sh | sh
cd backend
uv pip install -e .

# Or using pip
pip install -e .
```

### 2. Environment Variables

Create `.env` file:

```env
# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
KIMI_API_KEY=...

# Database
DATABASE_URL=mysql+aiomysql://user:pass@host:3306/db

# Vector Store
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Redis
REDIS_URL=redis://localhost:6379
```

### 3. Run Services

```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Start Redis
docker run -p 6379:6379 redis:alpine

# Start API
uvicorn app.main:app --reload

# Start MCP Server (optional)
python -m app.mcp.server
```

---

## 📦 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HR-RAG Architecture                       │
└─────────────────────────────────────────────────────────────┘

Frontend (Next.js)
        │
        ▼
FastAPI Backend
        │
        ├──► LangGraph Chat Workflow
        │         │
        │         ├──► LangChain RAG Chain
        │         │         ├──► Document Loaders
        │         │         ├──► Text Splitters
        │         │         └──► Vector Store (Qdrant)
        │         │
        │         ├──► LLM Models (OpenAI, Anthropic, Kimi)
        │         │
        │         └──► Memory (Redis)
        │
        ├──► FastMCP Server (Tools)
        │         ├──► search_knowledge_base
        │         ├──► answer_question
        │         ├──► chat
        │         └──► index_document
        │
        ├──► TiDB Cloud (SQL)
        │
        └──► Redis (Cache + State)
```

---

## 🔧 Services

### LangChain Services

| Service | File | Description |
|---------|------|-------------|
| LLM Service | `services/llm/langchain_service.py` | Multi-provider LLM |
| Document Loaders | `services/document_loaders.py` | PDF/DOCX/TXT loading |
| Text Splitters | `services/text_splitters.py` | Chunking strategies |
| Vector Store | `services/vector_store_langchain.py` | Qdrant integration |
| RAG Chain | `services/rag_chain.py` | RAG pipeline |

### LangGraph Services

| Service | File | Description |
|---------|------|-------------|
| Chat State | `services/chat_state.py` | State definition |
| Chat Nodes | `services/chat_nodes.py` | Node functions |
| Chat Graph | `services/chat_graph.py` | Workflow graph |

### FastMCP Server

| Tool | Description |
|------|-------------|
| `search_knowledge_base` | Search HR documents |
| `answer_question` | RAG-based Q&A |
| `chat` | Full chat workflow |
| `list_categories` | List document categories |
| `index_document` | Index new document |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test
pytest tests/test_chat_graph.py -v
```

---

## 📊 Chat Workflow

```
User Message
    │
    ▼
┌─────────────────┐
│  Load Memory    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Classify Intent │
└────────┬────────┘
         │
    ┌────┴────┬─────────┬──────────┐
    ▼         ▼         ▼          ▼
┌───────┐ ┌───────┐ ┌─────────┐ ┌────────┐
│Greet- │ │Chat-  │ │Complaint│ │Retrieve│
│ing    │ │chit   │ │         │ │  Docs  │
└───┬───┘ └───┬───┘ └────┬────┘ └───┬────┘
    │         │          │          │
    │         │          │          ▼
    │         │          │    ┌──────────┐
    │         │          │    │ Generate │
    │         │          │    │  Answer  │
    │         │          │    └────┬─────┘
    │         │          │         │
    │         │          │         ▼
    │         │          │    ┌──────────┐
    │         │          │    │ Evaluate │
    │         │          │    │ Quality  │
    │         │          │    └────┬─────┘
    │         │          │         │
    └─────────┴──────────┴─────────┤
                                  │
                                  ▼
                          ┌───────────────┐
                          │ Save Memory   │
                          └───────┬───────┘
                                  │
                                  ▼
                               Response
```

---

## 🔐 Security

- JWT authentication
- API rate limiting
- Input validation
- SQL injection protection
- XSS protection

---

## 📝 API Endpoints

### Chat

```http
POST /api/v1/chat
Content-Type: application/json

{
  "message": "นโยบายการลางานเป็นอย่างไร?",
  "user_id": 1,
  "session_id": "session-123"
}
```

### Search

```http
POST /api/v1/search
Content-Type: application/json

{
  "query": "สวัสดิการ",
  "category": "benefit",
  "limit": 5
}
```

---

## 🐳 Docker

```bash
# Build
docker build -t hr-rag:latest .

# Run
docker run -p 8000:8000 hr-rag:latest

# Docker Compose
docker-compose up -d
```

---

## 📈 Monitoring

- Health check: `GET /health`
- Metrics: `GET /metrics`
- Logs: Structured JSON logs

---

## 🔄 Migration from Old System

1. Export existing documents
2. Re-index with new document loaders
3. Update API clients to use new endpoints
4. Monitor performance

---

*Last Updated: 2026-03-08*
