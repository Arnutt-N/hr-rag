"""Search router

Semantic search over ingested documents within a project.
Includes Redis caching for repeated queries.
"""

import html
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_active_member
from app.core.logging import get_logger
from app.models.schemas import SearchRequest, SearchResponse, SearchResult
from app.models.database import Project, get_db
from app.services.vector_store import get_vector_store
from app.services.cache import get_cache_service, CacheService

logger = get_logger(__name__)

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
    
    logger.info(
        "search_request",
        user_id=current_user.id,
        project_id=payload.project_id,
        query_len=len(safe_query),
        top_k=payload.top_k,
    )
    
    res = await db.execute(select(Project).where(Project.id == payload.project_id, Project.owner_id == current_user.id))
    project = res.scalar_one_or_none()
    if not project:
        logger.warning("search_project_not_found", user_id=current_user.id, project_id=payload.project_id)
        raise HTTPException(status_code=404, detail="Project not found")

    # Try cache first
    cache = get_cache_service()
    cache_key = CacheService.make_search_key(payload.project_id, safe_query, payload.top_k)
    cached_results = await cache.get(cache_key)
    
    if cached_results is not None:
        # Return cached results
        return SearchResponse(
            query=safe_query,
            results=[
                SearchResult(
                    text=r["text"],
                    score=float(r["score"]),
                    document_id=int(r.get("document_id") or 0),
                    filename=r.get("filename") or "",
                )
                for r in cached_results
            ],
            cached=True
        )

    # Cache miss - perform actual search
    vs = get_vector_store()
    results = await vs.search(project.id, safe_query, top_k=payload.top_k)

    # Cache the results (1 hour TTL)
    cache_results = [
        {
            "text": r["text"],
            "score": float(r["score"]),
            "document_id": int(r.get("document_id") or 0),
            "filename": r.get("filename") or "",
        }
        for r in results
    ]
    await cache.set(cache_key, cache_results)

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
        cached=False
    )
