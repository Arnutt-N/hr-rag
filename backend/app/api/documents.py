from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


@router.get("/{project_id}")
async def list_documents(project_id: int):
    return []


@router.post("/{project_id}/upload")
async def upload_document(project_id: int, file: UploadFile = File(...)):
    """Upload a document.

    Scaffold: store metadata in TiDB (project_documents) and index chunks into Qdrant.
    """
    return {"project_id": project_id, "filename": file.filename, "status": "uploaded"}


class SearchRequest(BaseModel):
    query: str
    project_id: Optional[int] = None
    limit: int = 5


@router.post("/search")
async def search_documents(payload: SearchRequest):
    """Vector search scaffold."""
    return {"query": payload.query, "results": []}


@router.delete("/delete/{document_id}")
async def delete_document(document_id: int):
    return {"deleted": True, "id": document_id}
