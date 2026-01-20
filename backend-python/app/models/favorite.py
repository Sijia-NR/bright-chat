from sqlalchemy import Column, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional, List
from pydantic import BaseModel, field_validator
from datetime import datetime
import uuid

from ..core.database import Base
from .user import User
from .session import Session, Message


class MessageFavorite(Base):
    """消息收藏表"""
    __tablename__ = "message_favorites"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    message_id = Column(String(36), ForeignKey("messages.id"), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    note = Column(String(500), nullable=True)  # 用户备注
    created_at = Column(DateTime, nullable=False, default=func.now())

    # 唯一约束：一个用户对一条消息只能收藏一次
    __table_args__ = (
        UniqueConstraint('user_id', 'message_id', name='uq_user_message'),
    )

    # Relationships
    user = relationship("User")
    message = relationship("Message")
    session = relationship("Session")


# Pydantic Models

class FavoriteCreate(BaseModel):
    """创建收藏请求"""
    note: Optional[str] = None

    @field_validator('note')
    @classmethod
    def validate_note(cls, v):
        if v and len(v) > 500:
            raise ValueError('备注不能超过500字符')
        return v


class FavoriteResponse(BaseModel):
    """收藏响应"""
    id: str
    message: 'MessageResponse'
    session: 'SessionResponse'
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FavoriteListResponse(BaseModel):
    """收藏列表响应"""
    favorites: List[FavoriteResponse]
    total: int


class FavoriteStatusResponse(BaseModel):
    """收藏状态响应"""
    is_favorited: bool
    favorite_id: Optional[str] = None
