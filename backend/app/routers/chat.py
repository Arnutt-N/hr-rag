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
from app.core.logging import get_logger
from app.models.schemas import ChatRequest, SearchRequest
from app.models.database import Project, ChatSession, ChatMessage, get_db
from app.services.vector_store import get_vector_store
from app.services.llm_providers import get_llm_service

logger = get_logger(__name__)

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
    logger.info(
        "chat_request",
        user_id=current_user.id,
        project_id=payload.project_id,
        session_id=payload.session_id,
        stream=payload.stream,
        provider=str(payload.llm_provider or current_user.preferred_llm_provider),
    )
    
    # validate project ownership
    res = await db.execute(select(Project).where(Project.id == payload.project_id, Project.owner_id == current_user.id))
    project = res.scalar_one_or_none()
    if not project:
        logger.warning("chat_project_not_found", user_id=current_user.id, project_id=payload.project_id)
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
        # Open a fresh DB session — the route-handler session closes when the
        # Response object is returned, before the generator finishes streaming.
        from app.models.database import AsyncSessionLocal
        async with AsyncSessionLocal() as gen_db:
            collected = []
            try:
                async for chunk in llm.generate_response(prompt, provider=provider, stream=True):
                    collected.append(chunk)
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
            except Exception as e:
                logger.error("sse_generation_error", session_id=session.id, error=str(e))
                yield f"event: error\ndata: {json.dumps({'error': 'Generation failed'})}\n\n"
                return
            full = "".join(collected)
            assistant_msg = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=full,
                context_docs=context_docs,
                llm_provider=provider.value if hasattr(provider, 'value') else str(provider),
                llm_model=llm.get_default_model(provider),
            )
            gen_db.add(assistant_msg)
            await gen_db.commit()
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
    # Auth via the first WebSocket message (avoids token appearing in URL /
    # server access logs / browser history which query-param auth causes).
    # Client must send: {"type": "auth", "token": "<jwt>"}
    import asyncio
    from app.core.security import decode_token

    await websocket.accept()

    try:
        raw_auth = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        auth_data = json.loads(raw_auth)
        token = auth_data.get("token")
        if not token:
            logger.warning("ws_chat_auth_failed", reason="missing_token")
            await websocket.close(code=4401)
            return
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except Exception as e:
        logger.warning("ws_chat_auth_failed", error=str(e))
        await websocket.close(code=4401)
        return

    logger.info("ws_chat_connected", user_id=user_id)

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

                logger.info("ws_chat_message", user_id=user_id, project_id=project_id, message_len=len(message))

                # validate project ownership
                res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user_id))
                project = res.scalar_one_or_none()
                if not project:
                    logger.warning("ws_chat_project_not_found", user_id=user_id, project_id=project_id)
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
            logger.error("ws_chat_internal_error", user_id=user_id, error=str(e))
            try:
                await websocket.send_text(json.dumps({"type": "error", "detail": "An internal error occurred"}))
            finally:
                await websocket.close(code=1011)
                return
