from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta

from app.database import get_db
from app.models.models import User, Story
from app.schemas.message import StoryCreate, StoryResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/stories", tags=["stories"])


@router.get("/feed")
async def get_stories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cutoff = datetime.utcnow() - timedelta(hours=24)
    result = await db.execute(
        select(Story)
        .where(Story.expires_at > datetime.utcnow())
        .where(Story.created_at > cutoff)
        .order_by(desc(Story.created_at))
        .limit(50)
    )
    stories = result.scalars().all()
    out = []
    for s in stories:
        author = await db.execute(select(User).where(User.id == s.user_id))
        a = author.scalar_one_or_none()
        out.append({
            "id": s.id,
            "user_id": s.user_id,
            "image_url": s.image_url,
            "video_url": s.video_url,
            "caption": s.caption,
            "created_at": s.created_at.isoformat(),
            "user_name": a.display_name if a else "",
            "user_avatar": a.avatar_url if a else None,
        })
    return out


@router.post("/")
async def create_story(
    data: StoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    story = Story(
        user_id=current_user.id,
        image_url=data.image_url,
        video_url=data.video_url,
        caption=data.caption,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(story)
    await db.commit()
    await db.refresh(story)
    return {
        "id": story.id,
        "user_id": story.user_id,
        "image_url": story.image_url,
        "video_url": story.video_url,
        "caption": story.caption,
        "created_at": story.created_at.isoformat(),
        "user_name": current_user.display_name,
        "user_avatar": current_user.avatar_url,
    }


@router.delete("/{story_id}")
async def delete_story(
    story_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="История не найдена")
    if story.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет прав")
    await db.delete(story)
    await db.commit()
    return {"status": "deleted"}
