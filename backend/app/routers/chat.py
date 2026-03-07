"""Chat router

Endpoints:
- POST /chat : RAG chat, supports SSE streaming
- WS /chat/ws : WebSocket real-time chat (streams chunks)

Stores chat history in TiDB.
"""

from __future__ import annotations

import json
from typing import AsyncGenerator, Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_active_member
from app.models.schemas import ChatRequest, SearchRequest
from app.models.database import Project, ChatSession, ChatMessage, get_db
from app.services.vector_store import get_vector_store
from app.services.llm_providers import get_llm_service

router = APIRouter(prefix="/chat", tags=["chat"])


async def _get_or_create_session(
    db: AsyncSession,
    user_id: int,
    project_id: int,
    session_id: Optional[int],
) -> ChatSession:
    if session_id:
        res = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id, ChatSession.project_id == project_id)
        )
        session = res.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return session

    session = ChatSession(user_id=user_id, project_id=project_id, title="New Chat")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.post("", response_class=StreamingResponse)
async def chat(
    payload: ChatRequest,
    current_user=Depends(get_current_active_member),
    db: AsyncSession = Depends(get_db),
):
    # validate project ownership
    res = await db.execute(select(Project).where(Project.id == payload.project_id, Project.owner_id == current_user.id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    session = await _get_or_create_session(db, current_user.id, project.id, payload.session_id)

    # store user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=payload.message)
    db.add(user_msg)
    await db.commit()

    # retrieve context
    vs = get_vector_store()
    context_docs = await vs.search(project.id, payload.message, top_k=5)

    llm = get_llm_service()
    provider = payload.llm_provider or current_user.preferred_llm_provider
    prompt = llm.build_rag_prompt(payload.message, context_docs)

    async def sse_gen() -> AsyncGenerator[str, None]:
        collected = []
        async for chunk in llm.generate_response(prompt, provider=provider, stream=True):
            collected.append(chunk)
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        full = "".join(collected)
        # save assistant message
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=full,
            context_docs=context_docs,
            llm_provider=provider.value if hasattr(provider, 'value') else str(provider),
            llm_model=llm.get_default_model(provider),
        )
        db.add(assistant_msg)
        await db.commit()
        yield f"data: {json.dumps({'done': True, 'session_id': session.id})}\n\n"

    if payload.stream:
        return StreamingResponse(sse_gen(), media_type="text/event-stream")

    # non-stream: collect once
    collected = []
    async for chunk in llm.generate_response(prompt, provider=provider, stream=False):
        collected.append(chunk)
    full = "".join(collected)
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=full,
        context_docs=context_docs,
        llm_provider=provider.value if hasattr(provider, 'value') else str(provider),
        llm_model=llm.get_default_model(provider),
    )
    db.add(assistant_msg)
    await db.commit()

    return StreamingResponse(
        iter([json.dumps({"session_id": session.id, "message": full, "context_docs": context_docs})]),
        media_type="application/json",
    )


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket):
    # Auth via query param token to keep it simple for WS (can be upgraded to headers/cookies)
    # ws://.../chat/ws?token=...
    from app.core.security import decode_token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return

    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        await websocket.close(code=4401)
        return

    await websocket.accept()

    # Create a DB session manually in WS
    from app.models.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            while True:
                raw = await websocket.receive_text()
                msg = json.loads(raw)
                message = msg.get("message", "")
                project_id = int(msg.get("project_id"))
                session_id = msg.get("session_id")
                provider = msg.get("llm_provider")

                # validate project ownership
                res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user_id))
                project = res.scalar_one_or_none()
                if not project:
                    await websocket.send_text(json.dumps({"type": "error", "detail": "Project not found"}))
                    continue

                session = await _get_or_create_session(db, user_id, project_id, int(session_id) if session_id else None)

                # store user message
                db.add(ChatMessage(session_id=session.id, role="user", content=message))
                await db.commit()

                # retrieve context
                vs = get_vector_store()
                context_docs = await vs.search(project_id, message, top_k=5)

                llm = get_llm_service()
                from app.models.schemas import LLMProvider as LLMProviderEnum
                prov_enum = LLMProviderEnum(provider) if provider else llm.default_provider
                prompt = llm.build_rag_prompt(message, context_docs)

                collected = []
                async for chunk in llm.generate_response(prompt, provider=prov_enum, stream=True):
                    collected.append(chunk)
                    await websocket.send_text(json.dumps({"type": "chunk", "content": chunk, "session_id": session.id}))

                full = "".join(collected)
                db.add(
                    ChatMessage(
                        session_id=session.id,
                        role="assistant",
                        content=full,
                        context_docs=context_docs,
                        llm_provider=prov_enum.value,
                        llm_model=llm.get_default_model(prov_enum),
                    )
                )
                await db.commit()
                await websocket.send_text(json.dumps({"type": "done", "session_id": session.id}))

        except WebSocketDisconnect:
            return
        except Exception as e:
            try:
                await websocket.send_text(json.dumps({"type": "error", "detail": str(e)}))
            finally:
                await websocket.close(code=1011)
                return
