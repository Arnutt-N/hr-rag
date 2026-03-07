# HR-RAG

HR-RAG is a comprehensive HR knowledge management system that combines document storage, vector search, and AI-powered chat to help HR teams manage and query company policies, employee handbooks, and onboarding materials.

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              HR-RAG Architecture                        │
└─────────────────────────────────────────────────────────────────────────┘

                                    ┌──────────────┐
                                    │   Browser    │
                                    │  (Client)    │
                                    └──────┬───────┘
                                           │ HTTP/WebSocket
                                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              Load Balancer / CORS                       │
└─────────────────────────────────────────────────────────────────────────┘
                                           │
                    ┌────────────────────────┼────────────────────────┐
                    ▼                                                ▼
          ┌─────────────────┐                              ┌─────────────────┐
          │   Next.js       │                              │   FastAPI       │
          │   Frontend      │◄─────────────────────────────│   Backend       │
          │   (Port 3000)   │        REST API + WS         │   (Port 8000)   │
          └─────────────────┘                              └────────┬────────┘
                                                                     │
                              ┌──────────────────────────────────────┼──────────┐
                              │                                      │          │
                              ▼                                      ▼          ▼
                    ┌─────────────────┐                  ┌─────────────┐ ┌────────┐
                    │      Redis      │                  │   Qdrant    │ │  TiDB  │
                    │  (Cache/Session)│                  │  (Vectors)  │ │ Cloud  │
                    │   (Port 6379)   │                  │ (Port 6333) │ │        │
                    └─────────────────┘                  └─────────────┘ └────────┘
                                                                        │
                                                             ┌──────────┴──────────┐
                                                             │                     │
                                                     ┌───────┴───────┐    ┌───────┴───────┐
                                                     │    Tables:    │    │   Tables:     │
                                                     │  - users      │    │ - users       │
                                                     │  - sessions   │    │ - chat_sessions│
                                                     │  - messages   │    │ - chat_messages│
                                                     └───────────────┘    │ - projects     │
                                                                         │ - project_docs │
                                                                         │ - vector_meta  │
                                                                         │ - api_keys     │
                                                                         └────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                              Data Flow                                   │
└─────────────────────────────────────────────────────────────────────────┘

  1. Document Upload:
     Frontend → FastAPI → TiDB (metadata) + Qdrant (vectors)

  2. Chat Interaction:
     Frontend → FastAPI → Redis (session) → TiDB (history)
                                     ↓
                              Qdrant (semantic search)
                                     ↓
                              LLM (OpenAI GPT)
                                     ↓
                              Response → Frontend

  3. Project Management:
     Frontend → FastAPI → TiDB (projects & documents)

```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (v2.0+)
- Python 3.11+
- Node.js 18+
- TiDB Cloud account (or local TiDB for development)

### Development Setup

1. **Clone and navigate to project:**
   ```bash
   cd /data/Organization/HR-Moj/app/hr-rag
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services:**
   ```bash
   docker-compose up -d
   ```

4. **Wait for services to be ready (first run):**
   ```bash
   # Check service health
   docker-compose ps
   
   # View logs
   docker-compose logs -f
   ```

5. **Verify services:**
   ```bash
   # Backend health check
   curl http://localhost:8000/health
   
   # Frontend
   curl http://localhost:3000
   ```

### Access the Application

| Service | URL |
|---------|-----|
| Frontend (Next.js) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Qdrant Dashboard | http://localhost:6333/dashboard |
| TiDB (local dev) | http://localhost:4000 |

### Development Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart a service
docker-compose restart backend

# Rebuild after code changes
docker-compose build backend
docker-compose up -d backend

# Stop all services
docker-compose down

# Stop and remove volumes (clean start)
docker-compose down -v
```

### Running Without Docker

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="mysql+pymysql://root:@localhost:4000/hr_rag"
export REDIS_URL="redis://localhost:6379/0"
export QDRANT_HOST="localhost"
export SECRET_KEY="your-secret-key"

uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📚 API Documentation

### Authentication

```bash
# Register new user
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "your_password"
}

# Login
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "your_password"
}

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Projects

```bash
# List projects
GET /api/projects
Authorization: Bearer <token>

# Create project
POST /api/projects
{
  "name": "Employee Handbook 2026",
  "description": "Company policies and guidelines"
}

# Get project
GET /api/projects/{project_id}

# Delete project
DELETE /api/projects/{project_id}
```

### Documents

```bash
# Upload document
POST /api/documents/{project_id}/upload
Content-Type: multipart/form-data
File: <document>

# List documents
GET /api/documents/{project_id}

# Delete document
DELETE /api/documents/{document_id}

# Search documents (vector search)
POST /api/documents/search
{
  "query": "vacation policy",
  "project_id": 1,
  "limit": 5
}
```

### Chat Sessions

```bash
# List chat sessions
GET /api/chat/sessions

# Create chat session
POST /api/chat/sessions
{
  "title": "HR Questions",
  "project_id": 1
}

# Get chat history
GET /api/chat/sessions/{session_id}/messages

# Send message
POST /api/chat/sessions/{session_id}/messages
{
  "content": "What is the vacation policy?",
  "project_id": 1
}

# WebSocket for streaming responses
WS /api/chat/ws/{session_id}
```

### API Keys

```bash
# List API keys
GET /api/keys

# Create API key
POST /api/keys
{
  "name": "My API Key",
  "rate_limit": 1000
}

# Delete API key
DELETE /api/keys/{key_id}
```

