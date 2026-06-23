from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.models import User, Group, group_members_table
from app.schemas.message import GroupCreate, GroupResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/groups", tags=["groups"])


@router.get("/")
async def list_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Group).order_by(Group.created_at.desc()).limit(50)
    )
    groups = result.scalars().all()
    out = []
    for g in groups:
        cnt = await db.execute(
            select(func.count()).where(group_members_table.c.group_id == g.id)
        )
        out.append({
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "avatar_url": g.avatar_url,
            "is_public": g.is_public,
            "owner_id": g.owner_id,
            "created_at": g.created_at.isoformat(),
            "members_count": cnt.scalar() or 0,
        })
    return out


@router.post("/")
async def create_group(
    data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = Group(
        name=data.name,
        description=data.description,
        is_public=data.is_public,
        owner_id=current_user.id,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)

    await db.execute(
        group_members_table.insert().values(
            user_id=current_user.id, group_id=group.id, role="owner"
        )
    )
    await db.commit()

    return {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "avatar_url": group.avatar_url,
        "is_public": group.is_public,
        "owner_id": group.owner_id,
        "created_at": group.created_at.isoformat(),
        "members_count": 1,
    }


@router.post("/{group_id}/join")
async def join_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = await db.execute(select(Group).where(Group.id == group_id))
    if not group.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Группа не найдена")

    existing = await db.execute(
        select(group_members_table).where(
            group_members_table.c.user_id == current_user.id,
            group_members_table.c.group_id == group_id,
        )
    )
    if existing.first():
        return {"status": "already_member"}

    await db.execute(
        group_members_table.insert().values(
            user_id=current_user.id, group_id=group_id, role="member"
        )
    )
    await db.commit()
    return {"status": "joined"}


@router.post("/{group_id}/leave")
async def leave_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db.execute(
        group_members_table.delete().where(
            group_members_table.c.user_id == current_user.id,
            group_members_table.c.group_id == group_id,
        )
    )
    await db.commit()
    return {"status": "left"}


@router.get("/{group_id}/members")
async def get_members(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(User, group_members_table.c.role)
        .join(group_members_table, User.id == group_members_table.c.user_id)
        .where(group_members_table.c.group_id == group_id)
    )
    rows = result.all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "display_name": u.display_name,
            "avatar_url": u.avatar_url,
            "role": role,
        }
        for u, role in rows
    ]
