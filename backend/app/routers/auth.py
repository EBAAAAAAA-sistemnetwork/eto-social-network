from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from fastapi.security import OAuth2PasswordRequestForm

from app.database import get_db
from app.models.models import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.auth import hash_password, verify_password, create_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(User).where(User.username == data.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Имя пользователя уже занято")

    if data.email:
        email_exist = await db.execute(select(User).where(User.email == data.email))
        if email_exist.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email уже используется")

    if data.phone:
        phone_exist = await db.execute(select(User).where(User.phone == data.phone))
        if phone_exist.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Телефон уже используется")

    user = User(
        username=data.username,
        display_name=data.display_name,
        email=data.email,
        phone=data.phone,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(
            or_(
                User.username == data.login,
                User.email == data.login,
                User.phone == data.login,
            )
        )
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    token = create_token({"sub": user.id})
    user.is_online = True
    await db.commit()
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
        },
    }


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/oauth/token")
async def login_oauth(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    token = create_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}