## 🔧 Environment Variables

### Database (TiDB)
| Variable | Description | Required |
|----------|-------------|----------|
| `TIDB_HOST` | TiDB Cloud host | Yes (production) |
| `TIDB_PORT` | TiDB port | 4000 |
| `TIDB_USER` | TiDB username | Yes |
| `TIDB_PASSWORD` | TiDB password | Yes |
| `TIDB_DATABASE` | Database name | hr_rag |
| `DATABASE_URL` | Full database URL | Auto-generated |

### Redis (Cache/Session)
| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL | redis://redis:6379/0 |
| `REDIS_PASSWORD` | Redis password | - |

### Qdrant (Vector Database)
| Variable | Description | Default |
|----------|-------------|---------|
| `QDRANT_HOST` | Qdrant host | qdrant |
| `QDRANT_PORT` | Qdrant REST port | 6333 |
| `QDRANT_GRPC_PORT` | Qdrant gRPC port | 6334 |
| `QDRANT_API_KEY` | Qdrant API key (optional) | - |

### Authentication / JWT
| Variable | Description | Required |
|----------|-------------|----------|
| `JWT_SECRET_KEY` | JWT signing key | **Yes** - generate with `openssl rand -hex 64` |
| `JWT_ALGORITHM` | JWT algorithm | HS256 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | 1440 (24h) |

### CORS
| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Allowed origins (comma-separated) | http://localhost:3000,http://127.0.0.1:3000 |

### LLM Providers (at least one required)
| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key |
| `GOOGLE_API_KEY` | Google Gemini API key |
| `KIMI_API_KEY` | Moonshot AI (Kimi) API key |
| `GLM_API_KEY` | Zhipu AI API key |
| `MINIMAX_API_KEY` | MiniMax API key |
| `QWEN_API_KEY` | Alibaba Qwen API key |
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `DEFAULT_LLM_PROVIDER` | Primary provider | openai |

### Embedding Model
| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_MODEL` | Chat model | gpt-4-turbo-preview |
| `EMBEDDING_MODEL` | Embedding model | text-embedding-3-small |
| `EMBEDDING_DIMENSION` | Vector dimension | 1536 |

### Application Settings
| Variable | Description | Default |
|----------|-------------|---------|
| `NODE_ENV` | Environment | development |
| `LOG_LEVEL` | Logging level | INFO |

### Rate Limiting
| Variable | Description | Default |
|----------|-------------|---------|
| `RATE_LIMIT_PER_MINUTE` | Requests per minute | 60 |
| `RATE_LIMIT_PER_DAY` | Requests per day | 1000 |

### File Storage
| Variable | Description | Default |
|----------|-------------|---------|
| `UPLOAD_DIR` | Upload directory | /app/uploads |
| `MAX_FILE_SIZE_MB` | Max file size (MB) | 10 |
| `ALLOWED_EXTENSIONS` | Allowed file types | pdf,txt,md,doc,docx |

### Vector Search
| Variable | Description | Default |
|----------|-------------|---------|
| `VECTOR_COLLECTION_NAME` | Collection name | hr_documents |
| `CHUNK_SIZE` | Text chunk size | 500 |
| `CHUNK_OVERLAP` | Chunk overlap | 50 |

### Admin Panel
| Variable | Description | Default |
|----------|-------------|---------|
| `ADMIN_SESSION_TIMEOUT` | Session timeout (seconds) | 86400 (24h) |
| `ADMIN_MAX_LOGIN_ATTEMPTS` | Max failed attempts | 5 |
| `ADMIN_IP_BLOCK_DURATION` | IP block duration (seconds) | 3600 (1h) |
| `ADMIN_LOG_RETENTION_DAYS` | Log retention (days) | 90 |

## 📁 Project Structure

```
hr-rag/
├── database/
│   ├── schema.sql          # TiDB schema
│   ├── migrations/         # Database migrations
│   │   └── 001_initial_schema.sql
│   └── seed.sql           # Sample data
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI app
│   │   ├── api/            # API routes
│   │   ├── models/         # Pydantic models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js app router
│   │   ├── components/    # React components
│   │   └── lib/            # Utilities
│   ├── package.json
│   └── Dockerfile
├── scripts/
│   └── setup.sh            # Setup script
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🔐 Security

### Authentication & Authorization
- **Password Hashing**: bcrypt with salt (cost factor 12)
- **JWT Tokens**: Short-lived access tokens (24h) + refresh tokens (7 days)
- **API Key Authentication**: Support for programmatic access with rate limits
- **Session Management**: Redis-backed sessions with configurable timeout

### API Security
- **Rate Limiting**: Configurable per-minute and per-day limits
- **CORS Protection**: Configurable allowed origins
- **Input Validation**: Pydantic models for all requests
- **SQL Injection Prevention**: Parameterized queries via SQLAlchemy
- **Request Size Limits**: Max file upload size enforced

### Admin Panel Security
- **Login Attempt Limiting**: Max 5 failed attempts before IP block
- **IP Blocking**: Automatic temporary IP blocks on suspicious activity
- **Session Timeout**: Configurable session expiration (default: 24h)
- **Audit Logging**: System logs retained for 90 days

### Data Protection
- **Vector Collections**: Project-based isolation for multi-tenancy
- **API Key Management**: Create/revoke keys with rate limit controls
- **Environment-based Secrets**: No hardcoded credentials

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📝 License

MIT License
