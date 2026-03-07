# HR-RAG System Architecture

## Overview

The HR-RAG system is a Retrieval-Augmented Generation (RAG) application designed specifically for Thai language HR documents. It provides intelligent question-answering capabilities over HR policies, employee handbooks, and organizational documentation.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Web Browser (React/Next.js)                  │   │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │   │
│  │   │  Chat UI │  │Document  │  │  Admin   │  │ Analytics│        │   │
│  │   │          │  │  Viewer  │  │  Panel   │  │  Dashboard│       │   │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS/WSS
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY LAYER                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      FastAPI Server                             │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                │   │
│  │  │   Auth     │  │   Rate     │  │   CORS     │                │   │
│  │  │ Middleware │  │  Limiter   │  │ Middleware │                │   │
│  │  └────────────┘  └────────────┘  └────────────┘                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  CHAT SERVICE    │   │  INGEST SERVICE  │   │  ADMIN SERVICE   │
│                  │   │                  │   │                  │
│ • Query handling │   │ • Document       │   │ • User management│
│ • Context        │   │   processing     │   │ • Analytics      │
│   retrieval      │   │ • Embedding      │   │ • System config  │
│ • LLM streaming  │   │   generation    │   │ • Monitoring     │
└────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        CORE SERVICES LAYER                              │
│                                                                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │    Embedding   │  │  Vector Store  │  │   LLM Service │            │
│  │    Service     │  │   (Qdrant)     │  │  (OpenAI/Ollama)│           │
│  │                │  │                │  │                │            │
│  │ • Thai tokenize│  │ • Similarity  │  │ • Thai prompt  │            │
│  │ • BGE-M3 model │  │   search       │  │ • Streaming    │            │
│  │ • Batch encode │  │ • HNSW index   │  │ • Context fill │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                      │
│                                                                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │   PostgreSQL   │  │    Qdrant      │  │     Redis      │            │
│  │  (Metadata)   │  │   (Vectors)    │  │    (Cache)     │            │
│  │                │  │                │  │                │            │
│  │ • Users        │  │ • Doc embeddings│ │ • Sessions    │            │
│  │ • Documents    │  │ • Chunk store  │  │ • Embeddings   │            │
│  │ • Chat history │  │ • Fast search   │  │ • Rate limits  │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Client Layer (Frontend)

**Technology:** Next.js 14+ with TypeScript

**Components:**
- **Chat Interface** - Real-time chat with streaming responses
- **Document Viewer** - PDF/DOC viewer for HR documents
- **Admin Panel** - Document management, user administration
- **Analytics Dashboard** - Usage statistics, query analytics

### 2. API Gateway Layer

**Technology:** FastAPI (Python)

**Features:**
- RESTful API endpoints
- WebSocket support for streaming
- JWT authentication
- Rate limiting (Redis-backed)
- Request validation (Pydantic)
- CORS configuration

### 3. Core Services Layer

#### Embedding Service
- **Model:** `BAAI/bge-m3` (multilingual, Thai-optimized)
- **Processing:** Batch encoding with caching
- **Dimension:** 1024

#### Vector Store
- **Database:** Qdrant (self-hosted or cloud)
- **Index Type:** HNSW
- **Metric:** Cosine similarity
- **Top-K:** Configurable (default: 5)

#### LLM Service
- **Primary:** OpenAI GPT-4o-mini
- **Fallback:** Ollama (local Llama3.2)
- **Streaming:** Server-Sent Events (SSE)
- **Thai Optimization:** Specialized prompts

### 4. Data Layer

| Database | Purpose | Free Tier |
|----------|---------|-----------|
| PostgreSQL | Metadata, users, chat history | Neon (500MB) |
| Qdrant | Vector storage, similarity search | Qdrant Cloud (1GB) |
| Redis | Caching, rate limiting | Upstash (10K commands) |

## Data Flow

### Query Flow (Chat)
```
User Query → FastAPI → Embedding Service → Qdrant (Search)
                                        ↓
                              Retrieved Context
                                        ↓
                            LLM Service (with context)
                                        ↓
                              Stream Response → User
```

### Document Ingestion Flow
```
Upload File → FastAPI → Document Parser → Text Extraction
                                                ↓
                                    Thai Tokenizer (PyThaiNLP)
                                                ↓
                                        Chunk Generator
                                                ↓
                                    Embedding Service
                                                ↓
                                    Qdrant (Store)
                                                ↓
                              PostgreSQL (Metadata)
```

## API Endpoints

### Chat API
- `POST /api/v1/chat` - Send message, receive streaming response
- `GET /api/v1/chat/history` - Get conversation history
- `DELETE /api/v1/chat/history` - Clear chat history

### Document API
- `POST /api/v1/documents` - Upload document
- `GET /api/v1/documents` - List documents
- `GET /api/v1/documents/{id}` - Get document details
- `DELETE /api/v1/documents/{id}` - Delete document

### Admin API
- `GET /api/v1/admin/analytics` - Usage statistics
- `POST /api/v1/admin/reindex` - Rebuild vector index
- `GET /api/v1/admin/health` - System health check

## Security Architecture

```
┌─────────────────────────────────────────┐
│          SECURITY LAYERS               │
├─────────────────────────────────────────┤
│ 1. Network Level                       │
│    • HTTPS/TLS encryption              │
│    • Firewall rules                    │
│    • VPN for admin access              │
├─────────────────────────────────────────┤
│ 2. Application Level                   │
│    • JWT authentication                │
│    • Role-based access control (RBAC) │
│    • Input validation                  │
├─────────────────────────────────────────┤
│ 3. Data Level                          │
│    • API key rotation                  │
│    • Data encryption at rest          │
│    • PII masking                       │
└─────────────────────────────────────────┘
```

## Deployment Options

### Development (Local)
```
Docker Compose
├── frontend (Next.js)
├── backend (FastAPI)
├── qdrant (Vector DB)
├── postgres (Metadata)
└── redis (Cache)
```

### Production (Cloud)
```
Vercel (Frontend) + Railway/Render (Backend) + Qdrant Cloud
```

### Enterprise (Self-hosted)
```
Kubernetes Cluster
├── Multiple FastAPI replicas
├── Qdrant cluster
├── PostgreSQL HA
└── Redis Cluster
```

## Scaling Considerations

| Component | Scaling Strategy |
|-----------|-----------------|
| FastAPI | Horizontal (multiple replicas) |
| Embedding Service | GPU instances, batch queuing |
| Qdrant | Sharding, replication |
| LLM | Load balancing, caching |

---

*Generated for HR-RAG Project*
