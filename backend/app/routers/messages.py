from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, and_
from typing import List, Dict
import json

from app.database import get_db, async_session
from app.models.models import User, Message
from app.schemas.message import MessageCreate, MessageResponse, ChatItem
from app.auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["messages"])

active_connections: Dict[str, WebSocket] = {}


def make_chat_id(u1: str, u2: str) -> str:
    return "_".join(sorted([u1, u2]))


@router.get("/chats")
async def get_chats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subq = (
        select(
            Message.chat_id,
            func.max(Message.created_at).label("last_time"),
        )
        .where(Message.chat_id.contains(current_user.id))
        .group_by(Message.chat_id)
        .subquery()
    )

    result = await db.execute(
        select(Message, subq.c.last_time)
        .join(subq, and_(Message.chat_id == subq.c.chat_id, Message.created_at == subq.c.last_time))
        .order_by(desc(subq.c.last_time))
    )
    rows = result.all()

    chats = []
    seen = set()
    for msg, _ in rows:
        if msg.chat_id in seen:
            continue
        seen.add(msg.chat_id)

        parts = msg.chat_id.split("_")
        other_id = parts[0] if parts[1] == current_user.id else parts[1]

        other_user = await db.execute(select(User).where(User.id == other_id))
        other = other_user.scalar_one_or_none()
        if not other:
            continue

        unread = await db.execute(
            select(func.count()).where(
                Message.chat_id == msg.chat_id,
                Message.sender_id != current_user.id,
                Message.is_read == False,
            )
        )

        chats.append({
            "chat_id": msg.chat_id,
            "other_user_id": other.id,
            "other_user_name": other.display_name,
            "other_user_avatar": other.avatar_url,
            "last_message": msg.content,
            "last_message_time": msg.created_at.isoformat(),
            "unread_count": unread.scalar() or 0,
        })
    return chats


@router.get("/{chat_id}")
async def get_messages(
    chat_id: str,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(desc(Message.created_at))
        .offset(skip)
        .limit(limit)
    )
    msgs = result.scalars().all()
    out = []
    for m in reversed(msgs):
        sender = await db.execute(select(User).where(User.id == m.sender_id))
        s = sender.scalar_one_or_none()
        out.append({
            "id": m.id,
            "chat_id": m.chat_id,
            "sender_id": m.sender_id,
            "content": m.content,
            "image_url": m.image_url,
            "created_at": m.created_at.isoformat(),
            "is_read": m.is_read,
            "sender_name": s.display_name if s else "",
        })
    return out


@router.post("/send")
async def send_message(
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = await db.execute(select(User).where(User.id == data.recipient_id))
    if not target.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    chat_id = make_chat_id(current_user.id, data.recipient_id)
    msg = Message(
        chat_id=chat_id,
        sender_id=current_user.id,
        content=data.content,
        image_url=data.image_url,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    result = {
        "id": msg.id,
        "chat_id": msg.chat_id,
        "sender_id": msg.sender_id,
        "content": msg.content,
        "image_url": msg.image_url,
        "created_at": msg.created_at.isoformat(),
        "is_read": msg.is_read,
        "sender_name": current_user.display_name,
    }

    if data.recipient_id in active_connections:
        try:
            await active_connections[data.recipient_id].send_text(json.dumps(result))
        except Exception:
            pass

    return result


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    try:
        data = await websocket.receive_text()
        token_data = json.loads(data)
        token = token_data.get("token")

        import jwt
        from app.config import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        active_connections[user_id] = websocket

        async with async_session() as db:
            user = await db.execute(select(User).where(User.id == user_id))
            u = user.scalar_one_or_none()
            if u:
                u.is_online = True
                await db.commit()

        while True:
            raw = await websocket.receive_text()
            msg_data = json.loads(raw)
            recipient_id = msg_data.get("recipient_id")
            content = msg_data.get("content", "")

            async with async_session() as db:
                chat_id = make_chat_id(user_id, recipient_id)
                msg = Message(chat_id=chat_id, sender_id=user_id, content=content)
                db.add(msg)
                await db.commit()
                await db.refresh(msg)

                user_result = await db.execute(select(User).where(User.id == user_id))
                sender = user_result.scalar_one_or_none()

                out = {
                    "id": msg.id,
                    "chat_id": msg.chat_id,
                    "sender_id": msg.sender_id,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "is_read": msg.is_read,
                    "sender_name": sender.display_name if sender else "",
                }

                if recipient_id in active_connections:
                    try:
                        await active_connections[recipient_id].send_text(json.dumps(out))
                    except Exception:
                        pass

                await websocket.send_text(json.dumps(out))

    except WebSocketDisconnect:
        async with async_session() as db:
            if user_id in active_connections:
                del active_connections[user_id]
            user = await db.execute(select(User).where(User.id == user_id))
            u = user.scalar_one_or_none()
            if u:
                u.is_online = False
                await db.commit()
    except Exception:
        if user_id and user_id in active_connections:
            del active_connections[user_id]
