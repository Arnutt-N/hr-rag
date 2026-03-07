from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(payload: RegisterRequest):
    """Register a user.

    Note: This is a scaffold endpoint. Wire to TiDB (users table) + bcrypt hashing.
    """
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password too short")
    return {"id": 1, "email": payload.email, "created_at": datetime.utcnow().isoformat()}


@router.post("/login")
async def login(payload: LoginRequest):
    """Login a user.

    Note: This is a scaffold endpoint. Wire to JWT + users table.
    """
    return {"access_token": "dev-token", "token_type": "bearer"}
