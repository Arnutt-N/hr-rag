"""Projects router

Members have isolated projects. Each project maps to an isolated Qdrant collection.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_active_member
from app.models.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from app.models.database import Project, get_db
from app.services.vector_store import get_vector_store

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse)
async def create_project(
    payload: ProjectCreate,
    current_user=Depends(get_current_active_member),
    db: AsyncSession = Depends(get_db),
):
    project = Project(
        name=payload.name,
        description=payload.description,
        owner_id=current_user.id,
        is_public=payload.is_public,
        settings=payload.settings or {},
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    # create vector collection
    vs = get_vector_store()
    await vs.create_collection(project.id)

    project.vector_collection = f"hr_project_{project.id}"
    await db.commit()
    await db.refresh(project)

    return project


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    current_user=Depends(get_current_active_member),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Project).where(Project.owner_id == current_user.id).order_by(Project.created_at.desc()))
    return list(res.scalars().all())


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user=Depends(get_current_active_member),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    current_user=Depends(get_current_active_member),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(project, k, v)

    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user=Depends(get_current_active_member),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # delete qdrant collection
    vs = get_vector_store()
    await vs.delete_collection(project.id)

    await db.delete(project)
    await db.commit()
    return {"status": "deleted"}
