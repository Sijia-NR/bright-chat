from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class ChatRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class IASChatMessage(BaseModel):
    role: ChatRole
    content: str


class IASChatRequest(BaseModel):
    model: str = Field(..., description="Model name")
    messages: List[IASChatMessage] = Field(..., description="List of messages")
    stream: bool = Field(True, description="Enable streaming response")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature for sampling")


class IASChoice(BaseModel):
    index: int
    finish_reason: Optional[str]
    delta: Optional[Dict[str, Any]]
    message: Optional[IASChatMessage]


class IASChatResponse(BaseModel):
    id: str
    app_id: str
    global_trace_id: str
    object: str
    created: int
    choices: List[IASChoice]
    usage: Optional[Dict[str, float]] = None


class IASProxyRequest(BaseModel):
    model: str
    messages: List[IASChatMessage]
    stream: bool = True
    temperature: Optional[float] = None


class IASProxyResponse(BaseModel):
    status: str
    data: Optional[IASChatResponse] = None
    error: Optional[str] = None