"""
数据模型定义
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from enum import Enum

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class ContentType(str, Enum):
    TEXT = "text"
    IMAGE_URL = "image_url"
    IMAGE_BASE64 = "image_base64"

class Message(BaseModel):
    role: Role
    content: Union[str, List[Dict[str, Any]]]

class Function(BaseModel):
    type: str = "function"
    function: Dict[str, Any]

class ToolChoice(BaseModel):
    type: str
    function: Dict[str, str]

class ChatRequest(BaseModel):
    model: str = Field(..., description="要使用的模型ID")
    messages: List[Message] = Field(..., description="对话历史")
    modelVersion: Optional[str] = None
    stream: Optional[bool] = False
    temperature: Optional[float] = Field(0.95, gt=0, le=1.0)
    top_p: Optional[float] = Field(0.7, ge=0, le=1.0)
    presence_penalty: Optional[float] = Field(0, ge=-2.0, le=2.0)
    tools: Optional[List[Function]] = None
    tool_choice: Optional[Union[str, ToolChoice]] = None
    parallel_tool_calls: Optional[bool] = False
    max_tokens: Optional[int] = None

class VisionData(BaseModel):
    image_name: str
    image_type: str
    image_data: str

class VisionRequest(BaseModel):
    data: List[VisionData]
    model: str
    modelVersion: Optional[str] = None
    traceId: Optional[str] = None
    success: Optional[bool] = True

class VisionInferenceResult(BaseModel):
    bbox: List[int]
    category: str
    score: float

class VisionDataResponse(BaseModel):
    image_name: str
    image_height: int
    image_width: int
    infer_results: List[VisionInferenceResult]

class MultimodalContent(BaseModel):
    type: ContentType
    text: Optional[str] = None
    image: Optional[str] = None

class MultimodalMessage(BaseModel):
    role: Role
    content: List[MultimodalContent]

class MultimodalRequest(BaseModel):
    model: str
    messages: List[MultimodalMessage]
    modelVersion: Optional[str] = None
    stream: Optional[bool] = False
    temperature: Optional[float] = Field(0.9, gt=0, lt=2)
    top_p: Optional[float] = Field(0.8, gt=0, le=1.0)
    presence_penalty: Optional[float] = Field(0, ge=-2.0, le=2.0)
    max_tokens: Optional[int] = None

class ChatChoice(BaseModel):
    index: int
    finish_reason: Optional[str] = None
    message: Optional[Dict[str, Any]] = None
    delta: Optional[Dict[str, Any]] = None

class Usage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    id: str
    appId: str
    globalTraceId: str
    object: str
    created: int
    choices: List[ChatChoice]
    usage: Optional[Usage] = None

class ErrorResponse(BaseModel):
    code: str = "100000"
    success: str = "false"
    message: str
    data: Optional[Dict[str, Any]] = None