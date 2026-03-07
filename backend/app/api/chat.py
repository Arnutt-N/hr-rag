from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()


class CreateSessionRequest(BaseModel):
    title: Optional[str] = "New Chat"


@router.get("/sessions")
async def list_sessions():
    return []


@router.post("/sessions")
async def create_session(payload: CreateSessionRequest):
    return {"id": 1, "title": payload.title, "created_at": datetime.utcnow().isoformat()}


@router.get("/sessions/{session_id}/messages")
async def list_messages(session_id: int):
    return []


class SendMessageRequest(BaseModel):
    content: str
    project_id: Optional[int] = None


@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: int, payload: SendMessageRequest):
    """Chat message scaffold.

    Wire to:
      - chat_messages table for history
      - Qdrant for retrieval
      - LLM provider for generation
    """
    return {
        "id": 1,
        "session_id": session_id,
        "role": "assistant",
        "content": f"(stub) You said: {payload.content}",
        "created_at": datetime.utcnow().isoformat(),
    }
