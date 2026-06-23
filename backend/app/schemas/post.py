from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PostCreate(BaseModel):
    content: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None


class PostResponse(BaseModel):
    id: str
    author_id: str
    content: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    author_name: str = ""
    author_avatar: Optional[str] = None
    likes_count: int = 0
    comments_count: int = 0
    liked_by_me: bool = False

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: str
    post_id: str
    author_id: str
    content: str
    created_at: datetime
    author_name: str = ""

    model_config = {"from_attributes": True}
