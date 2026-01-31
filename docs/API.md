# BrightChat API 文档

> BrightChat 后端 API 接口完整参考
>
> **基础路径**: `/api/v1`
> **服务器端口**: `18080`
> **认证方式**: Bearer Token (JWT)
> **API 文档**: http://localhost:18080/docs (Swagger UI)

---

## 目录

1. [认证](#1-认证)
2. [用户管理](#2-用户管理)
3. [会话与消息](#3-会话与消息)
4. [AI 对话](#4-ai-对话)
5. [Agent 管理](#5-agent-管理)
6. [知识库管理](#6-知识库管理)
7. [模型管理](#7-模型管理)
8. [收藏管理](#8-收藏管理)
9. [数据模型](#9-数据模型)

---

## 1. 认证

### 1.1 用户登录

```
POST /api/v1/auth/login
```

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应** (200 OK):
```json
{
  "id": "user-uuid",
  "username": "admin",
  "role": "admin",
  "created_at": "2026-01-29T12:00:00",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**状态码**:
- `200` - 登录成功
- `401` - 用户名或密码错误

**默认账户**: `admin` / `pwd123`

---

### 1.2 用户登出

```
POST /api/v1/auth/logout
```

**响应** (200 OK):
```json
{
  "message": "Successfully logged out"
}
```

---

## 2. 用户管理

> 所有用户管理接口需要管理员权限

### 2.1 获取用户列表

```
GET /api/v1/admin/users
```

**请求头**: `Authorization: Bearer <token>`

**响应** (200 OK):
```json
[
  {
    "id": "user-uuid-1",
    "username": "admin",
    "role": "admin",
    "created_at": "2026-01-29T12:00:00"
  },
  {
    "id": "user-uuid-2",
    "username": "user1",
    "role": "user",
    "created_at": "2026-01-29T13:00:00"
  }
]
```

---

### 2.2 创建用户

```
POST /api/v1/admin/users
```

**请求体**:
```json
{
  "username": "string",
  "password": "string",
  "role": "admin|user"
}
```

**响应** (200 OK):
```json
{
  "id": "new-user-uuid",
  "username": "newuser",
  "role": "user",
  "created_at": "2026-01-29T14:00:00"
}
```

---

### 2.3 获取用户详情

```
GET /api/v1/admin/users/{user_id}
```

**响应** (200 OK):
```json
{
  "id": "user-uuid",
  "username": "admin",
  "role": "admin",
  "created_at": "2026-01-29T12:00:00"
}
```

---

### 2.4 更新用户

```
PUT /api/v1/admin/users/{user_id}
```

**请求体**:
```json
{
  "username": "string",
  "password": "string",
  "role": "admin|user"
}
```

---

### 2.5 删除用户

```
DELETE /api/v1/admin/users/{user_id}
```

**响应** (200 OK):
```json
{
  "message": "User deleted successfully"
}
```

---

## 3. 会话与消息

### 3.1 获取会话列表

```
GET /api/v1/sessions
```

**请求头**: `Authorization: Bearer <token>`

**说明**: 用户 ID 从 JWT token 中自动提取，不需要传参

**响应** (200 OK):
```json
[
  {
    "id": "session-uuid-1",
    "title": "新对话",
    "user_id": "user-uuid",
    "last_updated": "2026-01-29T12:00:00",
    "created_at": "2026-01-29T11:00:00",
    "agent_id": null
  },
  {
    "id": "session-uuid-2",
    "title": "AI助手对话",
    "user_id": "user-uuid",
    "last_updated": "2026-01-29T13:00:00",
    "created_at": "2026-01-29T12:30:00",
    "agent_id": "agent-uuid"
  }
]
```

---

### 3.2 创建会话

```
POST /api/v1/sessions
```

**请求体**:
```json
{
  "title": "string",
  "user_id": "string",
  "agent_id": "string (可选)"
}
```

**响应** (200 OK):
```json
{
  "id": "new-session-uuid",
  "title": "新对话",
  "user_id": "user-uuid",
  "last_updated": "2026-01-29T14:00:00",
  "created_at": "2026-01-29T14:00:00",
  "agent_id": null
}
```

---

### 3.3 获取会话消息

```
GET /api/v1/sessions/{session_id}/messages
```

**请求头**: `Authorization: Bearer <token>`

**响应** (200 OK):
```json
[
  {
    "id": "msg-uuid-1",
    "session_id": "session-uuid",
    "role": "user",
    "content": "你好",
    "timestamp": "2026-01-29T12:00:00"
  },
  {
    "id": "msg-uuid-2",
    "session_id": "session-uuid",
    "role": "assistant",
    "content": "你好!有什么我可以帮助你的吗?",
    "timestamp": "2026-01-29T12:00:05"
  }
]
```

---

### 3.4 保存消息

```
POST /api/v1/sessions/{session_id}/messages
```

**请求体**:
```json
{
  "messages": [
    {
      "id": "msg-uuid",
      "role": "user|assistant|system",
      "content": "消息内容",
      "timestamp": "2026-01-29T12:00:00"
    }
  ]
}
```

**响应** (200 OK):
```json
{
  "message": "Messages saved successfully"
}
```

---

### 3.5 删除会话

```
DELETE /api/v1/sessions/{session_id}
```

**请求头**: `Authorization: Bearer <token>`

**响应** (200 OK):
```json
{
  "message": "Session deleted successfully"
}
```

---

## 4. AI 对话

### 4.1 对话完成（流式）

```
POST /api/v1/lmp-cloud-ias-server/api/llm/chat/completions/V2
```

**请求体**:
```json
{
  "model": "string",
  "messages": [
    {
      "role": "system|user|assistant",
      "content": "string"
    }
  ],
  "stream": true,
  "temperature": 0.7
}
```

**响应**: Server-Sent Events (SSE) 流

```
data: {"id":"chat-uuid","appId":"app-id","choices":[{"delta":{"content":"你"}}]}

data: {"id":"chat-uuid","appId":"app-id","choices":[{"delta":{"content":"好"}}]}

data: [DONE]
```

**参数说明**:
- `model` - 模型名称（如 `glm-4-flash`）
- `messages` - 对话历史数组
- `stream` - 是否使用流式响应（默认 `true`）
- `temperature` - 温度参数 0.0-1.0（可选）

---

## 5. Agent 管理

### 5.1 获取 Agent 列表

```
GET /api/v1/agents/
```

**请求头**: `Authorization: Bearer <token>`

**查询参数**（可选）:
- `page` - 页码（默认 1）
- `limit` - 每页数量（默认 20，最大 100）
- `agent_type` - 筛选 Agent 类型（`rag|tool|custom`）
- `is_active` - 筛选激活状态（仅管理员）
- `search` - 搜索关键词（匹配 name 或 display_name）

**响应** (200 OK):
```json
{
  "agents": [
    {
      "id": "agent-uuid",
      "name": "research-assistant",
      "display_name": "研究助手",
      "description": "帮助进行学术研究",
      "agent_type": "tool",
      "system_prompt": "你是专业的学术研究助手...",
      "knowledge_base_ids": ["kb-1", "kb-2"],
      "tools": ["calculator", "knowledge_search"],
      "config": {
        "temperature": 0.7,
        "max_steps": 10,
        "timeout": 300
      },
      "llm_model_id": "model-123",
      "llm_model_name": "GLM-4-Flash",
      "enable_knowledge": true,
      "order": 1,
      "is_active": true,
      "created_by": "user-123",
      "created_at": "2026-01-29T10:00:00",
      "updated_at": "2026-01-29T10:00:00"
    }
  ],
  "total": 42,
  "page": 1,
  "limit": 20,
  "has_more": true
}
```

---

### 5.2 创建 Agent（管理员）

```
POST /api/v1/agents/
```

**请求头**: `Authorization: Bearer <token>`

**请求体**:
```json
{
  "name": "string",
  "display_name": "string",
  "description": "string (可选)",
  "agent_type": "rag|tool|custom",
  "system_prompt": "string (可选)",
  "knowledge_base_ids": ["string"],
  "tools": ["string"],
  "llm_model_id": "string (可选)",
  "config": {
    "temperature": 0.7,
    "max_steps": 10,
    "timeout": 300
  },
  "enable_knowledge": true,
  "order": 1,
  "is_active": true
}
```

**可用工具**:
- `knowledge_search` - 知识库检索
- `calculator` - 计算器
- `datetime` - 当前时间
- `code_executor` - 代码执行
- `browser` - 浏览器
- `file` - 文件操作

---

### 5.3 获取 Agent 详情

```
GET /api/v1/agents/{agent_id}
```

**请求头**: `Authorization: Bearer <token>`

**响应**: 与 Agent 列表中的单个 Agent 对象格式相同

---

### 5.4 更新 Agent（管理员）

```
PUT /api/v1/agents/{agent_id}
```

**请求头**: `Authorization: Bearer <token>`

**请求体**（所有字段可选）:
```json
{
  "name": "string",
  "display_name": "string",
  "description": "string",
  "system_prompt": "string",
  "knowledge_base_ids": ["string"],
  "tools": ["string"],
  "config": {
    "temperature": 0.7,
    "max_steps": 10,
    "timeout": 300
  },
  "llm_model_id": "string",
  "enable_knowledge": true,
  "order": 1,
  "is_active": true
}
```

---

### 5.5 删除 Agent（管理员）

```
DELETE /api/v1/agents/{agent_id}
```

**请求头**: `Authorization: Bearer <token>`

**响应** (200 OK):
```json
{
  "message": "Agent 删除成功"
}
```

---

### 5.6 Agent 对话（流式）

```
POST /api/v1/agents/{agent_id}/chat
```

**请求头**: `Authorization: Bearer <token>`

**请求体**:
```json
{
  "query": "string",
  "session_id": "string (可选)",
  "stream": true
}
```

**响应**: SSE 流式响应

**SSE 事件类型**:

| 事件类型 | 说明 |
|---------|------|
| `start` | 对话开始，包含 execution_id、agent_name、query |
| `step` | 推理步骤（think/act/observe），包含 node、step、state |
| `tool_call` | 工具调用，包含 tool、parameters、result |
| `complete` | 对话完成，包含 output、steps、duration |
| `error` | 错误，包含 error 信息 |

**SSE 流示例**:
```
data: {"type":"start","execution_id":"exec-456","agent_name":"研究助手","query":"帮我搜索最新AI论文","timestamp":"2026-01-29T12:00:00"}

data: {"type":"step","node":"think","step":1,"state":{"input":"帮我搜索最新AI论文"},"timestamp":"2026-01-29T12:00:01"}

data: {"type":"tool_call","tool":"knowledge_search","parameters":{"query":"AI论文","top_k":5},"result":"找到 5 条相关记录...","timestamp":"2026-01-29T12:00:03"}

data: {"type":"complete","output":"根据搜索结果，最新的AI论文包括...","steps":3,"duration":5.2,"timestamp":"2026-01-29T12:00:06"}

data: [DONE]
```

---

### 5.7 获取可用工具

```
GET /api/v1/agents/tools
```

**响应** (200 OK):
```json
{
  "tools": [
    {
      "name": "knowledge_search",
      "display_name": "知识库检索",
      "description": "在知识库中搜索相关信息",
      "category": "knowledge",
      "parameters": {
        "query": {"type": "string", "description": "搜索查询"},
        "knowledge_base_ids": {"type": "array", "description": "知识库 ID 列表"},
        "top_k": {"type": "integer", "default": 5, "description": "返回结果数量"}
      }
    },
    {
      "name": "calculator",
      "display_name": "计算器",
      "description": "执行数学计算",
      "category": "calculation",
      "parameters": {
        "expression": {"type": "string", "description": "数学表达式"}
      }
    },
    {
      "name": "datetime",
      "display_name": "当前时间",
      "description": "获取当前日期和时间",
      "category": "system",
      "parameters": {}
    },
    {
      "name": "code_executor",
      "display_name": "代码执行",
      "description": "安全执行 Python 代码（沙箱隔离）",
      "category": "system",
      "parameters": {
        "code": {"type": "string", "description": "要执行的 Python 代码"},
        "timeout": {"type": "integer", "default": 30, "description": "超时时间（秒）"}
      }
    },
    {
      "name": "browser",
      "display_name": "浏览器",
      "description": "网页浏览、搜索、数据抓取（无头浏览器）",
      "category": "search",
      "parameters": {
        "action": {"type": "string", "description": "操作类型：navigate/search/scrape/screenshot/click/fill"},
        "url": {"type": "string", "description": "目标 URL"},
        "selector": {"type": "string", "description": "CSS 选择器"},
        "text": {"type": "string", "description": "文本内容"},
        "wait_time": {"type": "integer", "default": 3000, "description": "等待时间（毫秒）"}
      }
    },
    {
      "name": "file",
      "display_name": "文件操作",
      "description": "读写文件、列出目录",
      "category": "system",
      "parameters": {
        "action": {"type": "string", "description": "操作类型：read/write/list/exists/delete"},
        "path": {"type": "string", "description": "文件路径"},
        "content": {"type": "string", "description": "文件内容（用于 write）"},
        "allowed_dirs": {"type": "array", "description": "允许访问的目录列表"}
      }
    }
  ]
}
```

---

### 5.8 获取执行历史

```
GET /api/v1/agents/{agent_id}/executions
```

**请求头**: `Authorization: Bearer <token>`

**查询参数**:
- `page` - 页码（默认 1）
- `limit` - 每页数量（默认 50，最大 100）

**响应** (200 OK):
```json
{
  "executions": [
    {
      "id": "exec-001",
      "agent_id": "agent-001",
      "user_id": "user-123",
      "session_id": "session-456",
      "input_prompt": "帮我分析销售数据",
      "status": "completed",
      "steps": 3,
      "result": "根据分析，销售数据呈上升趋势...",
      "error_message": null,
      "started_at": "2026-01-29T12:00:00",
      "completed_at": "2026-01-29T12:00:05"
    }
  ],
  "total": 42,
  "page": 1,
  "limit": 10,
  "has_more": true
}
```

**执行状态**: `running` | `completed` | `failed`

---

### 5.9 健康检查

```
GET /api/v1/agents/service-health
```

**响应** (200 OK):
```json
{
  "status": "healthy",
  "tools_registered": 6,
  "timestamp": "2026-01-29T12:00:00.123456"
}
```

---

## 6. 知识库管理

### 6.1 获取知识库分组列表

```
GET /api/v1/knowledge/groups
```

**请求头**: `Authorization: Bearer <token>`

**说明**: 返回当前用户的所有知识库分组

**响应** (200 OK):
```json
[
  {
    "id": "group-uuid-1",
    "name": "技术文档",
    "description": "包含所有技术相关的文档",
    "user_id": "user-uuid",
    "created_at": "2026-01-29T10:00:00",
    "updated_at": "2026-01-29T10:00:00"
  }
]
```

---

### 6.2 创建知识库分组

```
POST /api/v1/knowledge/groups
```

**请求头**: `Authorization: Bearer <token>`

**请求体**:
```json
{
  "name": "string",
  "description": "string (可选)"
}
```

**说明**: `user_id` 从 JWT token 中自动提取

---

### 6.3 删除知识库分组

```
DELETE /api/v1/knowledge/groups/{group_id}
```

**请求头**: `Authorization: Bearer <token>`

**响应** (200 OK):
```json
{
  "message": "分组已删除"
}
```

---

### 6.4 获取知识库列表

```
GET /api/v1/knowledge/bases
```

**请求头**: `Authorization: Bearer <token>`

**查询参数**（可选）:
- `group_id` - 筛选指定分组的知识库

**响应** (200 OK):
```json
[
  {
    "id": "kb-uuid-1",
    "group_id": "group-uuid-1",
    "user_id": "user-uuid",
    "name": "Python 入门指南",
    "description": "Python 编程基础知识",
    "embedding_model": "bge-large-zh-v1.5",
    "chunk_size": 500,
    "chunk_overlap": 50,
    "created_at": "2026-01-29T10:00:00",
    "updated_at": "2026-01-29T10:00:00",
    "document_count": 5
  }
]
```

---

### 6.5 获取知识库详情

```
GET /api/v1/knowledge/bases/{kb_id}
```

**请求头**: `Authorization: Bearer <token>`

**响应**: 与知识库列表中的单个对象格式相同

---

### 6.6 创建知识库

```
POST /api/v1/knowledge/bases
```

**请求头**: `Authorization: Bearer <token>`

**请求体**:
```json
{
  "name": "string",
  "description": "string (可选)",
  "group_id": "string (可选)",
  "embedding_model": "string (默认: bge-large-zh-v1.5)",
  "chunk_size": "int (默认: 500)",
  "chunk_overlap": "int (默认: 50)"
}
```

**说明**: `user_id` 从 JWT token 中自动提取；`group_id` 可选，为空时创建独立知识库

---

### 6.7 更新知识库

```
PUT /api/v1/knowledge/bases/{kb_id}
```

**请求头**: `Authorization: Bearer <token>`

**请求体**（所有字段可选）:
```json
{
  "name": "string",
  "description": "string",
  "group_id": "string",
  "is_active": "boolean"
}
```

---

### 6.8 删除知识库

```
DELETE /api/v1/knowledge/bases/{kb_id}
```

**请求头**: `Authorization: Bearer <token>`

**响应** (200 OK):
```json
{
  "message": "知识库已删除"
}
```

---

### 6.9 上传文档

```
POST /api/v1/knowledge/bases/{kb_id}/documents
```

**请求头**: `Authorization: Bearer <token>`

**请求参数**: multipart/form-data
- `file` - 文档文件（必填）
- `sync` - 是否同步处理，默认 `false`
- `chunk_size` - 分块大小，默认 `500`
- `chunk_overlap` - 重叠大小，默认 `50`

**支持的格式**: PDF, DOCX, TXT, MD, HTML, XLS, XLSX, PPT, PPTX

**文件大小限制**: 最大 50MB

**同步模式响应** (`sync=true`):
```json
{
  "id": "doc-uuid-1",
  "knowledge_base_id": "kb-uuid-1",
  "filename": "Python基础教程.pdf",
  "file_type": "pdf",
  "file_size": 1048576,
  "chunk_count": 42,
  "upload_status": "completed",
  "error_message": null,
  "uploaded_at": "2026-01-29T10:40:00",
  "processed_at": "2026-01-29T10:40:15"
}
```

**异步模式响应** (`sync=false`):
```json
{
  "id": "doc-uuid-1",
  "knowledge_base_id": "kb-uuid-1",
  "filename": "Python基础教程.pdf",
  "file_type": "pdf",
  "file_size": 1048576,
  "chunk_count": 0,
  "upload_status": "processing",
  "error_message": null,
  "uploaded_at": "2026-01-29T10:40:00",
  "processed_at": null
}
```

**上传状态**: `pending` | `processing` | `completed` | `error`

---

### 6.10 获取文档列表

```
GET /api/v1/knowledge/bases/{kb_id}/documents
```

**请求头**: `Authorization: Bearer <token>`

**响应** (200 OK):
```json
[
  {
    "id": "doc-uuid-1",
    "knowledge_base_id": "kb-uuid-1",
    "filename": "Python基础教程.pdf",
    "file_type": "pdf",
    "file_size": 1048576,
    "chunk_count": 42,
    "upload_status": "completed",
    "error_message": null,
    "uploaded_at": "2026-01-29T10:40:00",
    "processed_at": "2026-01-29T10:40:15",
    "created_at": "2026-01-29T10:40:00",
    "updated_at": "2026-01-29T10:40:15"
  }
]
```

---

### 6.11 获取文档详情

```
GET /api/v1/knowledge/bases/{kb_id}/documents/{doc_id}
```

**请求头**: `Authorization: Bearer <token>`

**响应**: 与文档列表中的单个对象格式相同

---

### 6.12 获取文档切片

```
GET /api/v1/knowledge/bases/{kb_id}/documents/{doc_id}/chunks
```

**请求头**: `Authorization: Bearer <token>`

**查询参数**:
- `offset` - 偏移量（默认 0）
- `limit` - 返回数量限制（可选，不传则返回全部）

**响应** (200 OK):
```json
{
  "document_id": "doc-uuid-1",
  "filename": "Python基础教程.pdf",
  "chunks": [
    {
      "id": "doc-uuid-1_chunk_0",
      "chunk_index": 0,
      "content": "Python 是一种高级编程语言，由 Guido van Rossum 于 1991 年首次发布...",
      "metadata": {
        "document_id": "doc-uuid-1",
        "knowledge_base_id": "kb-uuid-1",
        "user_id": "user-uuid",
        "filename": "Python基础教程.pdf",
        "file_type": "pdf",
        "source": "Python基础教程.pdf"
      }
    }
  ],
  "total_count": 42,
  "returned_count": 1,
  "offset": 0,
  "limit": 1
}
```

---

### 6.13 删除文档

```
DELETE /api/v1/knowledge/bases/{kb_id}/documents/{doc_id}
```

**请求头**: `Authorization: Bearer <token>`

**响应** (200 OK):
```json
{
  "message": "文档已删除"
}
```

---

### 6.14 语义搜索

```
GET /api/v1/knowledge/search
```

**请求头**: `Authorization: Bearer <token>`

**查询参数**:
- `query` - 搜索查询（必填）
- `knowledge_base_ids` - 知识库 ID 列表（逗号分隔，可选，不传则搜索所有）
- `top_k` - 返回结果数（默认 5）

**响应** (200 OK):
```json
{
  "results": [
    {
      "id": "doc-uuid-1_chunk_5",
      "content": "安装第三方库使用 pip 工具，pip 是 Python 的包管理器...",
      "metadata": {
        "document_id": "doc-uuid-1",
        "knowledge_base_id": "kb-uuid-1",
        "user_id": "user-uuid",
        "filename": "Python基础教程.pdf",
        "file_type": "pdf",
        "chunk_index": 5
      },
      "similarity": 0.892,
      "distance": 0.108
    }
  ],
  "query": "Python如何安装第三方库？",
  "total": 1
}
```

**无结果时响应**:
```json
{
  "results": [],
  "query": "搜索查询",
  "total": 0,
  "message": "暂无可搜索的知识库，请先创建知识库并上传文档"
}
```

---

## 7. 模型管理

### 7.1 获取所有模型（含 API Key）

```
GET /api/v1/admin/models
```

**请求头**: `Authorization: Bearer <token>` (管理员权限)

**响应** (200 OK):
```json
{
  "models": [
    {
      "id": "model-uuid-1",
      "name": "glm-4-flash",
      "display_name": "智谱 GLM-4 Flash",
      "model_type": "custom",
      "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
      "api_key": "sk-xxxxx",
      "api_version": null,
      "description": "智谱 AI GLM-4 Flash 模型",
      "is_active": true,
      "max_tokens": 4096,
      "temperature": 0.7,
      "stream_supported": true,
      "created_at": "2026-01-29T10:00:00"
    }
  ],
  "total": 1
}
```

---

### 7.2 获取模型详情（含 API Key）

```
GET /api/v1/admin/models/{model_id}
```

**请求头**: `Authorization: Bearer <token>` (管理员权限)

---

### 7.3 获取激活模型（不含 API Key）

```
GET /api/v1/models/active
```

**请求头**: `Authorization: Bearer <token>`

**响应**: 与获取所有模型相同，但不包含 `api_key` 字段

---

### 7.4 创建模型

```
POST /api/v1/admin/models
```

**请求头**: `Authorization: Bearer <token>` (管理员权限)

**请求体**:
```json
{
  "name": "string",
  "display_name": "string",
  "model_type": "openai|anthropic|custom|ias",
  "api_url": "string",
  "api_key": "string",
  "api_version": "string (可选)",
  "description": "string (可选)",
  "is_active": true,
  "max_tokens": 4096,
  "temperature": 0.7,
  "stream_supported": true,
  "custom_headers": {}
}
```

**注意**: `temperature` 在请求中使用浮点数（如 0.7），但存储时转换为整数（70）

---

### 7.5 更新模型

```
PUT /api/v1/admin/models/{model_id}
```

**请求头**: `Authorization: Bearer <token>` (管理员权限)

**请求体**（所有字段可选）:
```json
{
  "display_name": "string",
  "api_url": "string",
  "api_key": "string",
  "api_version": "string",
  "description": "string",
  "is_active": "boolean",
  "max_tokens": "int",
  "temperature": "float",
  "stream_supported": "boolean",
  "custom_headers": {}
}
```

---

### 7.6 删除模型

```
DELETE /api/v1/admin/models/{model_id}
```

**请求头**: `Authorization: Bearer <token>` (管理员权限)

**响应** (200 OK):
```json
{
  "message": "Model deleted successfully"
}
```

---

## 8. 收藏管理

### 8.1 添加收藏

```
POST /api/v1/messages/{message_id}/favorite
```

**请求头**: `Authorization: Bearer <token>`

**请求体**（可选）:
```json
{
  "note": "备注信息"
}
```

**响应** (200 OK):
```json
{
  "id": "favorite-uuid",
  "messageId": "message-uuid",
  "createdAt": "2026-01-29T12:00:00"
}
```

---

### 8.2 取消收藏

```
DELETE /api/v1/messages/{message_id}/favorite
```

**请求头**: `Authorization: Bearer <token>`

**响应** (200 OK):
```json
{
  "message": "取消收藏成功"
}
```

---

### 8.3 获取收藏列表

```
GET /api/v1/favorites
```

**请求头**: `Authorization: Bearer <token>`

**查询参数**:
- `limit` - 返回数量（默认 20）
- `offset` - 偏移量（默认 0）

**响应** (200 OK):
```json
{
  "favorites": [
    {
      "id": "favorite-uuid",
      "message": {
        "id": "message-uuid",
        "role": "assistant",
        "content": "这是一条重要的回答...",
        "timestamp": "2026-01-29T12:00:00"
      },
      "session": {
        "id": "session-uuid",
        "title": "对话标题",
        "last_updated": "2026-01-29T12:00:00",
        "user_id": "user-uuid"
      },
      "note": "重要的知识点",
      "createdAt": "2026-01-29T12:00:00"
    }
  ],
  "total": 10
}
```

---

### 8.4 检查收藏状态

```
GET /api/v1/messages/{message_id}/favorite-status
```

**请求头**: `Authorization: Bearer <token>`

**响应** (200 OK):
```json
{
  "is_favorited": true,
  "favorite_id": "favorite-uuid"
}
```

---

## 9. 数据模型

### User（用户）
```typescript
interface User {
  id: string;          // UUID
  username: string;    // 唯一用户名
  role: 'admin' | 'user';
  created_at: string;  // ISO 8601
}
```

### Session（会话）
```typescript
interface Session {
  id: string;
  title: string;
  user_id: string;
  agent_id?: string;   // 关联的 Agent ID
  last_updated: string;
  created_at: string;
}
```

### Message（消息）
```typescript
interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}
```

### Agent（智能体）
```typescript
interface Agent {
  id: string;
  name: string;
  display_name: string;
  agent_type: 'rag' | 'tool' | 'custom';
  description: string;
  system_prompt: string;
  knowledge_base_ids?: string[];
  tools?: string[];
  llm_model_id?: string;
  llm_model_name?: string;
  config: {
    temperature: number;
    max_steps: number;
    timeout: number;
  };
  enable_knowledge: boolean;
  order: number;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}
```

### KnowledgeGroup（知识库分组）
```typescript
interface KnowledgeGroup {
  id: string;
  name: string;
  description?: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}
```

### KnowledgeBase（知识库）
```typescript
interface KnowledgeBase {
  id: string;
  group_id?: string;
  user_id: string;
  name: string;
  description?: string;
  embedding_model: string;
  chunk_size: number;
  chunk_overlap: number;
  document_count: number;
  created_at: string;
  updated_at: string;
}
```

### Document（文档）
```typescript
interface Document {
  id: string;
  knowledge_base_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  chunk_count: number;
  upload_status: 'pending' | 'processing' | 'completed' | 'error';
  error_message?: string;
  uploaded_at: string;
  processed_at?: string;
}
```

### LLMModel（LLM 模型）
```typescript
interface LLMModel {
  id: string;
  name: string;
  display_name: string;
  model_type: 'openai' | 'anthropic' | 'custom' | 'ias';
  api_url: string;
  api_key?: string;    // 仅管理员可见
  api_version?: string;
  description?: string;
  is_active: boolean;
  max_tokens: number;
  temperature: number;  // 存储为整数（70 = 0.70）
  stream_supported: boolean;
  custom_headers?: Record<string, string>;
  created_at: string;
}
```

---

## 错误响应

所有错误返回统一格式：

```json
{
  "detail": "错误描述信息"
}
```

**常见 HTTP 状态码**:
- `200` - 成功
- `400` - 请求参数错误
- `401` - 未认证（Token 无效或过期）
- `403` - 无权限
- `404` - 资源不存在
- `413` - 文件过大（超过 50MB）
- `500` - 服务器内部错误

---

## 使用示例

### JavaScript/TypeScript

```typescript
// 登录
const loginRes = await fetch('http://localhost:18080/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'pwd123' })
});
const { token } = await loginRes.json();

// 创建会话
const sessionRes = await fetch('http://localhost:18080/api/v1/sessions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    title: '新对话',
    user_id: 'user-uuid'
  })
});
const { id: sessionId } = await sessionRes.json();

// AI 对话（流式）
const chatRes = await fetch('http://localhost:18080/api/v1/lmp-cloud-ias-server/api/llm/chat/completions/V2', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    model: 'glm-4-flash',
    messages: [{ role: 'user', content: '你好' }],
    stream: true
  })
});

// 处理 SSE 流
const reader = chatRes.body?.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader!.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data:') || line.startsWith('event:data')) {
      const dataStr = line.replace(/^event:data\s*/i, '').replace('data:', '').trim();
      if (dataStr === '[DONE]') break;

      try {
        const data = JSON.parse(dataStr);
        const content = data.choices[0]?.delta?.content || '';
        console.log('收到内容:', content);
      } catch (e) {}
    }
  }
}

