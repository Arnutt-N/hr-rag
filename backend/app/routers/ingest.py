"""Ingest router

File upload endpoint for PDF/DOC/DOCX/TXT and indexing into vector DB.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_active_member
from app.models.schemas import IngestResponse, DocumentResponse
from app.models.database import Project, Document, get_db
from app.services.file_processor import extract_text, chunk_text
from app.services.vector_store import get_vector_store

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/{project_id}", response_model=IngestResponse)
async def ingest_file(
    project_id: int,
    file: UploadFile = File(...),
    current_user=Depends(get_current_active_member),
    db: AsyncSession = Depends(get_db),
):
    # ensure project ownership
    res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    text, meta = await extract_text(file)
    if not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text")

    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="No chunks produced")

    # create document record
    doc = Document(
        filename=file.filename or "uploaded",
        original_filename=file.filename or "uploaded",
        file_type=(file.filename or "").split(".")[-1].lower(),
        content=text,
        file_size=len(text.encode("utf-8")),
        page_count=meta.get("page_count"),
        project_id=project.id,
        is_indexed=False,
        chunk_count=len(chunks),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # upsert into vector store
    vs = get_vector_store()
    metadatas = [
        {
            "document_id": doc.id,
            "filename": doc.original_filename,
            "project_id": project.id,
        }
        for _ in chunks
    ]
    vector_ids = await vs.upsert_documents(project.id, chunks, metadatas)

    doc.vector_ids = vector_ids
    doc.is_indexed = True
    await db.commit()

    return IngestResponse(
        document_id=doc.id,
        status="success",
        chunk_count=len(chunks),
        message="Document ingested and indexed",
    )


@router.get("/{project_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    project_id: int,
    current_user=Depends(get_current_active_member),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id))
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    res = await db.execute(select(Document).where(Document.project_id == project_id).order_by(Document.created_at.desc()))
    return list(res.scalars().all())
