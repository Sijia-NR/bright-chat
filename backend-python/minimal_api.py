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
from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.responses import StreamingResponse
import asyncio
import json
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Enum as SQLEnum, Text, ForeignKey, UniqueConstraint, Integer, JSON
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

# Configure logging - restore INFO level for detailed logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Restore httpx and uvicorn access logs to INFO
logging.getLogger("httpx").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)

# Database setup
DATABASE_URL = "mysql+pymysql://root:123456@47.116.218.206:13306/bright_chat"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
def hash_password(password: str) -> str:
    """Simple SHA256 hash for demo purposes"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

# JWT settings
SECRET_KEY = "your-super-secret-jwt-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

# App settings
APP_NAME = "Bright-Chat API"
API_PREFIX = "/api/v1"
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 18080

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

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.USER

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

class SessionResponse(BaseModel):
    id: str
    title: str
    last_updated: datetime
    user_id: str

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [UserResponse.from_orm(user) for user in users]

@app.post(f"{API_PREFIX}/admin/users", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if username already exists
    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Create user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        role=user_data.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return UserResponse.from_orm(db_user)

@app.put(f"{API_PREFIX}/admin/users/{{user_id}}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if username already exists for different user
    if user_data.username != user.username:
        existing_user = get_user_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

    # Update user fields
    user.username = user_data.username
    user.role = user_data.role
    # Note: We don't update password through this endpoint for security
    # Password should be updated through a dedicated endpoint

    db.commit()
    db.refresh(user)
    return UserResponse.from_orm(user)

@app.delete(f"{API_PREFIX}/admin/users/{{user_id}}")
async def delete_user(user_id: str, db: Session = Depends(get_db)):
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
        user_id=session_data.user_id
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return SessionResponse.from_orm(db_session)

@app.get(f"{API_PREFIX}/sessions/{{session_id}}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp.asc(), Message.id.asc()).all()
    return [MessageResponse.from_orm(message) for message in messages]

@app.post(f"{API_PREFIX}/sessions/{{session_id}}/messages")
async def save_messages(session_id: str, message_data: MessageCreate, db: Session = Depends(get_db)):
    # Validate session exists
    session = db.query(Session).filter(Session.id == session_id).first()
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
async def delete_session(session_id: str, db: Session = Depends(get_db)):
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

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

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