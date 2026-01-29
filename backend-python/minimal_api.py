#!/usr/bin/env python3
"""
Minimal API for Bright-Chat - Single file implementation
"""
import os
import sys
import base64
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends, status, Header, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
import asyncio
import json
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Enum as SQLEnum, Text, ForeignKey, UniqueConstraint, Integer, JSON, text
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.ext.declarative import declarative_base
from jose import JWTError, jwt
import hashlib
import uuid
import secrets
import time
import logging
import httpx
from pathlib import Path

# Configure logging - restore INFO level for detailed logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Restore httpx and uvicorn access logs to INFO
logging.getLogger("httpx").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)

# RAG 相关导入
from app.rag.config import get_rag_config, KNOWLEDGE_COLLECTION
from app.rag.document_processor import DocumentProcessor

# Agent 相关导入
from app.agents.router import router as agents_router

# 配置管理 - 使用 Settings 而非硬编码
from app.core.config import settings

# Database setup - 从环境变量读取
DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash (supports both bcrypt and SHA256)"""
    # Try bcrypt first
    if hashed_password.startswith('$2b$') or hashed_password.startswith('$2a$'):
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            pass

    # Fallback to SHA256 for backwards compatibility
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

# JWT settings - 从环境变量读取
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

# App settings - 从 Settings 读取，不使用硬编码
APP_NAME = settings.APP_NAME
API_PREFIX = settings.API_PREFIX
SERVER_HOST = settings.SERVER_HOST
SERVER_PORT = settings.SERVER_PORT

# IAS settings - MockServer configuration
IAS_BASE_URL = "http://localhost:18063"
IAS_APP_KEY = "APP_KEY"

# Models
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

class Session(Base):
    __tablename__ = "sessions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    user_id = Column(String(36), nullable=False, index=True)
    agent_id = Column(String(36), nullable=True, index=True)  # 新增：关联的 Agent ID
    last_updated = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, nullable=False, default=func.now())

class Message(Base):
    __tablename__ = "messages"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(String(5000), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=func.now())

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

class LLMModelType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"
    IAS = "ias"

class LLMModel(Base):
    """LLM 模型配置表"""
    __tablename__ = "llm_models"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    model_type = Column(SQLEnum(LLMModelType), nullable=False, default=LLMModelType.CUSTOM)
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

# ==================== Knowledge Base Models ====================

class KnowledgeGroup(Base):
    """知识库分组表"""
    __tablename__ = "knowledge_groups"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User")
    knowledge_bases = relationship("KnowledgeBase", back_populates="group", cascade="all, delete-orphan")

class KnowledgeBase(Base):
    """知识库表"""
    __tablename__ = "knowledge_bases"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String(36), ForeignKey("knowledge_groups.id"), nullable=True)  # 允许为空，支持独立知识库
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    embedding_model = Column(String(100), default="bge-large-zh-v1.5")
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=50)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User")
    group = relationship("KnowledgeGroup", back_populates="knowledge_bases")
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")

class Document(Base):
    """文档表"""
    __tablename__ = "documents"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_base_id = Column(String(36), ForeignKey("knowledge_bases.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_status = Column(String(50), default="pending")  # pending, processing, completed, error
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.USER

class UserUpdate(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None

class UserResponse(BaseModel):
    id: str
    username: str
    role: str
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

class SessionCreate(BaseModel):
    title: str
    user_id: str
    agent_id: Optional[str] = None  # 新增：关联的 Agent ID

class SessionResponse(BaseModel):
    id: str
    title: str
    last_updated: datetime
    user_id: str
    agent_id: Optional[str] = None  # 新增：关联的 Agent ID

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    messages: List[dict]

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

# Favorite Pydantic models
class FavoriteCreate(BaseModel):
    """创建收藏请求"""
    note: Optional[str] = None

class FavoriteResponse(BaseModel):
    """收藏响应"""
    id: str
    message: MessageResponse
    session: SessionResponse
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

# LLM Model Pydantic models
class LLMModelCreate(BaseModel):
    """创建 LLM 模型请求"""
    name: str
    display_name: str
    model_type: LLMModelType = LLMModelType.CUSTOM
    api_url: str
    api_key: str  # Will be encrypted before storage
    api_version: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    max_tokens: int = 4096
    temperature: float = 0.70
    stream_supported: bool = True
    custom_headers: Optional[dict] = None

class LLMModelUpdate(BaseModel):
    """更新 LLM 模型请求"""
    display_name: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    api_version: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream_supported: Optional[bool] = None
    custom_headers: Optional[dict] = None

class LLMModelResponse(BaseModel):
    """LLM 模型响应"""
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
    """LLM 模型列表响应"""
    models: List[LLMModelResponse]
    total: int

# Knowledge Base Pydantic models
class KnowledgeGroupCreate(BaseModel):
    """创建知识库分组请求"""
    name: str
    description: Optional[str] = None

class KnowledgeGroupResponse(BaseModel):
    """知识库分组响应"""
    id: str
    name: str
    user_id: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""
    group_id: Optional[str] = None  # 允许不指定分组，创建独立知识库
    name: str
    description: Optional[str] = None
    embedding_model: str = "bge-large-zh-v1.5"
    chunk_size: int = 500
    chunk_overlap: int = 50

class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: str
    group_id: Optional[str] = None
    user_id: str
    name: str
    description: Optional[str] = None
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    created_at: datetime
    updated_at: datetime
    document_count: Optional[int] = 0

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    """文档响应"""
    id: str
    knowledge_base_id: str
    filename: str
    file_type: str
    file_size: int
    upload_status: str
    chunk_count: int
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Utilities
# This function is now defined above

def get_password_hash(password: str) -> str:
    return hash_password(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# JWT Authentication dependency
async def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """从 JWT token 获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 提取 Bearer token
    if authorization is None:
        raise credentials_exception

    if not authorization.startswith("Bearer "):
        raise credentials_exception

    token = authorization[7:]  # 去掉 "Bearer " 前缀

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user

