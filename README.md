# HR-RAG

HR-RAG is a comprehensive HR knowledge management system that combines document storage, vector search, knowledge graph, and AI-powered chat to help HR teams manage and query company policies, employee handbooks, and onboarding materials.

## ✨ Features

- 🤖 **AI-Powered Chat** - Chat with your HR documents using multiple LLM providers
- 🔍 **Advanced RAG** - Hybrid search (vector + keyword + graph) for accurate retrieval
- 🕸️ **Knowledge Graph** - Neo4j-powered entity and relationship extraction
- 📄 **Document Management** - Upload and manage PDF, DOC, DOCX, TXT files
- 🔐 **Multi-tenant** - Project-based organization with user authentication
- 🚀 **Production Ready** - Docker Compose setup with Nginx + SSL
- 🌐 **Multiple LLM Providers** - OpenAI, Anthropic, Google, Kimi, GLM, MiniMax, Qwen, DeepSeek, Ollama

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              HR-RAG Architecture                        │
└─────────────────────────────────────────────────────────────────────────┘

                                    ┌──────────────┐
                                    │   Browser    │
                                    │  (Client)    │
                                    └──────┬───────┘
                                           │ HTTPS
                                           ▼
                              ┌────────────────────────┐
                              │   Nginx (SSL/Reverse)  │
                              │      (Port 443)        │
                              └───────────┬────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼                     ▼                     ▼
          ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
          │   Next.js       │   │   FastAPI       │   │   Certbot       │
          │   Frontend      │   │   Backend       │   │   (SSL Renew)   │
          │   (Port 3000)   │   │   (Port 8000)   │   │                 │
          └─────────────────┘   └────────┬────────┘   └─────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
              ▼                          ▼                          ▼
    ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
    │    PostgreSQL   │      │     Qdrant      │      │     Neo4j       │
    │   (Relational)  │      │  (Vector DB)    │      │  (Graph DB)     │
    │   (Port 5432)   │      │  (Port 6333)    │      │ (Port 7474)     │
    └─────────────────┘      └─────────────────┘      └─────────────────┘
              │                                               │
              │         ┌─────────────────┐                   │
              │         │     Redis       │                   │
              └────────►│  (Cache/Queue)  │◄──────────────────┘
                        │   (Port 6379)   │
                        └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (v2.0+)
- Domain name (for SSL)
- VPS with at least 4GB RAM (8GB recommended)

### Production Deployment

1. **Clone repository:**
   ```bash
   git clone https://github.com/Arnutt-N/hr-rag.git
   cd hr-rag
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Set up SSL (replace with your domain):**
   ```bash
   # Update nginx.conf with your domain
   sed -i 's/YOUR_DOMAIN/yourdomain.com/g' nginx.conf
   
   # Run SSL setup
   ./setup-ssl.sh yourdomain.com
   ```

4. **Start all services:**
   ```bash
   docker-compose up -d
   ```

5. **Verify deployment:**
   ```bash
   # Check all services
   docker-compose ps
   
   # View logs
   docker-compose logs -f
   ```

### Development Setup

```bash
# Start without SSL
docker-compose -f docker-compose.yml up -d

# Access services
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| nginx | 80, 443 | Reverse proxy + SSL |
| frontend | 3000 | Next.js web app |
| backend | 8000 | FastAPI API server |
| postgres | 5432 | PostgreSQL database |
| qdrant | 6333 | Vector database |
| neo4j | 7474, 7687 | Graph database |
| redis | 6379 | Cache & sessions |
| certbot | - | SSL auto-renewal |

## 📚 API Documentation

Once running, access interactive API docs at:
- Swagger UI: `https://yourdomain.com/docs`
- ReDoc: `https://yourdomain.com/redoc`

### Authentication

```bash
# Register
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "your_password",
  "username": "username"
}

# Login
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "your_password"
}
```

### Projects

```bash
# List projects
GET /api/projects

# Create project
POST /api/projects
{
  "name": "Employee Handbook 2026",
  "description": "Company policies"
}
```

### Documents

```bash
# Upload document
POST /api/documents/{project_id}/upload
Content-Type: multipart/form-data
File: <document>

# Search documents
POST /api/documents/search
{
  "query": "vacation policy",
  "project_id": 1
}
```

