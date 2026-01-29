"""
数字员工/Agent 相关数据模型
Digital Employee / Agent related data models
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, field_validator
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, func

from ..core.database import Base


# ==================== 常量定义 ====================

# Agent 类型
AGENT_TYPE_RAG = "rag"
AGENT_TYPE_TOOL = "tool"
AGENT_TYPE_CUSTOM = "custom"
ALLOWED_AGENT_TYPES = (AGENT_TYPE_RAG, AGENT_TYPE_TOOL, AGENT_TYPE_CUSTOM)

# Agent 执行状态
EXECUTION_STATUS_RUNNING = "running"
EXECUTION_STATUS_COMPLETED = "completed"
EXECUTION_STATUS_FAILED = "failed"
EXECUTION_STATUSES = (EXECUTION_STATUS_RUNNING, EXECUTION_STATUS_COMPLETED, EXECUTION_STATUS_FAILED)

# 工具分类
TOOL_CATEGORY_KNOWLEDGE = "knowledge"
TOOL_CATEGORY_CALCULATION = "calculation"
TOOL_CATEGORY_SEARCH = "search"
TOOL_CATEGORY_CODE = "code"
TOOL_CATEGORY_SYSTEM = "system"

# 验证常量
MAX_NAME_LENGTH = 255
MAX_QUERY_LENGTH = 2000
DEFAULT_AGENT_TYPE = AGENT_TYPE_TOOL

# 配置默认值
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_STEPS = 10
DEFAULT_TIMEOUT = 300
MIN_TEMPERATURE = 0
MAX_TEMPERATURE = 2
MIN_MAX_STEPS = 1
MAX_MAX_STEPS = 50


# ==================== SQLAlchemy 模型 ====================

class Agent(Base):
    """Agent 配置表"""
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    agent_type = Column(String(50), nullable=False)
    system_prompt = Column(Text, nullable=True)
    knowledge_base_ids = Column(JSON, nullable=True)
    tools = Column(JSON, nullable=True)
    config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


class AgentExecution(Base):
    """Agent 执行记录表"""
    __tablename__ = "agent_executions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)
    input_prompt = Column(Text, nullable=False)
    status = Column(String(50), default=EXECUTION_STATUS_RUNNING)
    steps = Column(Integer, default=0)
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_log = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=False, default=func.now())
    completed_at = Column(DateTime, nullable=True)


# ==================== 验证函数 ====================

def validate_not_empty(value: str, field_name: str) -> str:
    """验证字符串非空"""
    if not value or len(value.strip()) == 0:
        raise ValueError(f"{field_name}不能为空")
    if len(value) > MAX_NAME_LENGTH:
        raise ValueError(f"{field_name}不能超过{MAX_NAME_LENGTH}个字符")
    return value.strip()


def validate_agent_type(agent_type: str) -> str:
    """验证 Agent 类型"""
    if agent_type not in ALLOWED_AGENT_TYPES:
        raise ValueError(f"Agent 类型必须是以下之一: {list(ALLOWED_AGENT_TYPES)}")
    return agent_type


def validate_agent_config(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """验证并返回 Agent 配置"""
    if config is None:
        return get_default_agent_config()

    # 验证 temperature
    if "temperature" in config:
        temp = config["temperature"]
        if not isinstance(temp, (int, float)) or temp < MIN_TEMPERATURE or temp > MAX_TEMPERATURE:
            raise ValueError(f"temperature 必须在 {MIN_TEMPERATURE}-{MAX_TEMPERATURE} 之间")

    # 验证 max_steps
    if "max_steps" in config:
        steps = config["max_steps"]
        if not isinstance(steps, int) or steps < MIN_MAX_STEPS or steps > MAX_MAX_STEPS:
            raise ValueError(f"max_steps 必须在 {MIN_MAX_STEPS}-{MAX_MAX_STEPS} 之间")

    return config


def get_default_agent_config() -> Dict[str, Any]:
    """获取默认 Agent 配置"""
    return {
        "temperature": DEFAULT_TEMPERATURE,
        "max_steps": DEFAULT_MAX_STEPS,
        "timeout": DEFAULT_TIMEOUT
    }


# ==================== Pydantic 模型用于 API ====================

class AgentCreate(BaseModel):
    """创建 Agent 请求"""
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    agent_type: str = DEFAULT_AGENT_TYPE
    system_prompt: Optional[str] = None
    knowledge_base_ids: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_not_empty(v, "Agent 名称")

    @field_validator('agent_type')
    @classmethod
    def validate_agent_type_field(cls, v: str) -> str:
        return validate_agent_type(v)

    @field_validator('config')
    @classmethod
    def validate_config_field(cls, v: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return validate_agent_config(v)


class AgentUpdate(BaseModel):
    """更新 Agent 请求"""
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    knowledge_base_ids: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AgentResponse(BaseModel):
    """Agent 响应"""
    id: str
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    agent_type: str
    system_prompt: Optional[str] = None
    knowledge_base_ids: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None
    is_active: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentChatRequest(BaseModel):
    """Agent 聊天请求"""
    query: str
    session_id: Optional[str] = None
    stream: bool = True

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("查询内容不能为空")
        if len(v) > MAX_QUERY_LENGTH:
            raise ValueError(f"查询内容不能超过{MAX_QUERY_LENGTH}个字符")
        return v.strip()


class AgentExecutionResponse(BaseModel):
    """Agent 执行记录响应"""
    id: str
    agent_id: str
    user_id: str
    session_id: Optional[str] = None
    input_prompt: str
    status: str
    steps: int
    result: Optional[str] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgentExecutionCreate(BaseModel):
    """创建 Agent 执行记录（内部使用）"""
    agent_id: str
    user_id: str
    session_id: Optional[str] = None
    input_prompt: str


# ==================== Agent 工具定义 ====================

class AgentTool(BaseModel):
    """Agent 工具定义"""
    name: str
    display_name: str
    description: str
    category: str
    parameters: Dict[str, Any]


# 预定义工具列表
PREDEFINED_TOOLS = [
    AgentTool(
        name="knowledge_search",
        display_name="知识库检索",
        description="在知识库中搜索相关信息",
        category=TOOL_CATEGORY_KNOWLEDGE,
        parameters={
            "query": {"type": "string", "description": "搜索查询"},
            "knowledge_base_ids": {"type": "array", "description": "知识库 ID 列表"},
            "top_k": {"type": "integer", "default": 5, "description": "返回结果数量"}
        }
    ),
    AgentTool(
        name="calculator",
        display_name="计算器",
        description="执行数学计算",
        category=TOOL_CATEGORY_CALCULATION,
        parameters={
            "expression": {"type": "string", "description": "数学表达式"}
        }
    ),
    AgentTool(
        name="datetime",
        display_name="当前时间",
        description="获取当前日期和时间",
        category=TOOL_CATEGORY_SYSTEM,
        parameters={}
    ),
    AgentTool(
        name="code_executor",
        display_name="代码执行",
        description="安全执行 Python 代码（沙箱隔离）",
        category=TOOL_CATEGORY_SYSTEM,
        parameters={
            "code": {"type": "string", "description": "要执行的 Python 代码"},
            "timeout": {"type": "integer", "default": 30, "description": "超时时间（秒）"}
        }
    ),
    AgentTool(
        name="browser",
        display_name="浏览器",
        description="网页浏览、搜索、数据抓取（无头浏览器）",
        category=TOOL_CATEGORY_SEARCH,
        parameters={
            "action": {"type": "string", "description": "操作类型：navigate/search/scrape/screenshot/click/fill"},
            "url": {"type": "string", "description": "目标 URL"},
            "selector": {"type": "string", "description": "CSS 选择器"},
            "text": {"type": "string", "description": "文本内容"},
            "wait_time": {"type": "integer", "default": 3000, "description": "等待时间（毫秒）"}
        }
    ),
    AgentTool(
        name="file",
        display_name="文件操作",
        description="读写文件、列出目录",
        category=TOOL_CATEGORY_SYSTEM,
        parameters={
            "action": {"type": "string", "description": "操作类型：read/write/list/exists/delete"},
            "path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "文件内容（用于 write）"},
            "allowed_dirs": {"type": "array", "description": "允许访问的目录列表"}
        }
    ),
]
