# BrightChat API 文档

> BrightChat 后端 API 接口完整参考

**基础路径**: `/api/v1`
**认证方式**: Bearer Token (JWT)
**API 文档**: http://localhost:18080/docs (Swagger UI)

---

## 目录

1. [认证](#1-认证)
2. [用户管理](#2-用户管理)
3. [会话与消息](#3-会话与消息)
4. [AI 对话](#4-ai-对话)
5. [Agent 管理](#5-agent-管理)
6. [知识库管理](#6-知识库管理)
7. [模型管理](#7-模型管理)
8. [数据模型](#8-数据模型)

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

### 2.3 更新用户

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

### 2.4 删除用户

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
GET /api/v1/sessions?user_id={user_id}
```

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

**查询参数**:
- `user_id` - 用户ID（必填）

---

### 3.2 创建会话

```
POST /api/v1/sessions
```

**请求体**:
```json
{
  "title": "string",
  "user_id": "string"
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

**查询参数**（可选）:
- `is_active` - 筛选激活状态
- `skip` - 跳过记录数
- `limit` - 返回记录数

**响应** (200 OK):
```json
[
  {
    "id": "agent-uuid",
    "name": "research-assistant",
    "display_name": "研究助手",
    "description": "帮助进行学术研究",
    "agent_type": "tool",
    "is_active": true,
    "created_at": "2026-01-29T10:00:00"
  }
]
```

---

### 5.2 创建 Agent（管理员）

```
POST /api/v1/agents/
```

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
    "max_tokens": 2000
  },
  "is_active": true
}
```

---

### 5.3 获取 Agent 详情

```
GET /api/v1/agents/{agent_id}
```

---

### 5.4 更新 Agent（管理员）

```
PUT /api/v1/agents/{agent_id}
```

---

### 5.5 删除 Agent（管理员）

```
DELETE /api/v1/agents/{agent_id}
```

---

### 5.6 Agent 对话（流式）

```
POST /api/v1/agents/{agent_id}/chat
```

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
- `start` - 对话开始
- `step` - 推理步骤（think/act/observe）
- `tool_call` - 工具调用
- `complete` - 对话完成
- `error` - 错误

---

### 5.7 获取可用工具

```
GET /api/v1/agents/tools/
```

**响应** (200 OK):
```json
{
  "tools": [
    {
      "name": "calculator",
      "display_name": "计算器",
      "description": "执行数学计算",
      "parameters": {}
    },
    {
      "name": "datetime",
      "display_name": "时间日期",
      "description": "获取当前时间",
      "parameters": {}
    },
    {
      "name": "knowledge_search",
      "display_name": "知识库搜索",
      "description": "在知识库中检索信息",
      "parameters": {}
    },
    {
      "name": "code_executor",
      "display_name": "代码执行",
      "description": "执行 Python 代码",
      "parameters": {}
    }
  ]
}
```

---

### 5.8 健康检查

```
GET /api/v1/agents/service-health/
```

**响应** (200 OK):
```json
{
  "status": "healthy",
  "langgraph_version": "0.2.0",
  "tools_count": 6
}
```

---

## 6. 知识库管理

### 6.1 获取知识库分组列表

```
GET /api/v1/knowledge/groups?user_id={user_id}
```

---

### 6.2 创建知识库分组

```
POST /api/v1/knowledge/groups
```

**请求体**:
```json
{
  "user_id": "string",
  "name": "string",
  "description": "string (可选)"
}
```

---

### 6.3 获取知识库列表

```
GET /api/v1/knowledge/bases
```

**查询参数**（可选）:
- `group_id` - 筛选指定分组
- `name` - 按名称模糊搜索
- `skip` - 分页偏移
- `limit` - 返回记录数

---

### 6.4 创建知识库

```
POST /api/v1/knowledge/bases
```

**请求体**:
```json
{
  "group_id": "string",
  "name": "string",
  "description": "string (可选)",
  "embedding_model": "string"
}
```

---

### 6.5 上传文档

```
POST /api/v1/knowledge/bases/{kb_id}/documents
```

**请求参数**: multipart/form-data
- `file` - 文档文件
- `sync` - 是否同步处理（默认 false）
- `chunk_size` - 分块大小（默认 500）
- `chunk_overlap` - 重叠大小（默认 50）

**支持的格式**: PDF, DOCX, TXT, MD, HTML, XLS, XLSX, PPT, PPTX

---

### 6.6 获取文档列表

```
GET /api/v1/knowledge/bases/{kb_id}/documents
```

---

### 6.7 获取文档切片详情

```
GET /api/v1/knowledge/documents/{doc_id}/chunks
```

**查询参数**（可选）:
- `page` - 页码（从 1 开始）
- `page_size` - 每页数量（1-1000）
- `include_embeddings` - 是否包含向量数据

**响应** (200 OK):
```json
{
  "document_id": "uuid-doc-id",
  "filename": "example.pdf",
  "total_chunks": 150,
  "chunks": [
    {
      "id": "uuid-chunk-id",
      "document_id": "uuid-doc-id",
      "knowledge_base_id": "uuid-kb-id",
      "chunk_index": 0,
      "content": "这是文档的第一个切片内容...",
      "metadata": {
        "page": 1,
        "chunk_size": 500,
        "source": "example.pdf"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_count": 150,
    "total_pages": 15
  }
}
```

---

### 6.8 语义搜索

```
GET /api/v1/knowledge/search?query={query}
```

**查询参数**:
- `query` - 搜索查询（必填）
- `knowledge_base_ids` - 知识库ID列表（逗号分隔）
- `top_k` - 返回结果数（默认 5）

---

### 6.9 删除文档

```
DELETE /api/v1/knowledge/documents/{doc_id}
```

---

### 6.10 删除知识库

```
DELETE /api/v1/knowledge/bases/{kb_id}
```

---

### 6.11 删除分组

```
DELETE /api/v1/knowledge/groups/{group_id}
```

---

## 7. 模型管理

> 仅管理员可访问

### 7.1 获取所有模型（含 API Key）

```
GET /api/v1/admin/models
```

---

### 7.2 获取激活模型（不含 API Key）

```
GET /api/v1/models/active
```

---

### 7.3 创建模型

```
POST /api/v1/admin/models
```

**请求体**:
```json
{
  "name": "string",
  "display_name": "string",
  "model_type": "openai|anthropic|custom|ias",
  "api_url": "string",
  "api_key": "string",
  "is_active": true,
  "temperature": 70
}
```

---

### 7.4 更新模型

```
PUT /api/v1/admin/models/{model_id}
```

---

### 7.5 删除模型

```
DELETE /api/v1/admin/models/{model_id}
```

---

## 8. 数据模型

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
  system_prompt: string;
  knowledge_base_ids?: string[];
  tools?: string[];
  llm_model_id?: string;
  config: {
    temperature: number;
    max_tokens: number;
  };
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
```

### KnowledgeBase（知识库）
```typescript
interface KnowledgeBase {
  id: string;
  group_id: string;
  name: string;
  description?: string;
  embedding_model: string;
  document_count: number;
  created_at: string;
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
  upload_status: 'processing' | 'completed' | 'failed';
  uploaded_at: string;
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
  api_key: string;    // 管理员可见
  is_active: boolean;
  temperature: number;  // 存储为整数（70 = 0.70）
  stream_supported: boolean;
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
- `500` - 服务器内部错误

---

## 使用示例

### JavaScript/TypeScript

```typescript
// 登录
const loginRes = await fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'pwd123' })
});
const { token } = await loginRes.json();

// 创建会话
const sessionRes = await fetch('/api/v1/sessions', {
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
const chatRes = await fetch('/api/v1/lmp-cloud-ias-server/api/llm/chat/completions/V2', {
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
const reader = chatRes.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
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
```

### cURL

```bash
# 登录
curl -X POST http://localhost:18080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pwd123"}'

# 获取会话列表
curl "http://localhost:18080/api/v1/sessions?user_id=USER_ID" \
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
```

---

**最后更新**: 2026-01-29
**详细文档**: [MdDocs/backend/api/](MdDocs/backend/api/)