# Model configuration service functions
def create_llm_model(db: Session, model_data: LLMModelCreate, creator_id: str) -> LLMModel:
    """创建新的 LLM 模型配置"""
    # 检查名称是否已存在
    existing = db.query(LLMModel).filter(LLMModel.name == model_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Model with name '{model_data.name}' already exists"
        )

    # 创建模型
    db_model = LLMModel(
        name=model_data.name,
        display_name=model_data.display_name,
        model_type=model_data.model_type,
        api_url=model_data.api_url,
        api_key=model_data.api_key,  # 明文存储
        api_version=model_data.api_version,
        description=model_data.description,
        is_active=model_data.is_active,
        max_tokens=model_data.max_tokens,
        temperature=int(model_data.temperature * 100),  # 转换为整数
        stream_supported=model_data.stream_supported,
        custom_headers=model_data.custom_headers,
        created_by=creator_id
    )

    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

def get_llm_model(db: Session, model_id: str) -> Optional[LLMModel]:
    """获取模型"""
    return db.query(LLMModel).filter(LLMModel.id == model_id).first()

def get_llm_model_by_name(db: Session, name: str) -> Optional[LLMModel]:
    """根据名称获取模型"""
    return db.query(LLMModel).filter(LLMModel.name == name).first()

def get_active_llm_models(db: Session) -> List[LLMModel]:
    """获取所有启用的模型"""
    return db.query(LLMModel).filter(LLMModel.is_active == True).order_by(LLMModel.created_at.desc()).all()

def list_llm_models(db: Session, skip: int = 0, limit: int = 100) -> List[LLMModel]:
    """列出所有模型（管理员）"""
    return db.query(LLMModel).offset(skip).limit(limit).all()

def update_llm_model(db: Session, model_id: str, model_data: LLMModelUpdate) -> Optional[LLMModel]:
    """更新模型配置"""
    db_model = get_llm_model(db, model_id)
    if not db_model:
        return None

    # 更新字段
    for field, value in model_data.model_dump(exclude_unset=True).items():
        if field == 'api_key' and value:
            # 明文存储 API Key
            setattr(db_model, 'api_key', value)
        elif field == 'temperature' and value is not None:
            # 转换为整数
            setattr(db_model, field, int(value * 100))
        else:
            setattr(db_model, field, value)

    db.commit()
    db.refresh(db_model)
    return db_model

def delete_llm_model(db: Session, model_id: str) -> bool:
    """删除模型配置"""
    db_model = get_llm_model(db, model_id)
    if not db_model:
        return False

    db.delete(db_model)
    db.commit()
    return True