// Agent 对话
const agentChatRes = await fetch('http://localhost:18080/api/v1/agents/agent-id/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: '帮我分析最近一周的销售数据',
    session_id: sessionId
  })
});

// 处理 Agent SSE 流
for await (const event of readSSEStream(agentChatRes)) {
  switch (event.type) {
    case 'start':
      console.log('开始执行:', event.execution_id);
      break;
    case 'step':
      console.log('步骤:', event.node, event.step);
      break;
    case 'tool_call':
      console.log('工具调用:', event.tool, event.result);
      break;
    case 'complete':
      console.log('完成:', event.output);
      break;
    case 'error':
      console.error('错误:', event.error);
      break;
  }
}
```

### cURL

```bash
# 登录
curl -X POST http://localhost:18080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pwd123"}'

# 获取会话列表
curl http://localhost:18080/api/v1/sessions \
  -H "Authorization: Bearer YOUR_TOKEN"

# 创建会话
curl -X POST http://localhost:18080/api/v1/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"title":"新对话","user_id":"USER_ID"}'

# 获取 Agent 列表
curl http://localhost:18080/api/v1/agents/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Agent 对话
curl -X POST http://localhost:18080/api/v1/agents/AGENT_ID/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query":"帮我搜索最新的AI论文","stream":true}'

