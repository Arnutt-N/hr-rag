from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


@router.get("")
async def list_keys():
    return []


class CreateKeyRequest(BaseModel):
    name: str = "Default Key"
    rate_limit: int = 1000


@router.post("")
async def create_key(payload: CreateKeyRequest):
    return {"id": 1, "name": payload.name, "rate_limit": payload.rate_limit, "created_at": datetime.utcnow().isoformat()}


@router.delete("/{key_id}")
async def delete_key(key_id: int):
    return {"deleted": True, "id": key_id}
