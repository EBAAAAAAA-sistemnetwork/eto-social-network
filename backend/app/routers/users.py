from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List

from app.database import get_db
from app.models.models import User, friends_table, Post
from app.schemas.user import UserProfile, UserUpdate, UserResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/search")
async def search_users(
    q: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(User)
        .where(
            or_(
                User.username.ilike(f"%{q}%"),
                User.display_name.ilike(f"%{q}%"),
            )
        )
        .limit(20)
    )
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "display_name": u.display_name,
            "avatar_url": u.avatar_url,
        }
        for u in users
    ]


@router.get("/{user_id}", response_model=UserProfile)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    friends_count_result = await db.execute(
        select(func.count()).where(friends_table.c.user_id == user_id)
    )
    friends_count = friends_count_result.scalar() or 0

    posts_count_result = await db.execute(
        select(func.count()).where(Post.author_id == user_id)
    )
    posts_count = posts_count_result.scalar() or 0

    return UserProfile(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        phone=user.phone,
        avatar_url=user.avatar_url,
        bio=user.bio,
        status=user.status,
        is_online=user.is_online,
        last_seen=user.last_seen,
        created_at=user.created_at,
        friends_count=friends_count,
        posts_count=posts_count,
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.display_name is not None:
        current_user.display_name = data.display_name
    if data.bio is not None:
        current_user.bio = data.bio
    if data.status is not None:
        current_user.status = data.status
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/{user_id}/friend")
async def toggle_friend(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя добавить самого себя")

    target = await db.execute(select(User).where(User.id == user_id))
    if not target.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    existing = await db.execute(
        select(friends_table).where(
            friends_table.c.user_id == current_user.id,
            friends_table.c.friend_id == user_id,
        )
    )
    if existing.first():
        await db.execute(
            friends_table.delete().where(
                friends_table.c.user_id.in_([current_user.id, user_id]),
                friends_table.c.friend_id.in_([current_user.id, user_id]),
            )
        )
        await db.commit()
        return {"status": "removed"}
    else:
        await db.execute(friends_table.insert().values(user_id=current_user.id, friend_id=user_id))
        await db.execute(friends_table.insert().values(user_id=user_id, friend_id=current_user.id))
        await db.commit()
        return {"status": "added"}


@router.get("/{user_id}/friends")
async def get_friends(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(User)
        .join(friends_table, User.id == friends_table.c.friend_id)
        .where(friends_table.c.user_id == user_id)
    )
    friends = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "display_name": u.display_name,
            "avatar_url": u.avatar_url,
            "is_online": u.is_online,
        }
        for u in friends
    ]
