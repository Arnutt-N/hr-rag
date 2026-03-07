"""Auth router: register/login/me

JWT-based auth for members.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.schemas import UserCreate, UserLogin, Token, UserResponse
from app.models.database import User, get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
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
    return user


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.username == payload.username))
    user = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User disabled")

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user)):
    return current_user
