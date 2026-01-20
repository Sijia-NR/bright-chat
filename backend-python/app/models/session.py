from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional, List
from pydantic import BaseModel, field_validator
from datetime import datetime
import uuid

from ..core.database import Base
from .user import User


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    last_updated = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    user = relationship("User")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class SessionCreate(BaseModel):
    title: str
    user_id: str

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or len(v) < 1:
            raise ValueError('Title cannot be empty')
        if len(v) > 200:
            raise ValueError('Title cannot exceed 200 characters')
        return v


class SessionResponse(BaseModel):
    id: str
    title: str
    last_updated: datetime
    user_id: str

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(String(5000), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    session = relationship("Session", back_populates="messages")


class MessageCreate(BaseModel):
    messages: List[dict]  # List of message objects

    @field_validator('messages')
    @classmethod
    def validate_messages(cls, v):
        if not v:
            raise ValueError('Messages list cannot be empty')
        if len(v) > 1000:
            raise ValueError('Cannot save more than 1000 messages at once')

        for msg in v:
            if 'role' not in msg:
                raise ValueError('Each message must have a role')
            if msg['role'] not in ['user', 'assistant', 'system']:
                raise ValueError('Role must be one of: user, assistant, system')
            if 'content' not in msg or not msg['content']:
                raise ValueError('Message content cannot be empty')
            if 'timestamp' not in msg:
                raise ValueError('Message timestamp is required')
        return v


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True


class MessagesResponse(BaseModel):
    messages: List[MessageResponse]