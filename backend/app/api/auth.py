from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from datetime import datetime
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import re

logger = logging.getLogger(__name__)

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    ตรวจสอบความแข็งแรงของรหัสผ่านตามมาตรฐานความปลอดภัย
    
    ข้อกำหนด:
    - ความยาวอย่างน้อย 8 ตัวอักษร
    - ต้องมีตัวอักษรพิมพ์ใหญ่ (A-Z)
    - ต้องมีตัวอักษรพิมพ์เล็ก (a-z)
    - ต้องมีตัวเลข (0-9)
    - ต้องมีอักขระพิเศษ (!@#$%^&*(),.?":{}|<>)
    
    Returns:
        tuple[bool, str]: (ผ่านการตรวจสอบ, ข้อความอธิบาย)
    """
    if len(password) < 8:
        return False, "รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร"
    if not re.search(r"[A-Z]", password):
        return False, "รหัสผ่านต้องมีตัวอักษรพิมพ์ใหญ่อย่างน้อย 1 ตัว"
    if not re.search(r"[a-z]", password):
        return False, "รหัสผ่านต้องมีตัวอักษรพิมพ์เล็กอย่างน้อย 1 ตัว"
    if not re.search(r"\d", password):
        return False, "รหัสผ่านต้องมีตัวเลขอย่างน้อย 1 ตัว"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "รหัสผ่านต้องมีอักขระพิเศษอย่างน้อย 1 ตัว (!@#$%^&*(),.?\":{}|<>)"
    return True, "รหัสผ่านถูกต้อง"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/register")
@limiter.limit("3/hour")  # 3 registrations per hour per IP
async def register(payload: RegisterRequest, request: Request):
    """Register a user.

    Note: This is a scaffold endpoint. Wire to TiDB (users table) + bcrypt hashing.
    Rate limited to 3 attempts per hour per IP.
    """
    logger.info(f"API auth: Registration attempt for email: {payload.email}")
    
    # ตรวจสอบความแข็งแรงของรหัสผ่าน
    is_valid, message = validate_password_strength(payload.password)
    if not is_valid:
        logger.warning(f"Weak password attempt for email: {payload.email}")
        raise HTTPException(status_code=400, detail=message)
    
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


@router.post("/reset-password")
@limiter.limit("3/hour")  # 3 reset attempts per hour per IP
async def reset_password(payload: ResetPasswordRequest, request: Request):
    """Reset password with token.

    Validates the new password meets security requirements.
    Rate limited to 3 attempts per hour per IP.
    """
    logger.info(f"API auth: Password reset attempt")
    
    # ตรวจสอบความแข็งแรงของรหัสผ่านใหม่
    is_valid, message = validate_password_strength(payload.new_password)
    if not is_valid:
        logger.warning(f"Weak password reset attempt")
        raise HTTPException(status_code=400, detail=message)
    
    # TODO: Implement actual password reset logic with token validation
    return {"message": "Password has been reset successfully"}
