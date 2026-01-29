# BrightChat + Agent Service 部署实施指南

## 概述

本文档提供数字员工智能体服务（agent-service）集成到 BrightChat 主项目的完整实施步骤。

---

## 配置验证报告

### 系统配置

- **配置文件**: docker-compose.yml.merged
- **服务总数**: 7 个
- **网络**: AIWorkbench-network (bridge)
- **数据卷**: 6 个

### 端口分配

| 服务 | 容器端口 | 主机端口 | 变量名 | 状态 |
|------|---------|---------|--------|------|
| mysql | 3306 | 13306 | MYSQL_PORT | OK |
| redis | 6379 | 6379 | REDIS_PORT | OK |
| elasticsearch | 9200 | 9200 | ES_PORT | OK |
| backend | 18080 | 18080 | BACKEND_PORT | OK |
| frontend | 3000 | 8080 | FRONTEND_PORT | OK |
| nginx (HTTP) | 80 | 9003 | NGINX_HTTP_PORT | OK |
| nginx (HTTPS) | 443 | 443 | NGINX_HTTPS_PORT | OK |
| agent-service | 8000 | 8000 | AGENT_SERVICE_PORT | OK |

**冲突检测**: 无端口冲突

### 健康检查

所有 7 个服务均已配置健康检查：
- mysql (mysqladmin ping)
- redis (redis-cli ping)
- elasticsearch (cluster health API)
- backend (HTTP /health)
- frontend (HTTP /health)
- nginx (HTTP /health)
- agent-service (HTTP /health)

### 服务依赖

```
elasticsearch (健康)
    └── agent-service

mysql (健康)
redis (健康)
    ├── backend
    │       └── frontend
    │               └── nginx
```

---

## 部署步骤

### 步骤 1: 环境准备

```bash
cd /data1/allresearchProject/Bright-Chat
```

### 步骤 2: 配置环境变量

编辑 `.env` 文件，确保以下变量正确配置：

```bash
# 必需：Agent Service API 密钥
ZHIPU_API_KEY=your_actual_api_key_here
ZHIPU_API_URL=https://open.bigmodel.cn/api/coding/paas/v4/chat/completions
ZHIPU_MODEL=glm-4.7
```

### 步骤 3: 应用配置

```bash
# 方法 1: 使用部署脚本（推荐）
./deploy-merged.sh

# 方法 2: 手动应用
cp docker-compose.yml.merged docker-compose.yml
cp .env.merged .env
```

### 步骤 4: 启动服务

```bash
# 拉取镜像
docker-compose pull

# 构建镜像
docker-compose build

# 启动所有服务
docker-compose up -d
```

### 步骤 5: 验证部署

```bash
# 查看容器状态
docker-compose ps

# 运行健康检查
./verify-services.sh

# 查看日志
docker-compose logs -f
```

---

## 验证检查清单

### 基础检查

- [ ] 所有 7 个容器状态为 "Up"
- [ ] 所有容器在 AIWorkbench-network 中
- [ ] 无端口冲突
- [ ] 所有数据卷已创建

### 服务检查

- [ ] MySQL 响应: `mysql -h localhost -P 13306 -u root -p`
- [ ] Redis 响应: `redis-cli -h localhost -p 6379 ping`
- [ ] Elasticsearch 响应: `curl http://localhost:9200/_cluster/health`
- [ ] Backend 响应: `curl http://localhost:18080/health`
- [ ] Frontend 响应: `curl http://localhost:8080`
- [ ] Nginx 响应: `curl http://localhost:9003`
- [ ] Agent Service 响应: `curl http://localhost:8000/health`

### 功能检查

- [ ] 前端界面可访问: http://localhost:9003
- [ ] 后端 API 可访问: http://localhost:18080/docs
- [ ] Agent Service API 可访问: http://localhost:8000
- [ ] Elasticsearch 索引已创建

---

## 访问地址

| 服务 | URL | 用途 |
|------|-----|------|
| **主应用** | http://localhost:9003 | BrightChat 前端界面 |
| **后端 API** | http://localhost:18080 | REST API |
| **API 文档** | http://localhost:18080/docs | Swagger 文档 |
| **Agent API** | http://localhost:8000 | 数字员工服务 |
| **Elasticsearch** | http://localhost:9200 | 搜索引擎 |

---

## 故障排查

### 问题 1: 容器启动失败

**检查步骤**:

```bash
# 1. 查看容器日志
docker-compose logs <service_name>

# 2. 检查容器状态
docker-compose ps -a

# 3. 检查资源使用
docker stats

# 4. 检查系统日志
journalctl -u docker -n 50
```

### 问题 2: 服务无法通信

**检查步骤**:

```bash
# 1. 检查网络
docker network inspect AIWorkbench-network

# 2. 测试容器间连接
docker exec AIWorkbench-agent-service ping mysql
docker exec AIWorkbench-agent-service curl http://elasticsearch:9200

# 3. 检查防火墙
sudo iptables -L -n
```

