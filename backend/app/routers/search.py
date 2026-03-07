"""Search router

Semantic search over ingested documents within a project.
"""

import html
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_active_member
from app.models.schemas import SearchRequest, SearchResponse, SearchResult
from app.models.database import Project, get_db
from app.services.vector_store import get_vector_store

router = APIRouter(prefix="/search", tags=["search"])


def sanitize_query(query: str) -> str:
    """
    Sanitize search query to prevent XSS and injection attacks.
    
    - Escape HTML entities
    - Limit length to 500 chars
    - Remove dangerous special characters
    """
    # Escape HTML to prevent XSS
    query = html.escape(query)
    # Limit length
    query = query[:500]
    # Remove dangerous characters: < > " ' \ 
    query = re.sub(r'[<>\"\'\\]', '', query)
    # Collapse multiple spaces
    query = re.sub(r'\s+', ' ', query).strip()
    return query


@router.post("", response_model=SearchResponse)
async def search(payload: SearchRequest, current_user=Depends(get_current_active_member), db: AsyncSession = Depends(get_db)):
    # Sanitize the search query before using it
    safe_query = sanitize_query(payload.query)
    
    res = await db.execute(select(Project).where(Project.id == payload.project_id, Project.owner_id == current_user.id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    vs = get_vector_store()
    results = await vs.search(project.id, safe_query, top_k=payload.top_k)

    return SearchResponse(
        query=safe_query,
        results=[
            SearchResult(
                text=r["text"],
                score=float(r["score"]),
                document_id=int(r.get("document_id") or 0),
                filename=r.get("filename") or "",
            )
            for r in results
        ],
    )