### Chat

```bash
# Create session
POST /api/chat/sessions
{
  "title": "HR Questions",
  "project_id": 1
}

# Send message
POST /api/chat/sessions/{session_id}/messages
{
  "content": "What is the vacation policy?"
}

# WebSocket streaming
WS /api/chat/ws/{session_id}
```

## 🔧 Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `JWT_SECRET_KEY` | Generate: `openssl rand -hex 64` |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `NEO4J_PASSWORD` | Neo4j password |
| `OPENAI_API_KEY` | At least one LLM provider |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `POSTGRES_HOST` | postgres | PostgreSQL host |
| `POSTGRES_PORT` | 5432 | PostgreSQL port |
| `POSTGRES_DB` | hr_rag | Database name |

### Vector & Graph DB

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_HOST` | qdrant | Qdrant host |
| `QDRANT_PORT` | 6333 | Qdrant port |
| `NEO4J_URI` | bolt://neo4j:7687 | Neo4j connection |
| `NEO4J_USER` | neo4j | Neo4j username |

### LLM Providers (at least one)

| Variable | Provider |
|----------|----------|
| `OPENAI_API_KEY` | OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic Claude |
| `GOOGLE_API_KEY` | Google Gemini |
| `KIMI_API_KEY` | Moonshot AI |
| `GLM_API_KEY` | Zhipu AI |
| `MINIMAX_API_KEY` | MiniMax |
| `QWEN_API_KEY` | Alibaba Qwen |
| `DEEPSEEK_API_KEY` | DeepSeek |
| `OLLAMA_BASE_URL` | Local Ollama |

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_LLM_PROVIDER` | openai | Default LLM |
| `EMBEDDING_MODEL` | BAAI/bge-m3 | Embedding model |
| `MAX_FILE_SIZE` | 10MB | Max upload size |
| `CORS_ORIGINS` | - | Allowed origins |

## 🧠 Advanced RAG Features

### 1. Hybrid Search
Combines vector similarity + keyword matching (BM25)

### 2. Query Expansion
LLM expands queries for better retrieval

### 3. Re-ranking
Cross-encoder re-ranks results for relevance

### 4. Knowledge Graph
Neo4j extracts entities and relationships for graph-based retrieval

### 5. Multi-hop Reasoning
Traverses knowledge graph for complex queries

## 📁 Project Structure

```
hr-rag/
├── backend/
│   ├── app/
│   │   ├── api/              # API routes
│   │   ├── models/           # Database models
│   │   ├── services/         # Business logic
│   │   │   ├── advanced_retrieval.py
│   │   │   ├── graph_rag.py
│   │   │   ├── neo4j_graph.py
│   │   │   └── llm/
│   │   └── core/             # Config
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   └── app/              # Next.js app
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── nginx.conf                # Nginx config
├── setup-ssl.sh              # SSL setup script
└── README.md
```

## 🔐 Security

- **JWT Authentication** - Short-lived tokens with refresh
- **Password Hashing** - bcrypt with salt
- **Rate Limiting** - Per-user and per-API-key limits
- **CORS Protection** - Configurable allowed origins
- **SQL Injection Prevention** - Parameterized queries
- **Input Validation** - Pydantic models
- **Admin Panel** - Login attempt limiting, IP blocking

## 🔄 Database Migrations

```bash
# Create a new migration
cd backend
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Current migration version
alembic current
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# With coverage
pytest --cov=app
```

## 📊 Monitoring

```bash
# View logs
docker-compose logs -f [service]

# Check resource usage
docker stats

# Health checks
curl https://yourdomain.com/health
```

## 🔄 Backup & Restore

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U postgres hr_rag > backup.sql

# Restore PostgreSQL
docker-compose exec -T postgres psql -U postgres hr_rag < backup.sql

# Backup Qdrant
docker-compose exec qdrant tar czf /qdrant/backup.tar.gz /qdrant/storage
```

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 🆘 Support

- 📧 Issues: [GitHub Issues](https://github.com/Arnutt-N/hr-rag/issues)
- 📖 Docs: [API Documentation](https://yourdomain.com/docs)

---

Built with ❤️ using FastAPI, Next.js, PostgreSQL, Qdrant, and Neo4j