# 创建知识库
curl -X POST http://localhost:18080/api/v1/knowledge/bases \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name":"Python 文档","description":"Python 相关文档"}'

# 上传文档
curl -X POST http://localhost:18080/api/v1/knowledge/bases/KB_ID/documents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/document.pdf" \
  -F "sync=true"

# 语义搜索
curl "http://localhost:18080/api/v1/knowledge/search?query=Python如何安装&top_k=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 系统状态端点

### 健康检查

```
GET /health
```

**响应** (200 OK):
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 系统健康检查（详细）

```
GET /api/v1/system/health
```

**请求头**: `Authorization: Bearer <token>`

**响应** (200 OK):
```json
{
  "timestamp": "2026-01-29T12:00:00",
  "status": "healthy",
  "components": {
    "database": {
      "status": "healthy",
      "message": "数据库连接正常"
    },
    "chromadb": {
      "status": "healthy",
      "message": "ChromaDB连接正常",
      "collection": "knowledge_chunks",
      "vector_count": 1500
    },
    "embedding_model": {
      "status": "healthy",
      "model_name": "bge-large-zh-v1.5",
      "dimension": 1024
    }
  }
}
```

---

**最后更新**: 2026-01-29
**服务器端口**: 18080
**详细文档**: [docs/知识库接口文档(正式).md](./知识库接口文档(正式).md), [docs/智能体接口文档(0.1版本).md](./智能体接口文档(0.1版本).md)
