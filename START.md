# Bright-Chat 本地启动指南

## 快速启动

### 1. 后端 Backend (Python/FastAPI)
```bash
cd backend-python
source venv/bin/activate
python minimal_api.py
```
访问: http://localhost:18080

### 2. 前端 Frontend (React/TypeScript)
```bash
cd frontend
npm run dev
```
访问: http://localhost:3000

### 3. Mock 服务器 (可选，用于离线开发)
```bash
cd mockserver
python start.py
```
访问: http://localhost:8080

---

## 服务信息

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:3000 | React 应用 |
| 后端 | http://localhost:18080 | FastAPI 服务 |
| API 文档 | http://localhost:18080/docs | Swagger |
| 健康检查 | http://localhost:18080/health | 后端健康状态 |

## 默认账号
- 用户名: `admin`
- 密码: `pwd123`

## 注意事项
- 前端配置文件 `frontend/config/index.ts` 中 `USE_MOCK: false` 表示连接真实后端
- 首次运行后端需确保数据库连接配置正确 (config/.env)