def require_admin(current_user: User = Depends(get_current_user)):
    """要求管理员权限的依赖"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Initialize database
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Bright-Chat API",
    description="Bright-Chat Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 创建上传目录
UPLOAD_DIR = Path("uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
logger.info(f"上传目录已创建/确认: {UPLOAD_DIR}")

# CORS middleware - 允许所有来源访问（支持局域网）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Agent router
app.include_router(agents_router, prefix=f"{API_PREFIX}/agents", tags=["agents"])
logger.info("Agent routes mounted at /api/v1/agents")

# Auth endpoints
@app.post(f"{API_PREFIX}/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_username(db, login_data.username)
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    return LoginResponse(
        id=user.id,
        username=user.username,
        role=user.role.value,
        created_at=user.created_at,
        token=access_token
    )

@app.post(f"{API_PREFIX}/auth/logout")
async def logout():
    # In a real implementation, we would add the token to a blacklist
    # or perform other cleanup operations
    return {"message": "Successfully logged out"}

# Admin user management
@app.get(f"{API_PREFIX}/admin/users", response_model=List[UserResponse])
async def get_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查 admin 权限
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    users = db.query(User).all()
    return [UserResponse.model_validate(user) for user in users]

@app.get(f"{API_PREFIX}/admin/users/{{user_id}}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查 admin 权限
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(user)

@app.post(f"{API_PREFIX}/admin/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查 admin 权限
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Check if username already exists
    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Create user
    hashed_password = hash_password(user_data.password)
    db_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        role=user_data.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return UserResponse.model_validate(db_user)

@app.put(f"{API_PREFIX}/admin/users/{{user_id}}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查 admin 权限
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if username already exists for different user
    if user_data.username and user_data.username != user.username:
        existing_user = get_user_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

    # Update user fields
    if user_data.username:
        user.username = user_data.username
    if user_data.role:
        user.role = user_data.role

    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)

@app.delete(f"{API_PREFIX}/admin/users/{{user_id}}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查 admin 权限
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

# Session management
@app.get(f"{API_PREFIX}/sessions", response_model=List[SessionResponse])
async def get_sessions(user_id: str, db: Session = Depends(get_db)):
    sessions = db.query(Session).filter(Session.user_id == user_id).all()
    return [SessionResponse.from_orm(session) for session in sessions]

@app.post(f"{API_PREFIX}/sessions", response_model=SessionResponse)
async def create_session(session_data: SessionCreate, db: Session = Depends(get_db)):
    db_session = Session(
        title=session_data.title,
        user_id=session_data.user_id,
        agent_id=session_data.agent_id  # 新增：保存 agent_id
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return SessionResponse.from_orm(db_session)

@app.get(f"{API_PREFIX}/sessions/{{session_id}}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 验证会话是否存在且属于当前用户
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id  # 添加用户所有权验证
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp.asc(), Message.id.asc()).all()
    return [MessageResponse.from_orm(message) for message in messages]

@app.post(f"{API_PREFIX}/sessions/{{session_id}}/messages")
async def save_messages(session_id: str, message_data: MessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 验证会话是否存在且属于当前用户
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id  # 添加用户所有权验证
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Save or update messages with deduplication by ID
    for msg in message_data.messages:
        msg_id = msg.get('id')
        if not msg_id:
            continue  # Skip messages without ID

        # Check if message already exists
        existing = db.query(Message).filter(Message.id == msg_id).first()

        if existing:
            # Update existing message content
            existing.content = msg['content']
            # Update timestamp if provided
            if 'timestamp' in msg:
                existing.timestamp = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
        else:
            # Create new message
            timestamp = datetime.utcnow()
            if 'timestamp' in msg:
                try:
                    timestamp = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                except:
                    pass  # Fallback to current time

            db_message = Message(
                id=msg_id,
                session_id=session_id,
                role=msg['role'],
                content=msg['content'],
                timestamp=timestamp
            )
            db.add(db_message)

    db.commit()
    return {"message": "Messages saved successfully"}

@app.delete(f"{API_PREFIX}/sessions/{{session_id}}")
async def delete_session(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 验证会话是否存在且属于当前用户
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id  # 添加用户所有权验证
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # 获取会话的所有消息 ID
    messages = db.query(Message).filter(Message.session_id == session_id).all()
    message_ids = [msg.id for msg in messages]

    # 先删除这些消息的收藏记录（由于外键约束）
    if message_ids:
        db.query(MessageFavorite).filter(MessageFavorite.message_id.in_(message_ids)).delete(synchronize_session=False)

    # 删除所有消息
    db.query(Message).filter(Message.session_id == session_id).delete()

    # 删除会话
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    db.delete(session)
    db.commit()
    return {"message": "Session deleted successfully"}

# IAS API proxy - forwards requests to MockServer
@app.post(f"{API_PREFIX}/lmp-cloud-ias-server/api/llm/chat/completions/V2")
async def ias_proxy(request: dict, db: Session = Depends(get_db)):
    """
    Proxy request to configured LLM model API
    Supports dynamic routing based on model selection
    """
    # Get model name from request
    model_name = request.get("model", "")
    if not model_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model name is required"
        )

    # Get model configuration from database
    model = get_llm_model_by_name(db, model_name)

    if not model or not model.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_name}' not found or not active"
        )

    # Get API key (明文存储)
    api_key = model.api_key

    # Prepare headers based on model type
    headers = _prepare_model_headers(model, api_key, request)

    # Use model's API URL
    api_url = model.api_url

    # Get streaming flag
    is_stream = request.get("stream", True)

    # Forward request to configured model API
    client = httpx.AsyncClient(timeout=120.0)

    async def forward_stream():
        """Forward SSE stream from model API to Frontend"""
        try:
            async with client.stream('POST',
                api_url,
                json=request,
                headers=headers,
                follow_redirects=True
            ) as model_response:
                if model_response.status_code != 200:
                    logger.error(f"[Model Proxy] {model.display_name} returned {model_response.status_code}")
                    error_detail = await model_response.aread()
                    raise HTTPException(
                        status_code=model_response.status_code,
                        detail=f"Model API error: {error_detail.decode()}"
                    )

                async for chunk in model_response.aiter_bytes():
                    yield chunk
        except HTTPException:
            raise
        except httpx.RequestError as e:
            logger.error(f"[Model Proxy] Connection error to {model.display_name}: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to model API: {str(e)}"
            )
        except Exception as e:
            logger.error(f"[Model Proxy] Stream error: {e}")
            raise
        finally:
            await client.aclose()

    return StreamingResponse(
        forward_stream(),
        media_type="text/event-stream;charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*"
        }
    )

def _prepare_model_headers(model: LLMModel, api_key: str, request: dict) -> dict:
    """Prepare headers based on model type"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    if model.model_type == LLMModelType.OPENAI:
        headers["Authorization"] = f"Bearer {api_key}"
    elif model.model_type == LLMModelType.ANTHROPIC:
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = model.api_version or "2023-06-01"
    elif model.model_type == LLMModelType.IAS:
        # For IAS type, use the original authorization from request if available
        auth_header = request.get("authorization", "")
        if auth_header and auth_header.startswith("Bearer "):
            headers["Authorization"] = auth_header
        else:
            # Fallback to using API key as app key
            headers["Authorization"] = f"Bearer {api_key}"
        headers["X-APP-KEY"] = api_key
    else:  # CUSTOM
        # Use custom headers if configured
        headers["Authorization"] = f"Bearer {api_key}"
        if model.custom_headers:
            headers.update(model.custom_headers)

    return headers

