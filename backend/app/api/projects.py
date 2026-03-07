from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


@router.get("")
async def list_projects():
    return []


@router.post("")
async def create_project(payload: ProjectCreate):
    return {"id": 1, "name": payload.name, "description": payload.description, "created_at": datetime.utcnow().isoformat()}


@router.get("/{project_id}")
async def get_project(project_id: int):
    return {"id": project_id, "name": "Demo", "description": None}


@router.delete("/{project_id}")
async def delete_project(project_id: int):
    return {"deleted": True, "id": project_id}
