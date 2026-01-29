# BrightChat

> 全功能 AI 聊天应用工作台，支持实时 LLM 集成、用户管理、模型管理、知识库(RAG)和 Agent 功能

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-brightgreen.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-19.0-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0-blue.svg)](https://www.typescriptlang.org/)

---

## 项目简介

BrightChat 是一个现代化的全栈 AI 聊天应用，支持多种 LLM 模型、流式响应、知识库检索和智能 Agent 功能。

### 核心功能

- **多模型支持** - 集成多家 LLM 提供商（OpenAI、Anthropic、智谱 AI、自定义模型）
- **流式对话** - 实时流式响应，支持长文本生成
- **用户管理** - 角色权限控制（管理员/普通用户）
- **知识库 RAG** - 基于 ChromaDB 的文档检索和语义搜索
- **智能 Agent** - 基于 LangGraph 的工具调用 Agent
- **消息收藏** - 重要消息书签和备注

---

## 技术栈

| 模块 | 技术栈 |
|------|--------|
| 前端 | React 19 + TypeScript 5 + Vite 6 + Tailwind CSS |
| 后端 | Python 3.11+ + FastAPI + SQLAlchemy |
| 数据库 | MySQL (port 13306) |
| 向量库 | ChromaDB (port 8002) |
| 部署 | Docker Compose + Nginx |
| Agent | LangGraph + LangChain |
| 嵌入模型 | BGE-large-zh-v1.5 (Sentence Transformers) |

---

## 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/your-org/Bright-Chat.git
cd Bright-Chat

# 一键启动
docker compose up -d

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f --tail=100
```

**访问地址**：
- 主应用: http://localhost:9003
- 后端 API: http://localhost:18080
- API 文档: http://localhost:18080/docs

**默认账户**：
- 用户名: `admin`
- 密码: `pwd123`

### 方式二：本地开发

#### 后端启动

```bash
cd backend-python

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动 ChromaDB (Docker)
docker run -d -p 8002:8000 --name bright-chat-chromadb chromadb/chroma:latest

# 启动后端
python minimal_api.py
```

#### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 访问 http://localhost:3000
```

---

## 项目结构

```
Bright-Chat/
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/        # React 组件
│   │   ├── services/          # API 服务层
│   │   ├── hooks/             # 自定义 Hooks
│   │   ├── types.ts           # TypeScript 类型
│   │   └── App.tsx            # 根组件
│   ├── package.json
│   └── vite.config.ts
│
├── backend-python/             # Python 后端
│   ├── app/
│   │   ├── agents/            # Agent 模块 (LangGraph)
│   │   ├── rag/               # RAG 知识库模块
│   │   ├── api/               # API 路由
│   │   ├── models/            # 数据模型
│   │   ├── services/          # 业务服务
│   │   └── core/              # 核心配置
│   ├── minimal_api.py         # 主入口 (单文件实现)
│   └── requirements.txt
│
├── docker-compose.yml          # Docker 编排配置
├── CLAUDE.md                   # 项目完整指南
└── README.md                   # 本文件
```

---

## 环境要求

### Docker 部署
- Docker >= 20.10
- Docker Compose >= 2.0
- 8GB+ 可用内存

### 本地开发
- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- ChromaDB (Docker)

---

## 核心模块

### 1. LLM 聊天

支持多种 LLM 模型的流式对话：

```typescript
// 前端调用示例
const response = await fetch('/api/v1/lmp-cloud-ias-server/api/llm/chat/completions/V2', {
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

// 处理 SSE 流式响应
const reader = response.body.getReader();
// ...
```

### 2. 知识库 RAG

基于 ChromaDB 的文档检索和语义搜索：

- 支持多种文档格式（PDF、DOCX、TXT、MD、HTML、XLS、XLSX、PPT、PPTX）
- BGE-large-zh-v1.5 嵌入模型
- 智能分块和向量索引
- 语义搜索和检索增强生成

### 3. 智能 Agent

基于 LangGraph 的工具调用 Agent：

- **预置工具**: calculator（计算器）、datetime（时间）、knowledge_search（知识库搜索）、code_executor（代码执行）、browser（浏览器）、file（文件操作）
- **Agent 类型**: rag（知识库）、tool（工具调用）、custom（自定义）
- **状态管理**: Think -> Act -> Observe 循环

---

## 文档

| 文档 | 说明 |
|------|------|
| [CLAUDE.md](CLAUDE.md) | 项目完整指南（架构、API、开发规范） |
| [MdDocs/INDEX.md](MdDocs/INDEX.md) | 结构化文档索引 |
| [README_QUICKSTART.md](README_QUICKSTART.md) | 快速启动指南 |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Docker 部署指南 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南 |
| [CHANGELOG.md](CHANGELOG.md) | 更新日志 |

---

## API 端点

### 认证
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/logout` - 用户登出

### 会话管理
- `GET /api/v1/sessions` - 获取会话列表
- `POST /api/v1/sessions` - 创建会话
- `GET /api/v1/sessions/{id}/messages` - 获取消息
- `DELETE /api/v1/sessions/{id}` - 删除会话

### Agent
- `GET /api/v1/agents/` - 获取 Agent 列表
- `POST /api/v1/agents/` - 创建 Agent（管理员）
- `POST /api/v1/agents/{id}/chat` - Agent 对话

### 知识库
- `GET /api/v1/knowledge/bases` - 获取知识库列表
- `POST /api/v1/knowledge/bases` - 创建知识库
- `POST /api/v1/knowledge/bases/{id}/documents` - 上传文档
- `GET /api/v1/knowledge/search` - 语义搜索

**完整 API 文档**: http://localhost:18080/docs (Swagger UI)

---

## 常见问题

### 1. ChromaDB 连接失败

```bash
# 检查 ChromaDB 容器
docker ps | grep chromadb

# 重启 ChromaDB
docker restart bright-chat-chromadb

# 手动启动
docker run -d -p 8002:8000 --name bright-chat-chromadb chromadb/chroma:latest
```

### 2. 后端无法启动

```bash
# 检查数据库连接
docker exec -it bright-chat-mysql mysql -u bright_chat -p -e "SELECT 1"

# 查看后端日志
docker logs -f bright-chat-backend
```

### 3. 登录失败

- 确认使用默认账户 `admin` / `pwd123`
- 检查数据库是否正常初始化
- 查看 [登录问题排查](MdDocs/backend/troubleshooting/login-issues.md)

### 4. 端口冲突

修改 `docker-compose.yml` 中的端口映射：

```yaml
services:
  backend:
    ports:
      - "18080:18080"  # 主机端口:容器端口
```

---

## 开发指南

### 添加新功能

1. **后端**: 在 `backend-python/app/` 添加模块，更新 `minimal_api.py`
2. **前端**: 在 `frontend/services/` 添加 API 调用，更新 `App.tsx`
3. **测试**: 编写测试用例验证功能

### 代码规范

- **不可变性**: 使用展开运算符，避免对象 mutation
- **错误处理**: 所有 API 调用必须处理错误
- **输入验证**: 使用 Zod 或类似库验证用户输入
- **命名**: 使用清晰、描述性的变量名

详见 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [.claude/rules/](.claude/rules/)。

---

## 安全建议

### 生产环境必做

1. **修改默认密码**
   - MySQL root 密码
   - 应用数据库密码
   - JWT_SECRET_KEY

2. **限制端口暴露**
   - 只开放 80/443 端口
   - 内网服务不暴露到公网

3. **启用 HTTPS**
   - 配置有效的 SSL 证书

4. **定期更新**
   - 更新 Docker 镜像
   - 安装安全补丁

---

## 许可证

MIT License

---

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

---

**最后更新**: 2026-01-29
**版本**: v1.0
