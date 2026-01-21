
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, Enum, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, field_validator
from datetime import datetime
import enum
import uuid

# Import database base from parent directory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base
from user import User


class ModelType(str, enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"
    IAS = "ias"


class LLMModel(Base):
    __tablename__ = "llm_models"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    model_type = Column(Enum(ModelType), nullable=False, default=ModelType.CUSTOM)
    api_url = Column(String(500), nullable=False)
    api_key = Column(Text, nullable=False)  # 明文存储 API Key，admin 用户可见
    api_version = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    max_tokens = Column(Integer, default=4096)
    temperature = Column(Integer, default=70)  # 存储为 70 表示 0.70
    stream_supported = Column(Boolean, default=True)
    custom_headers = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    creator = relationship("User")


# Pydantic Models

class LLMModelCreate(BaseModel):
    name: str
    display_name: str
    model_type: ModelType = ModelType.CUSTOM
    api_url: str
    api_key: str  # Will be encrypted before storage
    api_version: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    max_tokens: int = 4096
    temperature: float = 0.70
    stream_supported: bool = True
    custom_headers: Optional[Dict[str, str]] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v) < 2:
            raise ValueError('Model name must be at least 2 characters')
        if len(v) > 100:
            raise ValueError('Model name cannot exceed 100 characters')
        return v

    @field_validator('api_url')
    @classmethod
    def validate_api_url(cls, v):
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError('API URL must be a valid HTTP/HTTPS URL')
        return v

    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v


class LLMModelUpdate(BaseModel):
    display_name: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    api_version: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream_supported: Optional[bool] = None
    custom_headers: Optional[Dict[str, str]] = None


class LLMModelResponse(BaseModel):
    id: str
    name: str
    display_name: str
    model_type: str
    api_url: str
    api_version: Optional[str]
    description: Optional[str]
    is_active: bool
    max_tokens: int
    temperature: float
    stream_supported: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LLMModelListResponse(BaseModel):
    models: List[LLMModelResponse]
    total: int
