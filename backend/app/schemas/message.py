from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    recipient_id: str
    content: Optional[str] = None
    image_url: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    chat_id: str
    sender_id: str
    content: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    is_read: bool
    sender_name: str = ""

    model_config = {"from_attributes": True}


class ChatItem(BaseModel):
    chat_id: str
    other_user_id: str
    other_user_name: str
    other_user_avatar: Optional[str] = None
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0


class StoryCreate(BaseModel):
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    caption: Optional[str] = None


class StoryResponse(BaseModel):
    id: str
    user_id: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    caption: Optional[str] = None
    created_at: datetime
    user_name: str = ""
    user_avatar: Optional[str] = None

    model_config = {"from_attributes": True}


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = True


class GroupResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    is_public: bool
    owner_id: str
    created_at: datetime
    members_count: int = 0

    model_config = {"from_attributes": True}
