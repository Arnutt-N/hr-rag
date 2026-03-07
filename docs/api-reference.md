# API Reference (HR-RAG)

## Base URL

- Local: `http://localhost:8000`
- API prefix (backend): endpoints are mounted under:
  - `/api/auth`
  - `/api/projects`
  - `/api/documents`
  - `/api/chat`
  - `/api/keys`

The backend also exposes:
- `GET /` (service info)
- `GET /health` (health check)

> Note: In the current repository snapshot, router modules (`app/api/auth.py`, etc.) are not present yet, but the schemas exist in `backend/app/models/schemas.py`. This document specifies the **intended/expected** contract based on those schemas.

---

## Authentication

### Register
**POST** `/api/auth/register`

Request body: `UserCreate`
```json
{
  "email": "user@example.com",
  "username": "top",
  "password": "secret123",
  "full_name": "Top N"
}
```

Response: `UserResponse`

### Login
**POST** `/api/auth/login`

Request body: `UserLogin`
```json
{
  "username": "top",
  "password": "secret123"
}
```

Response: `Token`
```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

### Get current user
**GET** `/api/auth/me`

Headers:
- `Authorization: Bearer <access_token>`

Response: `UserResponse`

---

## Projects

### Create project
**POST** `/api/projects`

Request body: `ProjectCreate`
```json
{
  "name": "HR Policies",
  "description": "Company HR docs",
  "is_public": false,
  "settings": {}
}
```

Response: `ProjectResponse`

### List projects
**GET** `/api/projects`

Response: `List[ProjectResponse]`

### Get project
**GET** `/api/projects/{project_id}`

Response: `ProjectResponse`

### Update project
**PATCH** `/api/projects/{project_id}`

Request body: `ProjectUpdate`

Response: `ProjectResponse`

### Delete project
**DELETE** `/api/projects/{project_id}`

Response:
```json
{ "status": "success" }
```

---

## Documents

### Upload document
**POST** `/api/documents/upload`

`multipart/form-data`:
- `file`: (pdf/doc/docx/txt)
- `project_id`: integer

Response: `DocumentResponse`

### List documents
**GET** `/api/documents?project_id={project_id}`

Response: `List[DocumentResponse]`

### Get document
**GET** `/api/documents/{document_id}`

Response: `DocumentResponse`

### Delete document
**DELETE** `/api/documents/{document_id}`

Response:
```json
{ "status": "success" }
```

### Ingest (index) document into vector DB
**POST** `/api/documents/{document_id}/ingest`

Response: `IngestResponse`
```json
{
  "document_id": 123,
  "status": "success",
  "chunk_count": 87,
  "message": "Indexed successfully"
}
```

---

## Chat

### Create chat session
**POST** `/api/chat/sessions`

Request body: `ChatSessionCreate`
```json
{
  "project_id": 1,
  "title": "New Chat"
}
```

Response: `ChatSessionResponse`

### List sessions
**GET** `/api/chat/sessions?project_id={project_id}`

Response: `List[ChatSessionResponse]`

### Send chat message (RAG)
**POST** `/api/chat`

Request body: `ChatRequest`
```json
{
  "message": "นโยบายลาป่วยคืออะไร",
  "project_id": 1,
  "session_id": 10,
  "llm_provider": "openai",
  "stream": true
}
```

Response (non-stream): `ChatResponse`
```json
{
  "session_id": 10,
  "message": "...",
  "context_docs": [],
  "llm_provider": "openai",
  "llm_model": "gpt-4o-mini"
}
```

Streaming:
- If `stream=true`, response is typically `text/event-stream` (SSE) or chunked streaming.

### Add message to session
**POST** `/api/chat/messages`

Request body: `ChatMessageCreate`
```json
{
  "content": "...",
  "session_id": 10
}
```

Response: `ChatMessageResponse`

### List messages
**GET** `/api/chat/sessions/{session_id}/messages`

Response: `List[ChatMessageResponse]`

---

## API Keys

### Create API key
**POST** `/api/keys`

Request body:
```json
{
  "name": "integration-hr-portal"
}
```

Response:
```json
{
  "key": "sk_...",
  "name": "integration-hr-portal"
}
```

### List API keys
**GET** `/api/keys`

Response:
```json
[
  {
    "id": 1,
    "name": "integration-hr-portal",
    "created_at": "2026-03-07T10:00:00Z",
    "last_used": null
  }
]
```

### Revoke API key
**DELETE** `/api/keys/{key_id}`

Response:
```json
{ "status": "revoked" }
```

---

## Error Format (Recommended)

Use FastAPI default:

```json
{
  "detail": "Error message"
}
```

For validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "field"],
      "msg": "...",
      "type": "..."
    }
  ]
}
```

---

## Enums

### UserRole
- `admin`
- `member`
- `user`

### LLMProvider
- `openai`
- `anthropic`
- `google`
- `ollama`

