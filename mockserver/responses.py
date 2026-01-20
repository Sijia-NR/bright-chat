"""
模拟响应生成器
"""
import json
import uuid
import time
import random
import logging
from typing import Dict, Any, List, Optional
from utils import generate_trace_id, generate_request_id, stream_text
from config import Config

logger = logging.getLogger(__name__)

class MockResponseGenerator:
    """模拟响应生成器"""

    def __init__(self):
        self.app_id = Config.APP_ID

    def generate_semantic_response(self, request: Dict[str, Any], is_stream: bool = False) -> Dict[str, Any]:
        """生成语义模型响应"""
        trace_id = generate_trace_id()
        request_id = generate_request_id()
        timestamp = int(time.time())

        logger.debug(f"[responses] 生成语义响应 - trace_id: {trace_id}, request_id: {request_id}")
        logger.debug(f"[responses] 响应模式: {'流式' if is_stream else '非流式'}")

        # 获取用户消息
        user_message = ""
        if request.get("messages"):
            for msg in reversed(request["messages"]):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break

        logger.debug(f"[responses] 用户消息内容: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")

        # 检测是否是代码相关的请求
        code_keywords = ["代码", "code", "函数", "function", "class", "python", "javascript", "java", "api", "示例", "example"]
        is_code_request = any(keyword in user_message.lower() for keyword in code_keywords)

        if is_code_request:
            matched_keywords = [kw for kw in code_keywords if kw in user_message.lower()]
            logger.info(f"[responses] 检测到代码请求 - 匹配关键词: {matched_keywords}")
        else:
            logger.debug(f"[responses] 普通对话请求")

        # 根据请求类型生成不同的回复
        try:
            if is_code_request:
                content = self._generate_code_response(user_message)
                logger.info(f"[responses] 代码响应生成成功 - 长度: {len(content)} 字符")
            else:
                content = self._generate_normal_response(user_message)
                logger.debug(f"[responses] 普通响应生成成功 - 长度: {len(content)} 字符")
        except Exception as e:
            logger.error(f"[responses] 响应生成失败: {str(e)}")
            logger.error(f"[responses] 响应生成失败位置: responses.py:generate_semantic_response")
            raise

        if is_stream:
            logger.info(f"[responses] 创建流式响应 - 内容长度: {len(content)}")
            # 流式响应
            return self._create_stream_response(request_id, trace_id, timestamp, content)
        else:
            logger.info(f"[responses] 创建非流式响应 - 内容长度: {len(content)}")
            # 非流式响应
            return self._create_non_stream_response(request_id, trace_id, timestamp, content)

    def _generate_code_response(self, user_message: str) -> str:
        """生成代码相关的响应"""
        # Python API 示例
        python_code = f"""根据你的请求："{user_message}"

这里是一个Python代码示例：

```python
# 用户认证API示例
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class UserLogin(BaseModel):
    username: str
    password: str

@app.post("/api/auth/login")
async def login(user_data: UserLogin):
    # 验证用户凭据
    if user_data.username == "admin" and user_data.password == "pwd123":
        return {{"status": "success"}}
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

这段代码实现了一个简单的用户认证API，使用了FastAPI框架。主要功能包括：
- 定义用户登录模型
- POST /api/auth/login 端点
- 用户凭据验证
- 错误处理"""

        # JavaScript/React 示例
        js_code = f"""关于："{user_message}"

这是一个JavaScript代码示例：

```javascript
// 聊天消息组件
function ChatMessage({{ message, user }}) {{
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {{
    if (message.role === 'assistant' && !message.content) {{
      setIsTyping(true);
      setTimeout(() => setIsTyping(false), 1000);
    }}
  }}, [message]);

  return (
    <div className="message">
      <div className="content">
        {{isTyping ? '正在输入...' : message.content}}
      </div>
    </div>
  );
}}
```

这个JavaScript组件实现了聊天消息的显示功能。"""

        # SQL 示例
        sql_code = f"""回答："{user_message}"

以下是一个数据库操作的SQL示例：

```sql
-- 创建用户表
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 查询用户
SELECT id, username, email FROM users WHERE is_active = TRUE;
```

这个SQL示例展示了基本的数据库操作。"""

        code_examples = [python_code, js_code, sql_code]
        return random.choice(code_examples)

    def _generate_normal_response(self, user_message: str) -> str:
        """生成普通响应"""
        mock_responses = [
            f"你好！我是BrightChat智能助手。\n\n我收到了你的消息：\"{user_message}\"\n\n这是一个模拟的语义模型回复。在实际应用中，这里会调用真实的AI模型生成回复。",
            f"感谢您的提问：\"{user_message}\"。\n\n作为BrightChat的语义模型，我理解您的问题并准备为您提供帮助。目前这是模拟环境，实际部署时会连接真实的AI服务。",
            f"我已经理解您的输入：\"{user_message}\"。\n\nBrightChat语义模型正在处理您的请求，在真实环境中，这里会显示AI模型的实际生成内容。",
        ]

        return random.choice(mock_responses)

    def generate_vision_response(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """生成视觉模型响应"""
        trace_id = generate_trace_id()
        request_id = generate_request_id()
        timestamp = int(time.time())

        # 模拟视觉识别结果
        infer_results = [
            {
                "bbox": [100, 100, 200, 200],
                "category": "猫",
                "score": 0.95
            },
            {
                "bbox": [250, 150, 300, 250],
                "category": "狗",
                "score": 0.88
            }
        ]

        # 为每张图片生成响应
        responses = []
        for data in request.get("data", []):
            response = {
                "image_name": data.get("image_name", ""),
                "image_height": 480,
                "image_width": 640,
                "infer_results": infer_results
            }
            responses.append(response)

        return {
            "traceId": trace_id,
            "success": True,
            "data": responses
        }

    def generate_multimodal_response(self, request: Dict[str, Any], is_stream: bool = False) -> Dict[str, Any]:
        """生成多模态模型响应"""
        trace_id = generate_trace_id()
        request_id = generate_request_id()
        timestamp = int(time.time())

        # 获取用户消息
        user_message = ""
        has_image = False
        if request.get("messages"):
            for msg in reversed(request["messages"]):
                if msg.get("role") == "user":
                    content = msg.get("content", [])
                    if isinstance(content, list):
                        for item in content:
                            if item.get("type") == "text":
                                user_message += item.get("text", "") + " "
                            elif item.get("type") in ["image_url", "image_base64"]:
                                has_image = True
                    break

        # 生成模拟回复
        if has_image:
            content = f"我收到了您的图片和文本：\"{user_message}\"。\n\n作为多模态模型，我可以同时处理文本和图像信息。在真实环境中，我会分析图片内容并结合您的文本给出回答。"
        else:
            content = f"我收到了您的文本：\"{user_message}\"。\n\n虽然这是多模态接口，但您只提供了文本内容。多模态模型支持同时处理文本和图像信息。"

        if is_stream:
            # 流式响应
            return self._create_multimodal_stream_response(request_id, trace_id, timestamp, content)
        else:
            # 非流式响应
            return self._create_multimodal_non_stream_response(request_id, trace_id, timestamp, content)

    def _create_non_stream_response(self, request_id: str, trace_id: str, timestamp: int, content: str) -> Dict[str, Any]:
        """创建非流式响应"""
        return {
            "id": request_id,
            "appId": self.app_id,
            "globalTraceId": trace_id,
            "object": "chat.completion",
            "created": timestamp,
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content,
                        "isSensitiveWord": False
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": len(content),
                "total_tokens": 50 + len(content)
            }
        }

    def _create_stream_response(self, request_id: str, trace_id: str, timestamp: int, content: str) -> Dict[str, Any]:
        """创建流式响应生成器"""
        def generate_stream():
            # 发送初始chunk
            first_chunk = {
                "id": request_id,
                "appId": self.app_id,
                "globalTraceId": trace_id,
                "object": "chat.completion.chunk",
                "created": timestamp,
                "choices": [
                    {
                        "finish_reason": None,
                        "index": 0,
                        "delta": {
                            "role": "assistant",
                            "content": "",
                            "isSensitiveWord": False
                        }
                    }
                ],
                "usage": None
            }
            yield f"data:{json.dumps(first_chunk, ensure_ascii=False)}\n\n"

            # 发送内容chunks
            for char in stream_text(content):
                chunk = {
                    "id": request_id,
                    "appId": self.app_id,
                    "globalTraceId": trace_id,
                    "object": "chat.completion.chunk",
                    "created": timestamp,
                    "choices": [
                        {
                            "finish_reason": None,
                            "index": 0,
                            "delta": {
                                "role": None,
                                "content": char,
                                "isSensitiveWord": False
                            }
                        }
                    ],
                    "usage": None
                }
                yield f"data:{json.dumps(chunk, ensure_ascii=False)}\n\n"

            # 发送结束标记
            end_chunk = {
                "id": request_id,
                "appId": self.app_id,
                "globalTraceId": trace_id,
                "object": "chat.completion.chunk",
                "created": timestamp,
                "choices": [
                    {
                        "finish_reason": "stop",
                        "index": 0,
                        "delta": None
                    }
                ],
                "usage": None
            }
            yield f"data:{json.dumps(end_chunk, ensure_ascii=False)}\n\n"
            yield "data:[DONE]\n\n"

        return generate_stream()

    def _create_multimodal_non_stream_response(self, request_id: str, trace_id: str, timestamp: int, content: str) -> Dict[str, Any]:
        """创建多模态非流式响应"""
        return {
            "id": request_id,
            "appId": self.app_id,
            "globalTraceId": trace_id,
            "object": "chat.completion",
            "created": timestamp,
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content,
                        "isSensitiveWord": False
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": len(content),
                "total_tokens": 100 + len(content)
            }
        }

    def _create_multimodal_stream_response(self, request_id: str, trace_id: str, timestamp: int, content: str) -> Dict[str, Any]:
        """创建多模态流式响应生成器"""
        def generate_stream():
            # 发送初始chunk
            first_chunk = {
                "id": request_id,
                "appId": self.app_id,
                "globalTraceId": trace_id,
                "object": "chat.completion.chunk",
                "created": timestamp,
                "choices": [
                    {
                        "finish_reason": None,
                        "index": 0,
                        "delta": {
                            "role": "assistant",
                            "content": "",
                            "isSensitiveWord": False
                        }
                    }
                ],
                "usage": None
            }
            yield f"data:{json.dumps(first_chunk, ensure_ascii=False)}\n\n"

            # 发送内容chunks
            for char in stream_text(content):
                chunk = {
                    "id": request_id,
                    "appId": self.app_id,
                    "globalTraceId": trace_id,
                    "object": "chat.completion.chunk",
                    "created": timestamp,
                    "choices": [
                        {
                            "finish_reason": None,
                            "index": 0,
                            "delta": {
                                "role": None,
                                "content": char,
                                "isSensitiveWord": False
                            }
                        }
                    ],
                    "usage": None
                }
                yield f"data:{json.dumps(chunk, ensure_ascii=False)}\n\n"

            # 发送结束标记
            end_chunk = {
                "id": request_id,
                "appId": self.app_id,
                "globalTraceId": trace_id,
                "object": "chat.completion.chunk",
                "created": timestamp,
                "choices": [
                    {
                        "finish_reason": "stop",
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": content,
                            "isSensitiveWord": False
                        }
                    }
                ],
                "usage": None
            }
            yield f"data:{json.dumps(end_chunk, ensure_ascii=False)}\n\n"
            yield "data:[DONE]\n\n"

        return generate_stream()