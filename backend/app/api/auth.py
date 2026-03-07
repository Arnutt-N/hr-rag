from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from datetime import datetime
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

logger = logging.getLogger(__name__)

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/register")
@limiter.limit("3/hour")  # 3 registrations per hour per IP
async def register(payload: RegisterRequest, request: Request):
    """Register a user.

    Note: This is a scaffold endpoint. Wire to TiDB (users table) + bcrypt hashing.
    Rate limited to 3 attempts per hour per IP.
    """
    logger.info(f"API auth: Registration attempt for email: {payload.email}")
    
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password too short")
    return {"id": 1, "email": payload.email, "created_at": datetime.utcnow().isoformat()}


@router.post("/login")
@limiter.limit("5/minute")  # 5 login attempts per minute per IP
async def login(payload: LoginRequest, request: Request):
    """Login a user.

    Note: This is a scaffold endpoint. Wire to JWT + users table.
    Rate limited to 5 attempts per minute per IP.
    """
    logger.info(f"API auth: Login attempt for email: {payload.email}")
    return {"access_token": "dev-token", "token_type": "bearer"}


@router.post("/forgot-password")
@limiter.limit("3/hour")  # 3 forgot-password requests per hour per IP
async def forgot_password(payload: ForgotPasswordRequest, request: Request):
    """Request password reset.

    Rate limited to 3 requests per hour per IP to prevent abuse.
    """
    logger.info(f"API auth: Password reset request for email: {payload.email}")
    # TODO: Implement actual password reset logic
    return {"message": "If the email exists, a reset link will be sent"}
