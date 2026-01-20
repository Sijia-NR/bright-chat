from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
import uuid

from ..core.database import Base


class UserRole(PyEnum):
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


class UserCreate(BaseModel):
    username: str
    role: UserRole = UserRole.USER

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username cannot exceed 50 characters')
        return v

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in UserRole:
            raise ValueError(f'Role must be one of: {[role.value for role in UserRole]}')
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is None:
            return v
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username cannot exceed 50 characters')
        return v


class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    id: str
    username: str
    role: str
    created_at: datetime
    token: str