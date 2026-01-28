"""
知识库相关数据模型
Knowledge Base related data models
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, field_validator
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import relationship

from ..core.database import Base


class KnowledgeGroup(Base):
    """知识库分组表"""
    __tablename__ = "knowledge_groups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    color = Column(String(20), default="#3B82F6")
    created_at = Column(DateTime, nullable=False, default=func.now())

    knowledge_bases = relationship("KnowledgeBase", back_populates="group", cascade="all, delete-orphan")


class KnowledgeBase(Base):
    """知识库表"""
    __tablename__ = "knowledge_bases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(String(36), ForeignKey("knowledge_groups.id", ondelete="SET NULL"), nullable=True)
    embedding_model = Column(String(100), default="bge-large-zh-v1.5")
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=50)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    group = relationship("KnowledgeGroup", back_populates="knowledge_bases")
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")


class Document(Base):
    """知识库文档表"""
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_base_id = Column(String(36), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=True)
    file_size = Column(Integer, nullable=True)
    chunk_count = Column(Integer, default=0)
    upload_status = Column(String(50), default="processing")
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, nullable=False, default=func.now())
    processed_at = Column(DateTime, nullable=True)

    knowledge_base = relationship("KnowledgeBase", back_populates="documents")


# ==================== Pydantic 模型用于 API ====================

# 常量定义
DEFAULT_COLOR = "#3B82F6"
DEFAULT_EMBEDDING_MODEL = "bge-large-zh-v1.5"
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
MIN_CHUNK_SIZE = 100
MAX_CHUNK_SIZE = 2000
MAX_CHUNK_OVERLAP = 500
MAX_NAME_LENGTH = 255
MAX_QUERY_LENGTH = 2000

ALLOWED_FILE_TYPES = ("pdf", "docx", "txt", "md", "html")
UPLOAD_STATUSES = ("processing", "completed", "failed")


def validate_not_empty(value: str, field_name: str) -> str:
    """验证字符串非空"""
    if not value or len(value.strip()) == 0:
        raise ValueError(f"{field_name}不能为空")
    if len(value) > MAX_NAME_LENGTH:
        raise ValueError(f"{field_name}不能超过{MAX_NAME_LENGTH}个字符")
    return value.strip()


def validate_chunk_size(value: int) -> int:
    """验证分块大小"""
    if value < MIN_CHUNK_SIZE or value > MAX_CHUNK_SIZE:
        raise ValueError(f"分块大小必须在{MIN_CHUNK_SIZE}-{MAX_CHUNK_SIZE}之间")
    return value


def validate_chunk_overlap(value: int) -> int:
    """验证分块重叠"""
    if value < 0 or value > MAX_CHUNK_OVERLAP:
        raise ValueError(f"分块重叠必须在0-{MAX_CHUNK_OVERLAP}之间")
    return value


class KnowledgeGroupCreate(BaseModel):
    """创建知识库分组请求"""
    name: str
    description: Optional[str] = None
    color: str = DEFAULT_COLOR

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_not_empty(v, "分组名称")


class KnowledgeGroupResponse(BaseModel):
    """知识库分组响应"""
    id: str
    name: str
    description: Optional[str] = None
    user_id: str
    color: str
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""
    name: str
    description: Optional[str] = None
    group_id: Optional[str] = None
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_not_empty(v, "知识库名称")

    @field_validator('chunk_size')
    @classmethod
    def validate_chunk_size(cls, v: int) -> int:
        return validate_chunk_size(v)

    @field_validator('chunk_overlap')
    @classmethod
    def validate_chunk_overlap(cls, v: int) -> int:
        return validate_chunk_overlap(v)


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    group_id: Optional[str] = None
    is_active: Optional[bool] = None


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: str
    name: str
    description: Optional[str] = None
    user_id: str
    group_id: Optional[str] = None
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    document_count: int = 0

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    """创建文档请求（内部使用）"""
    knowledge_base_id: str
    filename: str
    file_type: str
    file_size: Optional[int] = None


class DocumentResponse(BaseModel):
    """文档响应"""
    id: str
    knowledge_base_id: str
    filename: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    chunk_count: int
    upload_status: str
    error_message: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    document_id: str
    filename: str
    status: str
    message: str


class RAGChatRequest(BaseModel):
    """RAG 聊天请求"""
    query: str
    knowledge_base_ids: List[str]
    session_id: Optional[str] = None
    retrieval_config: Optional[Dict[str, Any]] = None

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("查询内容不能为空")
        if len(v) > MAX_QUERY_LENGTH:
            raise ValueError(f"查询内容不能超过{MAX_QUERY_LENGTH}个字符")
        return v.strip()

    @field_validator('knowledge_base_ids')
    @classmethod
    def validate_kb_ids(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("请至少选择一个知识库")
        return v


class RAGChatResponse(BaseModel):
    """RAG 聊天响应"""
    answer: str
    sources: List[Dict[str, Any]]
    knowledge_bases_used: List[str]
