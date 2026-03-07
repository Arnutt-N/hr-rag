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

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- TiDB Cloud account (or local TiDB for development)

### Setup Steps

1. **Clone and navigate to project:**
   ```bash
   cd /data/Organization/HR-Moj/app/hr-rag
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the setup script:**
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

4. **Or manually with Docker Compose:**
   ```bash
   # Start all services
   docker-compose up -d

   # View logs
   docker-compose logs -f

   # Stop services
   docker-compose down
   ```

### Access the Application

| Service | URL |
|---------|-----|
| Frontend (Next.js) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Qdrant Dashboard | http://localhost:6333/dashboard |
| TiDB (local dev) | http://localhost:4000 |

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

| Variable | Description | Default |
|----------|-------------|---------|
| `TIDB_HOST` | TiDB Cloud host | - |
| `TIDB_PORT` | TiDB port | 4000 |
| `TIDB_USER` | TiDB username | root |
| `TIDB_PASSWORD` | TiDB password | - |
| `TIDB_DATABASE` | Database name | hr_rag |
| `REDIS_URL` | Redis connection URL | redis://redis:6379/0 |
| `QDRANT_HOST` | Qdrant host | qdrant |
| `QDRANT_PORT` | Qdrant REST port | 6333 |
| `SECRET_KEY` | JWT secret key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_MODEL` | OpenAI model | gpt-4-turbo-preview |
| `EMBEDDING_MODEL` | Embedding model | text-embedding-3-small |

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

- Passwords are hashed using bcrypt
- JWT tokens with short expiration
- API key rate limiting
- CORS protection
- SQL injection prevention (parameterized queries)
- Input validation with Pydantic

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
