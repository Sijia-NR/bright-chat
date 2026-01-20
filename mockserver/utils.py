"""
工具函数
"""
import uuid
import json
import random
import time
from typing import Dict, Any, Optional
from config import Config

def generate_trace_id() -> str:
    """生成全链路追踪ID"""
    return f"trace-{uuid.uuid4().hex}"

def generate_request_id() -> str:
    """生成请求ID"""
    return f"{uuid.uuid4()}"

def generate_delay() -> int:
    """生成随机延迟"""
    return random.randint(Config.RESPONSE_DELAY_MIN, Config.RESPONSE_DELAY_MAX)

def validate_auth_header(authorization: Optional[str]) -> bool:
    """验证Authorization头"""
    if not authorization:
        return False
    return authorization.startswith("Bearer ") or authorization == Config.DEFAULT_APP_KEY

def create_error_response(code: str, message: str = None, trace_id: str = None) -> Dict[str, Any]:
    """创建错误响应"""
    if message is None:
        message = Config.ERROR_MESSAGES.get(code, "未知错误")

    response = {
        "code": code,
        "success": "false",
        "message": f"失败！错误原因：{message}",
        "data": {
            "traceId": trace_id or generate_trace_id(),
            "appId": Config.APP_ID,
            "globalTraceId": generate_trace_id(),
            "answer": None,
            "messageId": None,
            "isEnd": None
        }
    }
    return response

def validate_chat_request(request: Dict[str, Any]) -> tuple[bool, str]:
    """验证聊天请求"""
    # 检查必填字段
    if "model" not in request:
        return False, "200003"
    if "messages" not in request or not request["messages"]:
        return False, "200003"

    # 检查模型是否支持
    if request["model"] not in Config.SUPPORTED_MODELS:
        return False, "200005"

    # 检查messages格式
    messages = request["messages"]
    if not isinstance(messages, list):
        return False, "200002"

    # 检查最后一个消息的角色
    if messages and messages[-1].get("role") != "user":
        return False, "200002"

    return True, ""

def stream_text(text: str, delay: int = Config.STREAM_DELAY):
    """流式生成文本"""
    for char in text:
        yield char
        time.sleep(delay / 1000.0)