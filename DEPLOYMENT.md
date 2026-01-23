# BrightChat AI工作台 - Docker 部署指南

本文档介绍如何使用 Docker 容器化部署 BrightChat AI工作台应用。

---

## 前置要求

### 必需软件

- **Docker**: 版本 20.10 或更高
- **Docker Compose**: 版本 2.0 或更高（或作为 Docker 插件）

### 检查安装

```bash
docker --version
docker compose version  # 或 docker-compose --version
```

---

## 快速开始

### 1. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件，修改默认密码
vim .env  # 或使用其他编辑器
```

**重要配置项**：
- `MYSQL_ROOT_PASSWORD`: MySQL root 密码（必须修改）
- `MYSQL_PASSWORD`: 应用数据库密码（必须修改）
- `JWT_SECRET_KEY`: JWT 认证密钥（必须修改，至少32字符）

### 2. 一键部署

```bash
# 赋予执行权限（首次运行）
chmod +x deploy.sh stop-deploy.sh

# 运行部署脚本
./deploy.sh
```

部署脚本会自动完成以下操作：
1. 检查 Docker 环境
2. 创建必要的目录
3. 构建 Docker 镜像
4. 启动所有服务
5. 等待服务就绪
6. 显示访问地址

### 3. 访问应用

部署成功后，访问以下地址：

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端应用 | http://localhost | AI工作台主界面 |
| API 文档 | http://localhost:18080/docs | Swagger API 文档 |
| 健康检查 | http://localhost/health | 服务健康状态 |

---

## 服务架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Nginx (反向代理)                          │
│                   端口 80 (HTTP) / 443 (HTTPS)                │
└──────────────────────────┬──────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
┌───────────────────┐          ┌───────────────────┐
│   Frontend        │          │   Backend         │
│   (React+Vite)     │          │   (FastAPI)       │
│   端口 8080         │          │   端口 18080      │
└───────────────────┘          └─────────┬───────────┘
                                       │
            ┌──────────────────────┴────────┐
            ▼                             ▼
    ┌─────────────┐           ┌─────────────┐
    │  MySQL      │           │   Redis     │
    │  端口 13306 │           │   端口 6379 │
    └─────────────┘           └─────────────┘
```

---

## 常用命令

### 服务管理

```bash
# 启动服务
docker compose up -d

# 停止服务（保留数据）
./stop-deploy.sh

# 停止服务（删除数据）
docker compose down -v

# 重启服务
docker compose restart [service_name]

# 查看服务状态
docker compose ps
```

### 日志查看

```bash
# 查看所有日志
docker compose logs

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend

# 实时跟踪日志
docker compose logs -f --tail=100
```

### 数据库操作

```bash
# 进入 MySQL 容器
docker exec -it bright-chat-mysql mysql -u bright_chat -p

# 备份数据库
docker exec bright-chat-mysql mysqldump -u root -p bright_chat > backup.sql

# 恢复数据库
docker exec -i bright-chat-mysql mysql -u root -p bright_chat < backup.sql
```

---

## 数据持久化

所有应用数据存储在 Docker volumes 中：

| Volume | 说明 |
|--------|------|
| `mysql_data` | MySQL 数据库文件 |
| `redis_data` | Redis 持久化数据 |
| `backend_logs` | 后端应用日志 |
| `nginx_logs` | Nginx 访问日志 |

### 备份数据

```bash
# 备份所有 volumes
docker run --rm -v bright-chat_mysql_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/mysql-backup.tar.gz -C /data .

docker run --rm -v bright-chat_redis_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/redis-backup.tar.gz -C /data .
```

---

## 故障排查

### 服务无法启动

1. 检查端口占用：
```bash
lsof -i :80
lsof -i :18080
```

2. 检查服务状态：
```bash
docker compose ps
```

3. 查看详细日志：
```bash
docker compose logs [service_name]
```

### 健康检查失败

```bash
# 手动检查健康状态
curl http://localhost/health
curl http://localhost:18080/health

# 查看容器健康状态
docker inspect --format='{{.State.Health.Status}}' bright-chat-backend
```

### 数据库连接失败

确保环境变量中的数据库密码与 `.env` 文件一致：
```bash
docker compose exec backend env | grep DB_
```

---

## 生产环境建议

### 安全加固

1. **修改默认密码**：所有默认密码必须修改
2. **启用 HTTPS**：配置 SSL 证书
3. **限制端口暴露**：仅暴露必要端口
4. **定期更新镜像**：保持依赖安全

### 性能优化

1. **调整 workers 数量**：根据 CPU 核心数设置 `SERVER_WORKERS`
2. **启用缓存**：确保 Redis 正常运行
3. **配置 CDN**：静态资源建议使用 CDN

### 监控建议

1. 配置日志聚合（如 ELK Stack）
2. 设置资源监控（如 Prometheus + Grafana）
3. 配置告警通知

---

## 端口说明

| 端口 | 服务 | 对外暴露 | 说明 |
|------|------|----------|------|
| 80 | Nginx | ✓ | 主入口端口 |
| 443 | Nginx HTTPS | 可选 | HTTPS 入口 |
| 8080 | Frontend | ✗ | 容器间通信 |
| 18080 | Backend | ✗ | 容器间通信 |
| 13306 | MySQL | 可选 | 数据库访问 |
| 6379 | Redis | 可选 | 缓存访问 |

---

## 许可证

Copyright © BrightChat Team