### 问题 3: Elasticsearch 启动失败

**常见原因**:
- 内存不足（至少需要 1GB）
- vm.max_map_count 太低

**解决方案**:

```bash
# 调整系统参数
sudo sysctl -w vm.max_map_count=262144

# 永久生效
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 重启 Elasticsearch
docker-compose restart elasticsearch
```

### 问题 4: Agent Service 无法连接

**检查步骤**:

```bash
# 1. 确认 Elasticsearch 状态
docker-compose logs elasticsearch

# 2. 检查环境变量
docker-compose exec agent-service env | grep ES

# 3. 测试连接
docker-compose exec agent-service curl http://elasticsearch:9200

# 4. 检查 API 密钥
docker-compose exec agent-service env | grep ZHIPU
```

---

## 回滚步骤

如果需要回滚到原始配置：

```bash
# 1. 停止所有服务
docker-compose down

# 2. 恢复配置文件
cp docker-compose.yml.backup docker-compose.yml
cp .env.backup .env

# 3. 重启服务
docker-compose up -d

# 4. 验证
docker-compose ps
```

---

## 维护操作

### 日常维护

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f --tail 100

# 重启特定服务
docker-compose restart agent-service

# 更新服务
docker-compose up -d --build agent-service
```

### 数据备份

```bash
# MySQL 备份
docker exec AIWorkbench-mysql sh -c 'exec mysqldump --all-databases -uroot -p${MYSQL_ROOT_PASSWORD}' > backup_$(date +%Y%m%d).sql

# Elasticsearch 备份
curl -X PUT "localhost:9200/_snapshot/backup" -H 'Content-Type: application/json' -d'{"type":"fs","settings":{"location":"/backup"}}'
curl -X PUT "localhost:9200/_snapshot/backup/snapshot_$(date +%Y%m%d)?wait_for_completion=true"
```

### 清理资源

```bash
# 清理停止的容器
docker container prune -f

# 清理未使用的镜像
docker image prune -a -f

# 清理未使用的卷
docker volume prune -f

# 清理未使用的网络
docker network prune -f
```

---

## 性能优化

### Elasticsearch

```yaml
# 调整内存设置
environment:
  - "ES_JAVA_OPTS=-Xms1g -Xmx1g"  # 设置为可用内存的 50%
```

### Agent Service

```bash
# 调整并发参数
MAX_STEPS=10           # 减少推理步数
TIMEOUT=300            # 设置超时
TEMPERATURE=0.7        # 调整温度参数
MAX_TOKENS=4096        # 限制 token 数量
```

### Backend

```bash
# 增加工作进程数
SERVER_WORKERS=4       # 根据 CPU 核心数调整
```

---

## 安全建议

### 生产环境必做

1. **修改默认密码**
   - MYSQL_ROOT_PASSWORD
   - MYSQL_PASSWORD
   - JWT_SECRET_KEY

2. **限制端口暴露**
   - 只开放必要的端口（80, 443）
   - 内网服务不要暴露到公网

3. **启用 Elasticsearch 认证**
   - 设置 xpack.security.enabled=true
   - 配置用户名和密码

4. **配置 TLS/SSL**
   - 启用 HTTPS
   - 配置有效的 SSL 证书

5. **定期更新**
   - 更新 Docker 镜像
   - 更新依赖包
   - 安装安全补丁

---

## 监控和日志

### 日志位置

- **Backend**: `backend_logs` volume
- **Nginx**: `nginx_logs` volume
- **Agent Service**: `./agent-service/logs/`
- **Docker 日志**: `/var/lib/docker/containers/`

### 监控命令

```bash
# 实时日志
docker-compose logs -f

# 特定服务日志
docker-compose logs -f agent-service

# 查看最近 100 行
docker-compose logs --tail 100

# 查看容器资源使用
docker stats

# 查看磁盘使用
docker system df
```

---

## 扩展和定制

### 添加新服务

编辑 `docker-compose.yml`：

```yaml
services:
  new-service:
    image: your-image
    networks:
      - AIWorkbench-network
    depends_on:
      - service-name
```

### 添加新卷

```yaml
volumes:
  new_volume:
    driver: local
```

### 配置负载均衡

```yaml
services:
  agent-service:
    deploy:
      replicas: 3
```

---

## 文档参考

- **集成详解**: AGENT_SERVICE_INTEGRATION.md
- **端口参考**: PORT_REFERENCE.md
- **快速总结**: INTEGRATION_SUMMARY.md
- **Agent Service**: ./agent-service/README.md

---

## 支持和反馈

如遇到问题：

1. 查看服务日志: `docker-compose logs`
2. 运行健康检查: `./verify-services.sh`
3. 查看相关文档
4. 检查系统资源: `docker stats`

---

## 更新日志

- **2025-01-26**: 初始版本，完成 agent-service 集成
