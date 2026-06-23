from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str
    display_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class UserLogin(BaseModel):
    login: str  # username, email или phone
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    status: Optional[str] = None
    is_online: bool
    last_seen: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfile(BaseModel):
    id: str
    username: str
    display_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    status: Optional[str] = None
    is_online: bool
    last_seen: datetime
    created_at: datetime
    friends_count: int = 0
    posts_count: int = 0

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    status: Optional[str] = None
    avatar_url: Optional[str] = None