# Favorite endpoints
@app.post(f"{API_PREFIX}/messages/{{message_id}}/favorite", response_model=dict)
async def add_favorite(
    message_id: str,
    favorite_data: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """收藏消息"""
    # 验证消息存在
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # 检查是否已收藏
    existing_favorite = db.query(MessageFavorite).filter(
        MessageFavorite.user_id == current_user.id,
        MessageFavorite.message_id == message_id
    ).first()
    if existing_favorite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message already favorited"
        )

    # 创建收藏
    favorite = MessageFavorite(
        user_id=current_user.id,
        message_id=message_id,
        session_id=message.session_id,
        note=favorite_data.note
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return {
        "id": favorite.id,
        "messageId": message_id,
        "createdAt": favorite.created_at.isoformat()
    }

@app.delete(f"{API_PREFIX}/messages/{{message_id}}/favorite")
async def remove_favorite(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消收藏消息"""
    # 查找收藏
    favorite = db.query(MessageFavorite).filter(
        MessageFavorite.user_id == current_user.id,
        MessageFavorite.message_id == message_id
    ).first()
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )

    # 删除收藏
    db.delete(favorite)
    db.commit()

    return {"message": "取消收藏成功"}

@app.get(f"{API_PREFIX}/favorites", response_model=dict)
async def get_favorites(
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """获取收藏列表"""
    # 查询收藏
    query = db.query(MessageFavorite).filter(
        MessageFavorite.user_id == current_user.id
    ).order_by(MessageFavorite.created_at.desc())

    total = query.count()
    favorites = query.limit(limit).offset(offset).all()

    # 构建响应
    favorite_responses = []
    for fav in favorites:
        # 获取关联的消息和会话
        message = db.query(Message).filter(Message.id == fav.message_id).first()
        session = db.query(Session).filter(Session.id == fav.session_id).first()

        if message and session:
            favorite_responses.append({
                "id": fav.id,
                "message": {
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "timestamp": message.timestamp
                },
                "session": {
                    "id": session.id,
                    "title": session.title,
                    "last_updated": session.last_updated,
                    "user_id": session.user_id
                },
                "note": fav.note,
                "createdAt": fav.created_at
            })

    return {
        "favorites": favorite_responses,
        "total": total
    }

@app.get(f"{API_PREFIX}/messages/{{message_id}}/favorite-status", response_model=dict)
async def get_favorite_status(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """检查消息收藏状态"""
    # 查找收藏
    favorite = db.query(MessageFavorite).filter(
        MessageFavorite.user_id == current_user.id,
        MessageFavorite.message_id == message_id
    ).first()

    return {
        "is_favorited": favorite is not None,
        "favorite_id": favorite.id if favorite else None
    }

# Model management endpoints
@app.get(f"{API_PREFIX}/models/active", response_model=dict)
async def get_active_models(
    db: Session = Depends(get_db)
):
    """获取所有启用的模型（公开）"""
    models = get_active_llm_models(db)

    # 构建响应，不返回 API Key
    model_responses = []
    for m in models:
        model_responses.append({
            "id": m.id,
            "name": m.name,
            "display_name": m.display_name,
            "model_type": m.model_type.value,
            "api_url": m.api_url,
            "api_version": m.api_version,
            "description": m.description,
            "is_active": m.is_active,
            "max_tokens": m.max_tokens,
            "temperature": m.temperature / 100.0,  # 转换回浮点数
            "stream_supported": m.stream_supported,
            "created_at": m.created_at.isoformat()
        })

    return {
        "models": model_responses,
        "total": len(model_responses)
    }

@app.get(f"{API_PREFIX}/admin/models", response_model=dict)
async def list_models(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """列出所有模型（管理员）- 包含 API Key"""
    models = list_llm_models(db, skip, limit)

    model_responses = []
    for m in models:
        model_responses.append({
            "id": m.id,
            "name": m.name,
            "display_name": m.display_name,
            "model_type": m.model_type.value,
            "api_url": m.api_url,
            "api_key": m.api_key,  # 返回 API Key 给管理员
            "api_version": m.api_version,
            "description": m.description,
            "is_active": m.is_active,
            "max_tokens": m.max_tokens,
            "temperature": m.temperature / 100.0,
            "stream_supported": m.stream_supported,
            "created_at": m.created_at.isoformat()
        })

    return {
        "models": model_responses,
        "total": len(model_responses)
    }

@app.get(f"{API_PREFIX}/admin/models/{{model_id}}", response_model=dict)
async def get_model_detail(
    model_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取特定模型详情（管理员）- 包含 API Key"""
    model = get_llm_model(db, model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    return {
        "id": model.id,
        "name": model.name,
        "display_name": model.display_name,
        "model_type": model.model_type.value,
        "api_url": model.api_url,
        "api_key": model.api_key,  # 返回 API Key 给管理员
        "api_version": model.api_version,
        "description": model.description,
        "is_active": model.is_active,
        "max_tokens": model.max_tokens,
        "temperature": model.temperature / 100.0,
        "stream_supported": model.stream_supported,
        "created_at": model.created_at.isoformat()
    }

@app.post(f"{API_PREFIX}/admin/models", response_model=dict)
async def create_model(
    model_data: LLMModelCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """创建新模型（管理员）"""
    try:
        model = create_llm_model(db, model_data, current_user.id)
        return {
            "id": model.id,
            "name": model.name,
            "display_name": model.display_name,
            "model_type": model.model_type.value,
            "api_url": model.api_url,
            "api_key": model.api_key,
            "is_active": model.is_active,
            "created_at": model.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create model: {str(e)}"
        )

@app.put(f"{API_PREFIX}/admin/models/{{model_id}}", response_model=dict)
async def update_model(
    model_id: str,
    model_data: LLMModelUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """更新模型（管理员）"""
    try:
        model = update_llm_model(db, model_id, model_data)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        return {
            "id": model.id,
            "name": model.name,
            "display_name": model.display_name,
            "model_type": model.model_type.value,
            "api_url": model.api_url,
            "api_key": model.api_key,
            "is_active": model.is_active,
            "updated_at": model.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update model: {str(e)}"
        )

@app.delete(f"{API_PREFIX}/admin/models/{{model_id}}")
async def delete_model(
    model_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """删除模型（管理员）"""
    try:
        success = delete_llm_model(db, model_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        return {"message": "Model deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete model: {str(e)}"
        )

# ==================== Document Processing Functions ====================

# Global RAG processor instance (lazy loading)
_document_processor: Optional[DocumentProcessor] = None

def get_document_processor() -> DocumentProcessor:
    """获取文档处理器实例（单例模式）"""
    global _document_processor
    if _document_processor is None:
        _document_processor = DocumentProcessor()
    return _document_processor

async def process_document_background(
    doc_id: str,
    file_path: str,
    kb_id: str,
    user_id: str,
    max_retries: int = 3
):
    """
    后台处理文档：解析、切片、向量化、存储到 ChromaDB（改进版）

    Args:
        doc_id: 文档 ID
        file_path: 文件路径
        kb_id: 知识库 ID
        user_id: 用户 ID
        max_retries: 最大重试次数（默认3次）

    改进：
    - 添加重试机制
    - 详细的日志记录
    - 更好的错误处理
    """
    processor = get_document_processor()

    # 重试循环
    for attempt in range(1, max_retries + 1):
        db_session = None
        try:
            logger.info(f"{'='*60}")
            logger.info(f"[文档处理] 尝试 {attempt}/{max_retries}: 处理文档 {doc_id}")
            logger.info(f"  文件路径: {file_path}")
            logger.info(f"  知识库ID: {kb_id}")
            logger.info(f"  用户ID: {user_id}")

            # 创建新的数据库会话
            db_session = SessionLocal()

            # 1. 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"  ❌ 文件不存在: {file_path}")
                doc = db_session.query(Document).filter(Document.id == doc_id).first()
                if doc:
                    doc.upload_status = "error"
                    doc.error_message = f"文件不存在: {file_path}"
                    db_session.commit()
                return

            file_size = os.path.getsize(file_path)
            logger.info(f"  ✅ 文件存在: {file_size} 字节")

            # 2. 更新状态为处理中
            doc = db_session.query(Document).filter(Document.id == doc_id).first()
            if not doc:
                logger.error(f"  ❌ 文档记录不存在: {doc_id}")
                return

            doc.upload_status = "processing"
            db_session.commit()
            logger.info(f"  ✅ 状态已更新: processing")

            # 3. 调用文档处理器
            logger.info(f"  🔄 开始分块和向量化...")
            result = await processor.process_document(
                file_path=file_path,
                knowledge_base_id=kb_id,
                user_id=user_id,
                filename=Path(file_path).name,
                document_id=doc_id
            )

            logger.info(f"  ✅ 处理完成: {result}")

            # 4. 更新数据库状态 - 简化逻辑
            if result.get("status") == "completed":
                chunk_count = result.get("chunk_count", 0)
            elif isinstance(result, list):
                chunk_count = len(result)
            else:
                chunk_count = 0

            doc.upload_status = "completed"
            doc.chunk_count = chunk_count
            doc.processed_at = func.now()
            doc.error_message = None
            db_session.commit()

            logger.info(f"{'='*60}")
            logger.info(f"✅ [文档处理] 文档 {doc_id} 处理完成")
            logger.info(f"   Chunks: {chunk_count}")
            logger.info(f"{'='*60}")

            # ✅ 修复：成功后清理临时文件
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"✅ [文档处理] 已清理临时文件: {file_path}")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️  [文档处理] 清理临时文件失败: {cleanup_error}")

            # 成功后退出重试循环
            return

        except Exception as e:
            logger.error(f"  ❌ 尝试 {attempt} 失败: {e}", exc_info=True)

            # 最后一次尝试失败后，更新为错误状态
            if attempt == max_retries:
                logger.error(f"{'='*60}")
                logger.error(f"❌ [文档处理] 文档 {doc_id} 处理失败（已重试{max_retries}次）")
                logger.error(f"   错误: {e}")
                logger.error(f"{'='*60}")

                if db_session:
                    try:
                        doc = db_session.query(Document).filter(Document.id == doc_id).first()
                        if doc:
                            doc.upload_status = "error"
                            doc.error_message = f"处理失败（重试{max_retries}次后）: {str(e)}"
                            db_session.commit()
                    except Exception as commit_error:
                        logger.error(f"  ❌ 更新错误状态失败: {commit_error}")
            else:
                # 还有重试机会，继续循环
                wait_time = attempt * 2
                logger.warning(f"  ⏳ {wait_time}秒后重试...")
                await asyncio.sleep(wait_time)

        finally:
            # ✅ 修复：确保在任何情况下都清理数据库连接和临时文件
            if db_session:
                try:
                    db_session.close()
                except:
                    pass

            # ✅ 修复：确保临时文件被清理（仅在所有重试都失败后）
            if attempt == max_retries and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"✅ [文档处理] 已清理临时文件（重试失败后）: {file_path}")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️  [文档处理] 清理临时文件失败: {cleanup_error}")

# ==================== Knowledge Base APIs ====================

@app.get(API_PREFIX + "/knowledge/groups", response_model=List[KnowledgeGroupResponse])
async def get_knowledge_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的知识库分组列表"""
    groups = db.query(KnowledgeGroup).filter(
        KnowledgeGroup.user_id == current_user.id
    ).order_by(KnowledgeGroup.created_at.desc()).all()
    return [KnowledgeGroupResponse.from_orm(g) for g in groups]

@app.post(API_PREFIX + "/knowledge/groups", response_model=KnowledgeGroupResponse)
async def create_knowledge_group(
    group_data: KnowledgeGroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建知识库分组"""
    # 检查名称是否重复
    existing = db.query(KnowledgeGroup).filter(
        KnowledgeGroup.user_id == current_user.id,
        KnowledgeGroup.name == group_data.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="分组名称已存在")

    group = KnowledgeGroup(
        name=group_data.name,
        description=group_data.description,
        user_id=current_user.id
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return KnowledgeGroupResponse.from_orm(group)

@app.delete(API_PREFIX + "/knowledge/groups/{group_id}")
async def delete_knowledge_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除知识库分组（及其所有知识库）"""
    group = db.query(KnowledgeGroup).filter(
        KnowledgeGroup.id == group_id,
        KnowledgeGroup.user_id == current_user.id
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    db.delete(group)
    db.commit()
    return {"message": "分组已删除"}

@app.get(API_PREFIX + "/knowledge/bases", response_model=List[KnowledgeBaseResponse])
async def get_knowledge_bases(
    group_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取知识库列表"""
    query = db.query(KnowledgeBase).filter(
        KnowledgeBase.user_id == current_user.id
    )

    if group_id:
        query = query.filter(KnowledgeBase.group_id == group_id)

    bases = query.order_by(KnowledgeBase.created_at.desc()).all()

    # 添加文档计数
    result = []
    for base in bases:
        base_dict = KnowledgeBaseResponse.from_orm(base).dict()
        doc_count = db.query(Document).filter(
            Document.knowledge_base_id == base.id,
            Document.upload_status == "completed"
        ).count()
        base_dict["document_count"] = doc_count
        result.append(KnowledgeBaseResponse(**base_dict))

    return result

@app.post(API_PREFIX + "/knowledge/bases", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    base_data: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建知识库"""
    # 如果指定了 group_id，验证存在且属于当前用户
    if base_data.group_id:
        group = db.query(KnowledgeGroup).filter(
            KnowledgeGroup.id == base_data.group_id,
            KnowledgeGroup.user_id == current_user.id
        ).first()
        if not group:
            raise HTTPException(status_code=404, detail="分组不存在")

    # 检查名称是否重复（在同一分组下或全局）
    existing_query = db.query(KnowledgeBase).filter(
        KnowledgeBase.user_id == current_user.id,
        KnowledgeBase.name == base_data.name
    )
    # 如果指定了分组，只在同一分组内检查重复
    if base_data.group_id:
        existing_query = existing_query.filter(KnowledgeBase.group_id == base_data.group_id)
    else:
        # 如果没有分组，检查其他无分组的知识库是否有重名
        existing_query = existing_query.filter(KnowledgeBase.group_id == None)

    existing = existing_query.first()
    if existing:
        raise HTTPException(status_code=400, detail="知识库名称已存在")

    base = KnowledgeBase(
        group_id=base_data.group_id,  # 可以为 None
        user_id=current_user.id,
        name=base_data.name,
        description=base_data.description,
        embedding_model=base_data.embedding_model,
        chunk_size=base_data.chunk_size,
        chunk_overlap=base_data.chunk_overlap
    )
    db.add(base)
    db.commit()
    db.refresh(base)
    return KnowledgeBaseResponse.from_orm(base)

@app.get(API_PREFIX + "/knowledge/bases/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取知识库详情"""
    base = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.user_id == current_user.id
    ).first()
    if not base:
        raise HTTPException(status_code=404, detail="知识库不存在")

    response = KnowledgeBaseResponse.from_orm(base).dict()
    doc_count = db.query(Document).filter(
        Document.knowledge_base_id == base.id,
        Document.upload_status == "completed"
    ).count()
    response["document_count"] = doc_count
    return KnowledgeBaseResponse(**response)

@app.delete(API_PREFIX + "/knowledge/bases/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除知识库（及其所有文档）"""
    base = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.user_id == current_user.id
    ).first()
    if not base:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 先清理 ChromaDB 向量
    try:
        processor = DocumentProcessor(rag_config)
        await processor.delete_knowledge_base(kb_id)
        logger.info(f"已清理知识库 {kb_id} 的 ChromaDB 向量")
    except Exception as e:
        logger.error(f"清理 ChromaDB 向量失败: {e}")
        # 继续删除 MySQL 记录，不阻止操作

    # 再删除 MySQL 记录
    db.delete(base)
    db.commit()
    return {"message": "知识库已删除"}

@app.get(API_PREFIX + "/knowledge/bases/{kb_id}/documents", response_model=List[DocumentResponse])
async def get_documents(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取知识库的文档列表"""
    # 验证知识库存在且属于当前用户
    base = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.user_id == current_user.id
    ).first()
    if not base:
        raise HTTPException(status_code=404, detail="知识库不存在")

    docs = db.query(Document).filter(
        Document.knowledge_base_id == kb_id
    ).order_by(Document.created_at.desc()).all()
    return [DocumentResponse.from_orm(d) for d in docs]

@app.get(API_PREFIX + "/knowledge/bases/{kb_id}/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    kb_id: str,
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取文档详情"""
    # 验证知识库存在且属于当前用户
    base = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.user_id == current_user.id
    ).first()
    if not base:
        raise HTTPException(status_code=404, detail="知识库不存在")

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.knowledge_base_id == kb_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    return DocumentResponse.from_orm(doc)

@app.get(API_PREFIX + "/knowledge/bases/{kb_id}/documents/{doc_id}/chunks")
async def get_document_chunks(
    kb_id: str,
    doc_id: str,
    offset: int = 0,
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取文档切片详情（支持分页）"""
    # 验证知识库存在且属于当前用户
    base = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.user_id == current_user.id
    ).first()
    if not base:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 验证文档存在
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.knowledge_base_id == kb_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 从 ChromaDB 获取切片
    try:
        rag_config = get_rag_config()
        collection = rag_config.get_or_create_collection(KNOWLEDGE_COLLECTION)

        # 查询该文档的所有切片
        results = collection.get(
            where={"document_id": doc_id}
        )

        chunks = []
        for i, (text, metadata) in enumerate(zip(results.get('documents', []), results.get('metadatas', []))):
            chunks.append({
                "id": f"{doc_id}_chunk_{i}",
                "chunk_index": metadata.get("chunk_index", i),
                "content": text,
                "metadata": metadata
            })

        # 应用分页
        total_count = len(chunks)
        start_idx = offset
        end_idx = offset + limit if limit else len(chunks)

        # 确保索引在有效范围内
        if start_idx >= total_count:
            paginated_chunks = []
        else:
            paginated_chunks = chunks[start_idx:end_idx]

        # ✅ 返回对象而不是数组，与 app/rag/router.py 保持一致
        return {
            "document_id": doc_id,
            "filename": doc.filename,
            "chunks": paginated_chunks,
            "total_count": total_count,
            "returned_count": len(paginated_chunks),
            "offset": offset,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"获取文档切片失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取切片失败: {str(e)}")


@app.get(API_PREFIX + "/knowledge/search")
async def search_knowledge(
    query: str,
    knowledge_base_ids: Optional[str] = None,  # 改为可选参数
    top_k: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """知识检索"""
    if not query:
        raise HTTPException(status_code=400, detail="查询内容不能为空")

    # 导入 RAG 配置
    from app.rag.config import get_rag_config
    rag_config = get_rag_config()

    # 如果没有指定知识库，使用用户的所有知识库
    if knowledge_base_ids:
        # 解析知识库 ID 列表
        try:
            kb_ids = knowledge_base_ids.split(',')
        except:
            raise HTTPException(status_code=400, detail="知识库 ID 格式错误")

        # 验证所有知识库都属于当前用户
        bases = db.query(KnowledgeBase).filter(
            KnowledgeBase.id.in_(kb_ids),
            KnowledgeBase.user_id == current_user.id
        ).all()
        if len(bases) != len(kb_ids):
            raise HTTPException(status_code=403, detail="无权访问某些知识库")
    else:
        # 获取用户的所有知识库
        bases = db.query(KnowledgeBase).filter(
            KnowledgeBase.user_id == current_user.id
        ).all()
        kb_ids = [kb.id for kb in bases]

    # 如果用户没有任何知识库，返回空结果
    if not kb_ids:
        return {
            "results": [],
            "query": query,
            "total": 0,
            "message": "暂无可搜索的知识库，请先创建知识库并上传文档"
        }

    try:
        # 使用 RAGRetriever 进行搜索（支持多知识库搜索）
        from app.rag.retriever import RAGRetriever
        retriever = RAGRetriever(rag_config)

        # 执行检索
        search_results = await retriever.search(
            query=query,
            knowledge_base_ids=kb_ids,
            user_id=current_user.id,
            top_k=top_k
        )

        # 格式化结果
        formatted_results = []
        for result in search_results:
            formatted_results.append({
                "id": result["id"],
                "content": result["content"],
                "metadata": result["metadata"],
                "similarity": round(result["similarity"], 3),
                "distance": round(result["distance"], 3)
            })

        return {"results": formatted_results, "query": query, "total": len(formatted_results)}
    except Exception as e:
        logger.error(f"知识检索失败: {e}")
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")


@app.delete(API_PREFIX + "/knowledge/bases/{kb_id}/documents/{doc_id}")
async def delete_document(
    kb_id: str,
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除文档"""
    # 验证知识库存在且属于当前用户
    base = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.user_id == current_user.id
    ).first()
    if not base:
        raise HTTPException(status_code=404, detail="知识库不存在")

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.knowledge_base_id == kb_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 先清理 ChromaDB 向量
    try:
        processor = DocumentProcessor(rag_config)
        await processor.delete_document(doc_id)
        logger.info(f"已清理文档 {doc_id} 的 ChromaDB 向量")
    except Exception as e:
        logger.error(f"清理 ChromaDB 向量失败: {e}")
        # 继续删除 MySQL 记录，不阻止操作

    # 再删除 MySQL 记录
    db.delete(doc)
    db.commit()
    return {"message": "文档已删除"}

@app.post(API_PREFIX + "/knowledge/bases/{kb_id}/documents", response_model=DocumentResponse)
async def upload_document(
    kb_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sync: bool = False,  # 新增：是否同步处理
    chunk_size: int = 500,  # 新增：分块大小
    chunk_overlap: int = 50,  # 新增：分块重叠
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传文档到知识库（支持同步/异步处理）

    流程：
    1. 验证知识库权限
    2. 保存文件到临时目录
    3. 创建文档记录（状态=pending）
    4. 同步模式：立即处理文档；异步模式：启动后台任务
    5. 返回响应

    参数：
    - sync: true=同步处理（立即完成），false=异步处理（后台任务）
    - chunk_size: 文本分块大小（默认500字符）
    - chunk_overlap: 分块重叠大小（默认50字符）
    """
    temp_file_path = None
    try:
        # 1. 验证知识库存在且属于当前用户
        kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id
        ).first()

        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 2. 保存文件到临时目录
        temp_dir = Path("uploads/documents")
        temp_dir.mkdir(parents=True, exist_ok=True)

        file_extension = Path(file.filename).suffix
        temp_file_path = temp_dir / f"{uuid.uuid4()}{file_extension}"

        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"[文档上传] 文件已保存到: {temp_file_path} (大小: {len(content)} 字节)")

        # 3. 创建文档记录（状态：pending）
        document = Document(
            knowledge_base_id=kb_id,
            filename=file.filename,
            file_type=file.content_type or "application/octet-stream",
            file_size=len(content),
            upload_status="pending"
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        logger.info(f"[文档上传] 文档记录已创建: {document.id}")

        # 4. 根据sync参数选择处理方式
        if sync:
            # 同步处理模式（立即完成）
            logger.info(f"[文档上传] 使用同步处理模式")
            try:
                processor = get_document_processor()

                # 直接处理文档
                result = await processor.process_document(
                    file_path=str(temp_file_path),
                    knowledge_base_id=kb_id,
                    user_id=current_user.id,
                    filename=file.filename,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    document_id=document.id
                )

                # ✅ 修复：从 result dict 中正确获取 chunk_count
                if result.get("status") == "completed":
                    document.upload_status = "completed"
                    document.chunk_count = result.get("chunk_count", 0)
                    db.commit()
                    logger.info(f"✅ [文档上传] 同步处理成功: {result.get('chunk_count', 0)} 个chunks")
                else:
                    document.upload_status = "error"
                    document.error_message = result.get("error", "未知错误")
                    db.commit()
                    logger.error(f"❌ [文档上传] 同步处理失败: {document.error_message}")
                    raise HTTPException(status_code=500, detail=f"文档处理失败: {document.error_message}")
            except HTTPException:
                raise
            except Exception as e:
                # 同步处理失败
                document.upload_status = "error"
                document.error_message = str(e)
                db.commit()
                logger.error(f"❌ [文档上传] 同步处理失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")
            finally:
                # ✅ 修复：同步模式完成后清理临时文件
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                        logger.info(f"[文档上传] 已清理临时文件: {temp_file_path}")
                    except Exception as cleanup_error:
                        logger.warning(f"[文档上传] 清理临时文件失败: {cleanup_error}")
        else:
            # 异步处理模式（原有逻辑）
            logger.info(f"[文档上传] 使用异步处理模式")
            background_tasks.add_task(
                process_document_background,
                document.id,
                str(temp_file_path),
                kb_id,
                current_user.id
            )
            logger.info(f"[文档上传] 后台处理任务已启动: {document.id}")
            # 注意：异步模式下，临时文件由 process_document_background 负责清理

        return document

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[文档上传] 失败: {e}", exc_info=True)

        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# Detailed system health check
@app.get(f"{API_PREFIX}/system/health")
async def system_health_check(current_user: User = Depends(get_current_user)):
    """
    系统健康检查（详细版）

    检查项目：
    - 数据库连接
    - ChromaDB连接和collection状态
    - BGE模型加载状态
    """
    health = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "components": {}
    }

    # 1. 检查数据库
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health["components"]["database"] = {"status": "healthy", "message": "数据库连接正常"}
    except Exception as e:
        health["components"]["database"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"

    # 2. 检查ChromaDB
    try:
        rag_config = get_rag_config()

        # 检查连接
        if not rag_config.health_check():
            health["components"]["chromadb"] = {"status": "down", "error": "ChromaDB连接失败"}
            health["status"] = "unhealthy"
        else:
            # 检查collection健康状态
            try:
                collection = rag_config.get_or_create_collection(KNOWLEDGE_COLLECTION)
                count = collection.count()
                health["components"]["chromadb"] = {
                    "status": "healthy",
                    "message": "ChromaDB连接正常",
                    "collection": KNOWLEDGE_COLLECTION,
                    "vector_count": count
                }
            except Exception as e:
                health["components"]["chromadb"] = {
                    "status": "degraded",
                    "message": "ChromaDB连接正常，但collection有问题",
                    "error": str(e)
                }
                health["status"] = "degraded"

    except Exception as e:
        health["components"]["chromadb"] = {"status": "down", "error": str(e)}
        health["status"] = "unhealthy"

    # 3. 检查BGE模型
    try:
        rag_config = get_rag_config()
        model = rag_config.embedding_model
        dimension = model.get_sentence_embedding_dimension()
        health["components"]["embedding_model"] = {
            "status": "healthy",
            "model_name": rag_config.embedding_model_name,
            "dimension": dimension
        }
    except Exception as e:
        health["components"]["embedding_model"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"

    return health

# Root
@app.get("/")
async def root():
    return {"name": APP_NAME, "version": "1.0.0", "docs": "/docs"}

# Create default admin user
def create_default_admin():
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = get_user_by_username(db, "admin")
        if not admin:
            logger.info("Creating default admin user...")
            hashed_password = get_password_hash("pwd123")
            admin = User(
                username="admin",
                password_hash=hashed_password,
                role=UserRole.ADMIN
            )
            db.add(admin)
            db.commit()
            logger.info("Default admin created: admin / admin123")
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
    finally:
        db.close()

# Create default admin on startup
create_default_admin()

# Startup event: 初始化和检查系统组件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化和健康检查"""
    logger.info("="*60)
    logger.info("系统初始化")
    logger.info("="*60)

    # 1. 检查数据库连接
    logger.info("1. 检查数据库连接...")
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("   ✅ 数据库连接正常")
    except Exception as e:
        logger.error(f"   ❌ 数据库连接失败: {e}")

    # 2. 检查ChromaDB并自动修复
    logger.info("2. 检查ChromaDB...")
    try:
        rag_config = get_rag_config()

        if not rag_config.health_check():
            logger.error("   ❌ ChromaDB连接失败")
            logger.error("   请启动ChromaDB:")
            logger.error("   docker run -d -p 8002:8000 --name bright-chat-chromadb chromadb/chroma:latest")
        else:
            logger.info("   ✅ ChromaDB连接正常")

            # 检查并修复knowledge_chunks collection
            logger.info("3. 检查knowledge_chunks collection...")
            try:
                collection = rag_config.get_or_create_collection(KNOWLEDGE_COLLECTION)
                count = collection.count()
                logger.info(f"   ✅ Collection健康 ({count} 个向量)")
            except Exception as e:
                logger.warning(f"   ⚠️  Collection检查失败: {e}")
                logger.info("   尝试自动修复...")

                try:
                    # 尝试重建collection
                    rag_config.chroma_client.delete_collection(KNOWLEDGE_COLLECTION)
                    rag_config.chroma_client.create_collection(KNOWLEDGE_COLLECTION)
                    logger.info("   ✅ Collection重建成功")
                except Exception as repair_error:
                    logger.error(f"   ❌ Collection修复失败: {repair_error}")

    except Exception as e:
        logger.error(f"   ❌ ChromaDB初始化失败: {e}")

    # 3. 检查BGE模型（可选，失败不影响启动）
    logger.info("4. 检查BGE模型...")
    try:
        # 预加载模型（首次加载会较慢）
        rag_config = get_rag_config()
        model = rag_config.embedding_model
        dimension = model.get_sentence_embedding_dimension()
        logger.info(f"   ✅ BGE模型加载成功 (维度: {dimension})")
    except Exception as e:
        logger.warning(f"   ⚠️  BGE模型加载失败: {e}")
        logger.warning("   向量化功能将不可用，但其他功能正常")

    logger.info("="*60)
    logger.info("系统初始化完成")
    logger.info("="*60)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    logger.info("系统正在关闭...")
    # 这里可以添加清理逻辑
    logger.info("系统已关闭")

if __name__ == "__main__":
    import uvicorn
    print(f"Starting {APP_NAME}...")
    print(f"Server running on: http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"API Documentation: http://localhost:{SERVER_PORT}/docs")
    uvicorn.run(
        "minimal_api:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=False,
        log_level="info"
    )