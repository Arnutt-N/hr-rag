"""Auth router: register/login/me

JWT-based auth for members.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.models.schemas import UserCreate, UserLogin, Token, UserResponse
from app.models.database import User, get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.core.logging import get_logger

# Setup structlog logger
logger = get_logger(__name__)

# Rate limiter instance (use same key_func as main)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["auth"])


# Rate limit exceeded handler for this router
@router.exception_handler(RateLimitExceeded)
async def auth_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Log rate limit hits for auth endpoints."""
    logger.warning(
        "auth_rate_limit_exceeded",
        ip=get_remote_address(request),
        endpoint=request.url.path,
        detail=exc.detail,
    )
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests", "retry_after": str(exc.detail)},
        headers={"Retry-After": str(exc.detail)}
    )


@router.post("/register", response_model=UserResponse)
@limiter.limit("3/hour")  # 3 registrations per hour per IP
async def register(payload: UserCreate, request: Request, db: AsyncSession = Depends(get_db)):
    """Register a new user.
    
    Rate limited to 3 attempts per hour per IP to prevent abuse.
    """
    logger.info("user_registration_attempt", email=payload.email, ip=get_remote_address(request))
    
    # ensure unique
    res = await db.execute(select(User).where((User.email == payload.email) | (User.username == payload.username)))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email or username already exists")

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        # default: user
        is_member=False,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("user_registered", user_id=user.id, email=user.email)
    return user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")  # 5 login attempts per minute per IP
async def login(payload: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    """Login with username and password.
    
    Rate limited to 5 attempts per minute per IP to prevent brute force attacks.
    """
    logger.info("user_login_attempt", username=payload.username, ip=get_remote_address(request))
    
    res = await db.execute(select(User).where(User.username == payload.username))
    user = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        logger.warning("user_login_failed", username=payload.username, reason="invalid_credentials")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        logger.warning("user_login_failed", username=payload.username, reason="user_disabled")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User disabled")

    token = create_access_token({"sub": str(user.id)})
    logger.info("user_logged_in", user_id=user.id, username=user.username)
    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user)):
    return current_user
