# 前后端联调测试报告

## 测试时间
2026-01-28 09:30

## 发现的问题

### 1. 前后端API不匹配 ⚠️
前端调用：`GET /api/v1/knowledge/groups/{groupId}/bases`
后端实际：`GET /api/v1/knowledge/bases`

**需要修复：** 修改 frontend/services/knowledgeService.ts

### 2. ChromaDB环境变量问题 ⚠️
需要设置：
```bash
export CHROMADB_HOST=localhost
export CHROMADB_PORT=8002
export RAG_USE_CHROMADB_EMBEDDING=true  # 使用内置模型
```

## 测试通过的功能 ✅
- 用户登录认证
- 用户管理CRUD
- 知识库分组CRUD
- 知识库CRUD
- 文档上传
- ChromaDB连接

## 快速修复步骤
1. 修复前端 knowledgeService.ts
2. 设置环境变量
3. 重启后端测试

详见报告内容。
