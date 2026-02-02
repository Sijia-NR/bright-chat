# 智能体接口文档

**Bright-Chat Agent API Documentation**

> 版本: 1.0.0
> 基础路径: `/api/v1/agents`
> 协议: HTTP/HTTPS
> 数据格式: JSON
> 最后更新: 2026-02-02

---

## 📋 目录

- [认证说明](#认证说明)
- [响应格式](#响应格式)
- [接口列表](#接口列表)
- [Agent 管理](#agent-管理)
  - [创建 Agent](#1-创建-agent)
  - [获取 Agent 列表](#2-获取-agent-列表)
  - [获取 Agent 详情](#3-获取-agent-详情)
  - [更新 Agent](#4-更新-agent)
  - [删除 Agent](#5-删除-agent)
- [Agent 交互](#agent-交互)
  - [Agent 聊天](#6-agent-聊天)
  - [获取执行历史](#7-获取执行历史)
  - [获取消息执行记录](#8-获取消息执行记录)
- [工具与服务](#工具与服务)
  - [获取可用工具](#9-获取可用工具)
  - [健康检查](#10-健康检查)
- [数据模型](#数据模型)
- [Agent 工具详细说明](#agent-工具详细说明)
- [错误码](#错误码)

---

## 认证说明

所有需要认证的接口都使用 **Bearer Token** 认证方式。

### 请求头

```
Authorization: Bearer <token>
```

### 获取 Token

通过登录接口获取：

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "pwd123"
}
```

**响应示例**：

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "id": "fe4e56fb-86c6-48b3-a64d-86192a2f867c",
  "username": "admin",
  "role": "admin"
}
```

---

## 响应格式

### 成功响应

```json
{
  "success": true,
  "data": { ... }
}
```

### 错误响应

```json
{
  "detail": "错误描述信息"
}
```

或

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

---

## 接口列表

| 序号 | 接口名称 | 方法 | 路径 | 认证 | 权限 |
|------|---------|------|------|------|------|
| 1 | 创建 Agent | POST | `/agents/` | ✅ | Admin |
| 2 | 获取 Agent 列表 | GET | `/agents/` | ✅ | All |
| 3 | 获取 Agent 详情 | GET | `/agents/{id}` | ✅ | All |
| 4 | 更新 Agent | PUT | `/agents/{id}` | ✅ | Admin |
| 5 | 删除 Agent | DELETE | `/agents/{id}` | ✅ | Admin |
| 6 | Agent 聊天 | POST | `/agents/{id}/chat` | ✅ | All |
| 7 | 获取执行历史 | GET | `/agents/{id}/executions` | ✅ | All |
| 8 | 获取消息执行记录 | GET | `/agents/messages/{message_id}/execution` | ✅ | All |
| 9 | 获取可用工具 | GET | `/agents/tools` | ❌ | Public |
| 10 | 健康检查 | GET | `/agents/service-health` | ❌ | Public |

---

## Agent 管理

### 1. 创建 Agent

创建新的智能体。

**接口信息**：

- **方法**: `POST`
- **路径**: `/api/v1/agents/`
- **认证**: 需要
- **权限**: 仅管理员

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | Agent 名称（唯一标识） |
| `display_name` | string | ❌ | 显示名称 |
| `description` | string | ❌ | 描述信息 |
| `agent_type` | string | ❌ | Agent 类型：`rag` / `tool` / `custom`，默认 `tool` |
| `system_prompt` | string | ❌ | 系统提示词 |
| `knowledge_base_ids` | array | ❌ | 关联的知识库 ID 列表 |
| `tools` | array | ❌ | 可用工具列表 |
| `config` | object | ❌ | Agent 配置 |
| `llm_model_id` | string | ❌ | 关联的 LLM 模型 ID |
| `enable_knowledge` | boolean | ❌ | 是否启用知识库，默认 `true` |
| `order` | integer | ❌ | 显示顺序，自动生成 |

**config 对象结构**：

```json
{
  "temperature": 0.7,    // 0-2，默认 0.7
  "max_steps": 10,       // 1-50，默认 10
  "timeout": 300         // 超时时间（秒），默认 300
}
```

**可用工具列表**：

- `knowledge_search` - 知识库检索
- `calculator` - 计算器
- `datetime` - 当前时间
- `code_executor` - 代码执行（沙箱隔离）
- `browser` - 浏览器（无头浏览器）
- `file` - 文件操作（路径受限）

**请求示例**：

```bash
curl -X POST http://localhost:18080/api/v1/agents/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "data_analyst",
    "display_name": "数据分析师",
    "description": "擅长数据分析和可视化",
    "agent_type": "tool",
    "system_prompt": "你是一个专业的数据分析师...",
    "knowledge_base_ids": ["kb-001", "kb-002"],
    "tools": ["calculator", "knowledge_search"],
    "config": {
      "temperature": 0.7,
      "max_steps": 10,
      "timeout": 300
    },
    "llm_model_id": "model-123",
    "enable_knowledge": true
  }'
```

**成功响应** (200):

```json
{
  "id": "6659a670-3a71-4f61-bc4c-9a454c000b0e",
  "name": "data_analyst",
  "display_name": "数据分析师",
  "description": "擅长数据分析和可视化",
  "agent_type": "tool",
  "system_prompt": "你是一个专业的数据分析师...",
  "knowledge_base_ids": ["kb-001", "kb-002"],
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
  "created_by": "user-001",
  "created_at": "2026-02-02T12:00:00",
  "updated_at": "2026-02-02T12:00:00"
}
```

**错误响应**：

- `400` - 不支持的工具 / LLM 模型不存在 / 参数验证失败
- `401` - 未认证
- `403` - 无权限
- `500` - 服务器错误

---

### 2. 获取 Agent 列表

获取所有 Agent 列表，支持分页、过滤和搜索。

**接口信息**：

- **方法**: `GET`
- **路径**: `/api/v1/agents/`
- **认证**: 需要
- **权限**: 所有用户

**查询参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `page` | integer | ❌ | 1 | 页码（从 1 开始） |
| `limit` | integer | ❌ | 20 | 每页数量（1-100） |
| `agent_type` | string | ❌ | - | 过滤 Agent 类型 |
| `is_active` | boolean | ❌ | - | 过滤激活状态（仅管理员） |
| `search` | string | ❌ | - | 搜索关键词（匹配 name 或 display_name） |

**请求示例**：

```bash
# 获取第一页，每页 20 条
curl http://localhost:18080/api/v1/agents/ \
  -H "Authorization: Bearer <token>"

# 获取第 2 页，每页 10 条
curl http://localhost:18080/api/v1/agents/?page=2&limit=10 \
  -H "Authorization: Bearer <token>"

# 过滤 tool 类型的 Agent
curl http://localhost:18080/api/v1/agents/?agent_type=tool \
  -H "Authorization: Bearer <token>"

# 搜索包含"数据"的 Agent
curl http://localhost:18080/api/v1/agents/?search=数据 \
  -H "Authorization: Bearer <token>"

# 组合查询
curl "http://localhost:18080/api/v1/agents/?page=1&limit=10&agent_type=tool&search=分析" \
  -H "Authorization: Bearer <token>"
```

**成功响应** (200):

```json
{
  "agents": [
    {
      "id": "agent-001",
      "name": "data_analyst",
      "display_name": "数据分析师",
      "description": "擅长数据分析和可视化",
      "agent_type": "tool",
      "system_prompt": "你是一个专业的数据分析师...",
      "knowledge_base_ids": ["kb-001"],
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
      "created_by": "user-001",
      "created_at": "2026-02-02T12:00:00",
      "updated_at": "2026-02-02T12:00:00"
    }
  ],
  "total": 42,
  "page": 1,
  "limit": 20,
  "has_more": true
}
```

**权限说明**：

- **管理员**：可以看到所有 Agent（包括已禁用的）
- **普通用户**：只能看到 `is_active=true` 的 Agent

---

### 3. 获取 Agent 详情

获取指定 Agent 的详细信息。

**接口信息**：

- **方法**: `GET`
- **路径**: `/api/v1/agents/{agent_id}`
- **认证**: 需要
- **权限**: 所有用户

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `agent_id` | string | ✅ | Agent ID |

**请求示例**：

```bash
curl http://localhost:18080/api/v1/agents/agent-001 \
  -H "Authorization: Bearer <token>"
```

**成功响应** (200):

```json
{
  "id": "agent-001",
  "name": "data_analyst",
  "display_name": "数据分析师",
  "description": "擅长数据分析和可视化",
  "agent_type": "tool",
  "system_prompt": "你是一个专业的数据分析师...",
  "knowledge_base_ids": ["kb-001"],
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
  "created_by": "user-001",
  "created_at": "2026-02-02T12:00:00",
  "updated_at": "2026-02-02T12:00:00"
}
```

**错误响应**：

- `404` - Agent 不存在

---

### 4. 更新 Agent

更新指定 Agent 的信息。

**接口信息**：

- **方法**: `PUT`
- **路径**: `/api/v1/agents/{agent_id}`
- **认证**: 需要
- **权限**: 仅管理员

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `agent_id` | string | ✅ | Agent ID |

**请求参数**（所有字段可选）：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ❌ | Agent 名称 |
| `display_name` | string | ❌ | 显示名称 |
| `description` | string | ❌ | 描述信息 |
| `system_prompt` | string | ❌ | 系统提示词 |
| `knowledge_base_ids` | array | ❌ | 关联的知识库 ID 列表 |
| `tools` | array | ❌ | 可用工具列表 |
| `config` | object | ❌ | Agent 配置 |
| `llm_model_id` | string | ❌ | 关联的 LLM 模型 ID |
| `enable_knowledge` | boolean | ❌ | 是否启用知识库 |
| `order` | integer | ❌ | 显示顺序 |
| `is_active` | boolean | ❌ | 是否激活 |

**请求示例**：

```bash
curl -X PUT http://localhost:18080/api/v1/agents/agent-001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "高级数据分析师",
    "description": "擅长复杂数据分析和机器学习",
    "order": 10,
    "enable_knowledge": false
  }'
```

**成功响应** (200):

```json
{
  "id": "agent-001",
  "name": "data_analyst",
  "display_name": "高级数据分析师",
  "description": "擅长复杂数据分析和机器学习",
  "agent_type": "tool",
  "system_prompt": "你是一个专业的数据分析师...",
  "knowledge_base_ids": ["kb-001"],
  "tools": ["calculator", "knowledge_search"],
  "config": {
    "temperature": 0.7,
    "max_steps": 10,
    "timeout": 300
  },
  "llm_model_id": "model-123",
  "llm_model_name": "GLM-4-Flash",
  "enable_knowledge": false,
  "order": 10,
  "is_active": true,
  "created_by": "user-001",
  "created_at": "2026-02-02T12:00:00",
  "updated_at": "2026-02-02T12:30:00"
}
```

**错误响应**：

- `400` - 不支持的工具 / LLM 模型不存在
- `403` - 无权限更新 Agent
- `404` - Agent 不存在

---

### 5. 删除 Agent

删除指定的 Agent。

**接口信息**：

- **方法**: `DELETE`
- **路径**: `/api/v1/agents/{agent_id}`
- **认证**: 需要
- **权限**: 仅管理员

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `agent_id` | string | ✅ | Agent ID |

**请求示例**：

```bash
curl -X DELETE http://localhost:18080/api/v1/agents/agent-001 \
  -H "Authorization: Bearer <token>"
```

**成功响应** (200):

```json
{
  "message": "Agent 删除成功"
}
```

**错误响应**：

- `403` - 无权限删除 Agent
- `404` - Agent 不存在

---

## Agent 交互

### 6. Agent 聊天

与 Agent 进行对话，支持流式输出（SSE）。

**接口信息**：

- **方法**: `POST`
- **路径**: `/api/v1/agents/{agent_id}/chat`
- **认证**: 需要
- **权限**: 所有用户
- **响应类型**: `text/event-stream` (Server-Sent Events)

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `agent_id` | string | ✅ | Agent ID |

**请求参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | string | ✅ | - | 用户查询内容（最大 2000 字符） |
| `session_id` | string | ❌ | - | 会话 ID（可选，用于关联对话） |
| `stream` | boolean | ❌ | true | 是否流式输出 |

**请求示例**：

```bash
curl -X POST http://localhost:18080/api/v1/agents/agent-001/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "帮我分析一下最近一周的销售数据趋势",
    "session_id": "session-123",
    "stream": true
  }'
```

**SSE 事件流**：

```javascript
// 1. 开始事件
data: {"type":"start","execution_id":"exec-456","agent_name":"数据分析师","query":"帮我分析一下最近一周的销售数据趋势","timestamp":"2026-02-02T12:00:00"}

// 2. 推理事件
data: {"type":"reasoning","step":1,"node":"think","reasoning":"我需要搜索知识库来获取销售数据...","tool_decision":{"tool":"knowledge_search","parameters":{"query":"销售数据"}},"timestamp":"2026-02-02T12:00:01"}

// 3. 工具调用事件
data: {"type":"tool_call","tool":"knowledge_search","parameters":{"query":"销售数据","top_k":5},"result":"找到 5 条相关记录...","timestamp":"2026-02-02T12:00:03"}

// 4. 完成事件
data: {"type":"complete","output":"根据最近一周的销售数据分析，总体趋势呈上升态势...","steps":3,"duration":5.2,"timestamp":"2026-02-02T12:00:06"}

// 5. 结束标记
data: [DONE]
```

**事件类型说明**：

| 事件类型 | 说明 | 字段 |
|---------|------|------|
| `start` | 开始执行 | `execution_id`, `agent_name`, `query`, `timestamp` |
| `reasoning` | 推理过程 | `step`, `node`, `reasoning`, `tool_decision`, `timestamp` |
| `tool_call` | 工具调用 | `tool`, `parameters`, `result`, `timestamp` |
| `complete` | 执行完成 | `output`, `steps`, `duration`, `timestamp` |
| `error` | 执行错误 | `error`, `timestamp` |

**前端处理示例**（JavaScript）：

```javascript
const response = await fetch('/api/v1/agents/agent-001/chat', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: '帮我分析销售数据',
    session_id: 'session-123'
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = line.slice(6);
      if (data === '[DONE]') continue;

      const event = JSON.parse(data);

      switch (event.type) {
        case 'start':
          console.log('开始执行:', event.execution_id);
          break;
        case 'reasoning':
          console.log('推理:', event.reasoning);
          break;
        case 'tool_call':
          console.log('工具调用:', event.tool, event.parameters);
          break;
        case 'complete':
          console.log('完成:', event.output);
          break;
        case 'error':
          console.error('错误:', event.error);
          break;
      }
    }
  }
}
```

**错误响应**：

- `404` - Agent 不存在或未激活
- `500` - 执行失败

---

### 7. 获取执行历史

获取指定 Agent 的执行历史记录，支持分页。

**接口信息**：

- **方法**: `GET`
- **路径**: `/api/v1/agents/{agent_id}/executions`
- **认证**: 需要
- **权限**: 所有用户

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `agent_id` | string | ✅ | Agent ID |

**查询参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `page` | integer | ❌ | 1 | 页码（从 1 开始） |
| `limit` | integer | ❌ | 50 | 每页数量（1-100） |

**请求示例**：

```bash
curl "http://localhost:18080/api/v1/agents/agent-001/executions?page=1&limit=10" \
  -H "Authorization: Bearer <token>"
```

**成功响应** (200):

```json
{
  "executions": [
    {
      "id": "exec-001",
      "agent_id": "agent-001",
      "user_id": "user-123",
      "session_id": "session-456",
      "message_id": "msg-789",
      "input_prompt": "帮我分析销售数据",
      "status": "completed",
      "steps": 3,
      "result": "根据分析，销售数据呈上升趋势...",
      "error_message": null,
      "execution_log": [
        {
          "step": 1,
          "tool": "knowledge_search",
          "parameters": {"query": "销售数据"},
          "result": "找到 5 条相关记录..."
        }
      ],
      "reasoning_steps": [
        {
          "step": 1,
          "node": "think",
          "reasoning": "需要搜索知识库获取销售数据"
        }
      ],
      "started_at": "2026-02-02T12:00:00",
      "completed_at": "2026-02-02T12:00:05"
    }
  ],
  "total": 42,
  "page": 1,
  "limit": 10,
  "has_more": true
}
```

**执行状态说明**：

| 状态 | 说明 |
|------|------|
| `running` | 正在执行 |
| `completed` | 执行完成 |
| `failed` | 执行失败 |

**错误响应**：

- `404` - Agent 不存在

---

### 8. 获取消息执行记录

获取指定消息关联的 Agent 执行记录。

**接口信息**：

- **方法**: `GET`
- **路径**: `/api/v1/agents/messages/{message_id}/execution`
- **认证**: 需要
- **权限**: 所有用户

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `message_id` | string | ✅ | 消息 ID |

**请求示例**：

```bash
curl http://localhost:18080/api/v1/agents/messages/msg-789/execution \
  -H "Authorization: Bearer <token>"
```

**成功响应** (200):

```json
{
  "id": "exec-001",
  "agent_id": "agent-001",
  "user_id": "user-123",
  "session_id": "session-456",
  "message_id": "msg-789",
  "input_prompt": "帮我分析销售数据",
  "status": "completed",
  "steps": 3,
  "result": "根据分析，销售数据呈上升趋势...",
  "error_message": null,
  "execution_log": [
    {
      "step": 1,
      "tool": "knowledge_search",
      "parameters": {"query": "销售数据"},
      "result": "找到 5 条相关记录..."
    }
  ],
  "reasoning_steps": [
    {
      "step": 1,
      "node": "think",
      "reasoning": "需要搜索知识库获取销售数据"
    }
  ],
  "started_at": "2026-02-02T12:00:00",
  "completed_at": "2026-02-02T12:00:05"
}
```

**错误响应**：

- `404` - 消息不存在或无关联执行记录

---

## 工具与服务

### 9. 获取可用工具

获取所有可用的 Agent 工具列表。

**接口信息**：

- **方法**: `GET`
- **路径**: `/api/v1/agents/tools`
- **认证**: 不需要
- **权限**: 公开

**请求示例**：

```bash
curl http://localhost:18080/api/v1/agents/tools
```

**成功响应** (200):

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
      "description": "读写文件、列出目录（路径受限）",
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

**工具分类说明**：

| 分类 | 说明 | 工具 |
|------|------|------|
| `knowledge` | 知识相关 | `knowledge_search` |
| `calculation` | 计算相关 | `calculator` |
| `system` | 系统工具 | `datetime`, `code_executor`, `file` |
| `search` | 搜索工具 | `browser` |

---

### 10. 健康检查

检查 Agent 服务的健康状态。

**接口信息**：

- **方法**: `GET`
- **路径**: `/api/v1/agents/service-health`
- **认证**: 不需要
- **权限**: 公开

**请求示例**：

```bash
curl http://localhost:18080/api/v1/agents/service-health
```

**成功响应** (200):

```json
{
  "status": "healthy",
  "tools_registered": 6,
  "timestamp": "2026-02-02T12:00:00.123456"
}
```

**错误响应** (503):

```json
{
  "status": "unhealthy",
  "error": "Agent service initialization failed",
  "timestamp": "2026-02-02T12:00:00.123456"
}
```

---

## 数据模型

### Agent 对象

```typescript
{
  id: string;                    // Agent ID (UUID)
  name: string;                  // Agent 名称（唯一标识）
  display_name: string;          // 显示名称
  description: string;           // 描述信息
  agent_type: string;            // Agent 类型: "rag" | "tool" | "custom"
  system_prompt: string;         // 系统提示词
  knowledge_base_ids: string[];  // 关联的知识库 ID 列表
  tools: string[];               // 可用工具列表
  config: {                      // Agent 配置
    temperature: number;         // 0-2，默认 0.7
    max_steps: number;           // 1-50，默认 10
    timeout: number;             // 超时时间（秒），默认 300
  };
  llm_model_id: string;          // 关联的 LLM 模型 ID
  llm_model_name: string;        // LLM 模型名称（自动填充）
  enable_knowledge: boolean;     // 是否启用知识库
  order: number;                 // 显示顺序
  is_active: boolean;            // 是否激活
  created_by: string;            // 创建者 ID
  created_at: string;            // 创建时间（ISO 8601）
  updated_at: string;            // 更新时间（ISO 8601）
}
```

### AgentExecution 对象

```typescript
{
  id: string;              // 执行记录 ID (UUID)
  agent_id: string;        // Agent ID
  user_id: string;         // 用户 ID
  session_id: string;      // 会话 ID（可选）
  message_id: string;      // 关联的消息 ID
  input_prompt: string;    // 用户输入
  status: string;          // 状态: "running" | "completed" | "failed"
  steps: number;           // 执行步数
  result: string;          // 执行结果
  error_message: string;   // 错误信息
  execution_log: Array<{   // 工具调用日志
    step: number;
    tool: string;
    parameters: object;
    result: string;
  }>;
  reasoning_steps: Array<{ // 推理步骤
    step: number;
    node: string;
    reasoning: string;
    tool_decision?: object;
  }>;
  started_at: string;      // 开始时间（ISO 8601）
  completed_at: string;    // 完成时间（ISO 8601，可选）
}
```

---

## Agent 工具详细说明

### 1. 知识库检索 (knowledge_search)

在指定的知识库中搜索信息，使用向量相似度搜索。

**参数**：
- `query` (string, 必填): 搜索查询
- `knowledge_base_ids` (array, 必填): 知识库 ID 列表
- `top_k` (integer, 可选): 返回结果数量，默认 5
- `user_id` (string, 可选): 用户 ID（用于权限验证）

**返回值**：
```json
{
  "query": "搜索关键词",
  "total_results": 5,
  "context": "格式化的上下文文本",
  "sources": ["文件1.pdf", "文档2.docx"],
  "results": [
    {
      "content": "内容片段",
      "filename": "文件名",
      "similarity": 0.95,
      "chunk_index": 0
    }
  ]
}
```

**安全限制**：
- 必须选择至少一个知识库
- 自动验证用户权限
- 限制返回结果数量

---

### 2. 计算器 (calculator)

执行数学计算，支持基本运算。

**参数**：
- `expression` (string, 必填): 数学表达式

**支持的操作**：
- 基本运算：`+`, `-`, `*`, `/`
- 括号：`()`
- 小数点：`.`

**返回值**：
- 成功：计算结果（number）
- 失败：错误信息字符串

**示例**：
```javascript
// 简单计算
"2 + 3 * 4"  // 返回 14

// 复杂表达式
"(100 + 50) / 2"  // 返回 75

// 错误处理
"100 / 0"  // 返回 "错误：除数不能为零"
```

**安全限制**：
- 使用正则表达式验证表达式合法性
- 限制只能使用特定的数学运算字符
- 使用受限的 eval 环境

---

### 3. 当前时间 (datetime)

获取当前日期和时间信息。

**参数**：
- 无

**返回值**：
```json
{
  "datetime": "2026-02-02T10:30:45",
  "date": "2026-02-02",
  "time": "10:30:45",
  "year": 2026,
  "month": 2,
  "day": 2,
  "hour": 10,
  "minute": 30,
  "second": 45,
  "weekday": 1,
  "weekday_name": "Tuesday",
  "timezone": "Asia/Shanghai"
}
```

**安全限制**：
- 无权限风险
- 只读取系统时间

---

### 4. 代码执行 (code_executor)

在沙箱环境中安全执行 Python 代码。

**参数**：
- `code` (string, 必填): 要执行的 Python 代码
- `timeout` (integer, 可选): 超时时间（秒），默认 30

**允许的模块**：
- `math`, `datetime`, `json`, `re`, `collections`, `itertools`, `random`, `statistics`

**允许的内置函数**：
- `print`, `len`, `range`, `str`, `int`, `float`, `bool`, `list`, `dict`, `tuple`, `set`, `sum`, `max`, `min`, `abs`, `round`, `sorted`, `enumerate`, `zip`, `map`, `filter`, `any`, `all`, `isinstance`, `type`

**禁止的操作**：
- 文件系统操作（`import os`, `open` 等）
- 进程操作（`import subprocess`）
- 危险函数（`eval`, `exec globals`, `locals` 等）
- 网络操作

**返回值**：
```json
{
  "success": true,
  "output": "执行结果",
  "error": null,
  "execution_time": 1.23
}
```

**示例**：
```python
# 简单计算
x = 10 + 5
print(x)  # 输出: 15

# 数学计算
import math
result = math.sqrt(100)
print(f"平方根: {result}")  # 输出: 平方根: 10.0
```

**安全限制**：
- 沙箱隔离环境
- 严格的安全检查
- 超时保护
- 限制危险模块和函数

---

### 5. 浏览器 (browser)

服务端无头浏览器，基于 Playwright，支持网页操作。

**参数**：
- `action` (string, 必填): 操作类型
  - `navigate`: 导航到 URL
  - `screenshot`: 截图
  - `click`: 点击元素
  - `fill`: 填写表单
  - `scrape`: 抓取页面文本
  - `search`: 搜索引擎搜索（百度）
- `url` (string, 可选): 目标 URL
- `selector` (string, 可选): CSS 选择器
- `text` (string, 可选): 文本内容（用于填写或搜索）
- `wait_time` (integer, 可选): 等待时间（毫秒），默认 3000

**返回值**：
```json
// 导航操作
{
  "success": true,
  "data": {
    "url": "https://example.com",
    "title": "页面标题"
  }
}

// 搜索操作
{
  "success": true,
  "data": {
    "query": "搜索关键词",
    "results": [
      {
        "rank": 1,
        "title": "结果标题",
        "url": "https://example.com",
        "snippet": "摘要内容"
      }
    ],
    "count": 10,
    "engine": "baidu"
  }
}
```

**示例**：
```javascript
// 导航网页
{action: "navigate", url: "https://example.com"}

// 抓取内容
{action: "scrape", url: "https://example.com"}

// 搜索
{action: "search", text: "Python编程"}

// 点击元素
{action: "click", selector: "button#submit"}
```

**安全限制**：
- 只使用无头模式，不显示界面
- 支持并发访问，有锁保护
- 限制内容抓取长度（10,000 字符）
- 超时控制（30 秒）

---

### 6. 文件操作 (file)

安全的文件读写操作，支持路径访问限制。

**参数**：
- `action` (string, 必填): 操作类型
  - `read`: 读取文件
  - `write`: 写入文件
  - `list`: 列出目录
  - `exists`: 检查文件是否存在
  - `delete`: 删除文件
- `path` (string, 必填): 文件/目录路径
- `content` (string, 可选): 文件内容（用于 write）
- `allowed_dirs` (list, 可选): 允许访问的目录列表

**默认允许目录**：
- `/tmp`
- `/uploads`
- `/agent_workspace`

**返回值**：
```json
// 读取文件
{
  "success": true,
  "data": {
    "path": "/path/to/file.txt",
    "content": "文件内容",
    "size": 1024
  }
}

// 列出目录
{
  "success": true,
  "data": {
    "path": "/path/to/directory",
    "items": [
      {
        "name": "file.txt",
        "path": "/path/to/directory/file.txt",
        "type": "file",
        "size": 1024
      }
    ],
    "count": 5
  }
}
```

**示例**：
```javascript
// 读取文件
{action: "read", path: "/tmp/test.txt"}

// 写入文件
{action: "write", path: "/tmp/test.txt", content: "Hello, World"}

// 列出目录
{action: "list", path: "/tmp"}
```

**安全限制**：
- 默认允许目录列表控制
- 相对路径自动转换为工作目录路径
- 严格路径检查，防止目录遍历攻击
- 只能访问白名单目录

---

## 错误码

| HTTP 状态码 | 错误类型 | 说明 |
|-------------|---------|------|
| `200` | Success | 请求成功 |
| `400` | Bad Request | 请求参数错误 / 不支持的工具 / LLM 模型不存在 |
| `401` | Unauthorized | 未认证 / Token 无效 |
| `403` | Forbidden | 无权限 |
| `404` | Not Found | Agent 不存在 |
| `500` | Internal Server Error | 服务器错误 |
| `503` | Service Unavailable | Agent 服务不健康 |

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

或（部分接口）

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

---

## 附录

### A. 前端调用示例

```typescript
import { agentService } from './services/agentService';

// 1. 获取 Agent 列表
const agents = await agentService.getAgents();
console.log('Agent 列表:', agents);

// 2. 创建 Agent
const newAgent = await agentService.createAgent({
  name: 'my-agent',
  display_name: '我的 Agent',
  description: '这是一个测试 Agent',
  agent_type: 'tool',
  tools: ['calculator', 'datetime']
});

// 3. Agent 聊天（流式）
for await (const event of await agentService.agentChat(newAgent.id, {
  query: '帮我计算 123 + 456',
  session_id: 'session-123'
})) {
  switch (event.type) {
    case 'reasoning':
      console.log('推理:', event.reasoning);
      break;
    case 'tool_call':
      console.log('工具调用:', event.tool, event.parameters);
      break;
    case 'complete':
      console.log('最终答案:', event.output);
      break;
    case 'error':
      console.error('错误:', event.error);
      break;
  }
}

// 4. 获取执行历史
const executions = await agentService.getAgentExecutions(newAgent.id, 10);
console.log('执行历史:', executions);
```

### B. Agent 工作流程

Agent 使用 LangGraph 实现状态机，工作流程如下：

```
1. Plan 节点（规划）
   ├─ 使用 TaskPlanner 将复杂任务分解为子任务
   ├─ 生成执行计划（execution_plan）
   └─ 设置当前子任务

2. Think 节点（思考）
   ├─ 使用 LLMReasoner 进行推理
   ├─ 决定是否使用工具及使用哪个工具
   └─ 生成 reasoning 链和 tool_decision

3. Act 节点（行动）
   ├─ 执行 LLM 决定的工具
   ├─ 记录工具调用结果
   └─ 支持参数增强

4. Observe 节点（观察）
   ├─ 判断是否继续循环
   ├─ 生成最终答案
   └─ 支持子任务切换
```

### C. Swagger 文档

交互式 API 文档：`http://localhost:18080/docs`

### D. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 0.1.0 | 2026-01-29 | 初始版本 |
| 1.0.0 | 2026-02-02 | 正式版本，新增工具和接口 |

---

## 联系方式

- **项目**: Bright-Chat
- **文档版本**: 1.0.0
- **最后更新**: 2026-02-02
- **基础路径**: `/api/v1/agents`
- **服务器端口**: `18080`（本地开发）

---

**注意事项**：

1. 所有时间字段使用 **ISO 8601** 格式（如：`2026-02-02T12:00:00`）
2. 所有 ID 字段使用 **UUID** 格式
3. 分页参数从 **1** 开始计数
4. Agent 名称在系统中必须**唯一**
5. 只有**管理员**可以创建、更新、删除 Agent
6. 流式接口使用 **Server-Sent Events (SSE)** 协议
7. 新增了 3 个高级工具：`code_executor`, `browser`, `file`
8. 新增了 `reasoning` 事件类型，用于显示 Agent 推理过程
9. 新增了通过 `message_id` 查询执行记录的接口
10. AgentExecution 新增了 `reasoning_steps` 和 `message_id` 字段
