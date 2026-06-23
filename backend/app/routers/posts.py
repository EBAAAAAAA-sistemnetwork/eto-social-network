from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List

from app.database import get_db
from app.models.models import User, Post, Comment, Like, friends_table
from app.schemas.post import PostCreate, PostResponse, CommentCreate, CommentResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/posts", tags=["posts"])


async def enrich_post(post: Post, db: AsyncSession, current_user_id: str) -> dict:
    author = await db.execute(select(User).where(User.id == post.author_id))
    author_user = author.scalar_one_or_none()

    likes_count = await db.execute(
        select(func.count()).where(Like.post_id == post.id)
    )
    comments_count = await db.execute(
        select(func.count()).where(Comment.post_id == post.id)
    )
    liked = await db.execute(
        select(Like).where(Like.post_id == post.id, Like.user_id == current_user_id)
    )

    return {
        "id": post.id,
        "author_id": post.author_id,
        "content": post.content,
        "image_url": post.image_url,
        "video_url": post.video_url,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "author_name": author_user.display_name if author_user else "",
        "author_avatar": author_user.avatar_url if author_user else None,
        "likes_count": likes_count.scalar() or 0,
        "comments_count": comments_count.scalar() or 0,
        "liked_by_me": liked.first() is not None,
    }


@router.get("/feed")
async def get_feed(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    friend_ids_subq = select(friends_table.c.friend_id).where(
        friends_table.c.user_id == current_user.id
    )
    friend_result = await db.execute(friend_ids_subq)
    friend_ids = [row[0] for row in friend_result.all()]
    friend_ids.append(current_user.id)

    result = await db.execute(
        select(Post)
        .where(Post.author_id.in_(friend_ids))
        .order_by(desc(Post.created_at))
        .offset(skip)
        .limit(limit)
    )
    posts = result.scalars().all()
    return [await enrich_post(p, db, current_user.id) for p in posts]


@router.get("/user/{user_id}")
async def get_user_posts(
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Post)
        .where(Post.author_id == user_id)
        .order_by(desc(Post.created_at))
        .offset(skip)
        .limit(limit)
    )
    posts = result.scalars().all()
    return [await enrich_post(p, db, current_user.id) for p in posts]


@router.post("/")
async def create_post(
    data: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = Post(author_id=current_user.id, content=data.content, image_url=data.image_url, video_url=data.video_url)
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return await enrich_post(post, db, current_user.id)


@router.get("/{post_id}")
async def get_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    return await enrich_post(post, db, current_user.id)


@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет прав")
    await db.delete(post)
    await db.commit()
    return {"status": "deleted"}


@router.post("/{post_id}/like")
async def toggle_like(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    existing = await db.execute(
        select(Like).where(Like.post_id == post_id, Like.user_id == current_user.id)
    )
    like = existing.scalar_one_or_none()
    if like:
        await db.delete(like)
        await db.commit()
        return {"status": "unliked"}
    else:
        new_like = Like(post_id=post_id, user_id=current_user.id)
        db.add(new_like)
        await db.commit()
        return {"status": "liked"}


@router.get("/{post_id}/comments")
async def get_comments(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at)
    )
    comments = result.scalars().all()
    out = []
    for c in comments:
        author = await db.execute(select(User).where(User.id == c.author_id))
        author_user = author.scalar_one_or_none()
        out.append({
            "id": c.id,
            "post_id": c.post_id,
            "author_id": c.author_id,
            "content": c.content,
            "created_at": c.created_at,
            "author_name": author_user.display_name if author_user else "",
        })
    return out


@router.post("/{post_id}/comments")
async def add_comment(
    post_id: str,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Пост не найден")

    comment = Comment(post_id=post_id, author_id=current_user.id, content=data.content)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return {
        "id": comment.id,
        "post_id": comment.post_id,
        "author_id": comment.author_id,
        "content": comment.content,
        "created_at": comment.created_at,
        "author_name": current_user.display_name,
    }
