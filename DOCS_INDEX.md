# Bright-Chat 文档索引

> 项目文档快速导航指南

## 📚 核心文档

### 项目概览
- **[README.md](README.md)** - 项目介绍、功能特性和快速开始
- **[CLAUDE.md](CLAUDE.md)** - Claude Code 项目指南（架构、开发流程、API 文档）
- **[CHANGELOG.md](CHANGELOG.md)** - 版本变更记录

### 开发指南
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - 贡献指南和开发规范
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - 部署指南和运维文档
- **[PROGRESS.md](PROGRESS.md)** - 项目进度和任务跟踪

## 🔌 API 文档

### 核心 API
- **[API 文档](docs/API.md)** - 认证、用户、会话、模型等通用接口
- **[智能体接口文档](docs/AGENT_API.md)** - Agent 管理、聊天、工具使用（v1.0 正式版）
- **[知识库接口文档](docs/知识库接口文档(正式).md)** - 知识库 CRUD、文档上传、向量搜索

### 交互式文档
- **Swagger UI**: `http://localhost:18080/docs` - 交互式 API 测试
- **ReDoc**: `http://localhost:18080/redoc` -精美的 API 参考文档

## 🛠️ 部署脚本

### Docker 部署
```bash
./deploy.sh              # 一键部署所有服务
./stop-deploy.sh         # 停止所有服务
```

### 本地开发
```bash
./start-local.sh         # 启动本地开发环境
./stop-local.sh          # 停止本地开发环境
```

### 服务检查
```bash
./check-services.sh      # 检查所有服务状态
./verify-services.sh     # 验证服务健康状态
```

## 🏗️ 项目架构

### 技术栈
- **前端**: React 19 + TypeScript + Vite 6
- **后端**: Python 3.11 + FastAPI + SQLAlchemy
- **数据库**: MySQL (端口 13306)
- **向量数据库**: ChromaDB (端口 8002)
- **部署**: Docker Compose + Nginx

### 核心模块
```
backend-python/app/
├── agents/       # Agent 模块（LangGraph）
├── rag/          # RAG 知识库
├── models/       # 数据模型
└── core/         # 核心工具
```

详细架构说明参见 [CLAUDE.md - Architecture Overview](CLAUDE.md#architecture-overview)

## 🧪 测试

### 后端测试
```bash
cd backend-python
pytest -v                    # 运行所有测试
pytest tests/test_agent_api.py -v  # 运行特定测试
```

### E2E 测试
```bash
cd e2e-tests
npm run test                 # 运行 Playwright E2E 测试
```

## 📖 常见问题

### 快速链接
- [数据库迁移](CLAUDE.md#database-migration-after-schema-changes)
- [Agent 开发](CLAUDE.md#agent-development)
- [知识库开发](CLAUDE.md#knowledge-base-development)
- [故障排查](CLAUDE.md#troubleshooting)

## 🔧 配置文件

### 环境变量
- `.env` - Docker 部署环境变量
- `.env.rag` - RAG 配置
- `backend-python/app/core/config.py` - 后端配置
- `frontend/config/index.ts` - 前端配置

### 服务端口
| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx | 80, 443 | 主入口 |
| Frontend | 3000 | Vite 开发服务器 |
| Backend | 18080 | FastAPI 后端 |
| MySQL | 13306 | 数据库 |
| Redis | 6379 | 缓存 |
| ChromaDB | 8002 | 向量数据库 |

## 📝 文档维护

### 添加新文档
1. 在适当的位置创建文档文件
2. 更新本索引文件
3. 在相关文档中添加交叉引用

### 文档规范
- 使用清晰的标题层级
- 提供代码示例和命令
- 包含相关链接和引用
- 保持与代码同步更新

---

**最后更新**: 2026-02-02
