# Bright-Chat API Backend

基于 Python FastAPI 构建的 Bright-Chat 后端服务，提供完整的聊天应用 API 功能。

## 功能特性

- 🔐 用户认证与授权 (JWT)
- 👥 用户管理（管理员功能）
- 💬 会话管理
- 🤖 IAS API 代理（支持流式/非流式）
- 📡 OpenAPI/Swagger 文档
- 🗄️ 数据库管理（MariaDB）
- 📊 Prometheus 监控指标
- 🐳 Docker 支持
- 🔧 配置管理

## 技术栈

- **框架**: FastAPI 0.104.1
- **数据库**: MariaDB 10.11 / PostgreSQL
- **缓存**: Redis
- **认证**: JWT + bcrypt
- **文档**: OpenAPI/Swagger
- **监控**: Prometheus
- **部署**: Docker + Docker Compose

## 快速开始

### 环境要求

- Python 3.8+
- MariaDB 10.11+
- Redis 6.0+

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd backend-python

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\\Scripts\\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 或使用开发依赖
pip install -r requirements.txt[dev]
```

### 配置设置

1. 复制环境配置文件：
```bash
cp config/.env.example config/.env
```

2. 编辑 `config/.env` 文件，配置数据库连接等信息：
```env
# 数据库配置
DB_HOST=47.116.218.206
DB_PORT=13306
DB_USERNAME=root
DB_PASSWORD=123456
DB_DATABASE=bright_chat

# JWT 密钥
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
```

### 数据库初始化

```bash
# 初始化数据库
python scripts/init_db.py

# 重置数据库（会删除所有数据）
python scripts/init_db.py --reset
```

### 运行服务

```bash
# 开发模式（热重载）
python run.py

# 或使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### 使用 Docker

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down
```

## API 文档

启动服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## API 端点

### 认证接口
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/logout` - 用户退出

### 用户管理接口（仅管理员）
- `GET /api/v1/admin/users` - 获取用户列表
- `POST /api/v1/admin/users` - 创建用户
- `PUT /api/v1/admin/users/{user_id}` - 更新用户
- `DELETE /api/v1/admin/users/{user_id}` - 删除用户

### 会话管理接口
- `GET /api/v1/sessions` - 获取会话列表
- `POST /api/v1/sessions` - 创建会话
- `GET /api/v1/sessions/{session_id}/messages` - 获取会话消息
- `POST /api/v1/sessions/{session_id}/messages` - 保存消息
- `DELETE /api/v1/sessions/{session_id}` - 删除会话

### IAS API 代理
- `POST /api/v1/lmp-cloud-ias-server/api/llm/chat/completions/V2` - 聊天代理（支持流式）

### 健康检查
- `GET /health` - 健康检查
- `GET /` - API 信息

## 默认账户

初始化后会创建以下默认账户：

- **管理员**: `admin` / `admin123`

## 数据库模型

### User（用户）
```python
class User(Base):
    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

### Session（会话）
```python
class Session(Base):
    id = Column(String(36), primary_key=True)
    title = Column(String(200), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"))
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())
```

### Message（消息）
```python
class Message(Base):
    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id"))
    role = Column(String(20), nullable=False)  # user/assistant/system
    content = Column(String(5000), nullable=False)
    timestamp = Column(DateTime, default=func.now())
```

## 配置说明

主要配置项位于 `config/settings.yaml`：

```yaml
# 应用设置
app:
  name: "Bright-Chat API"
  debug: false

# 服务器设置
server:
  host: "0.0.0.0"
  port: 8080

# 数据库设置
database:
  driver: "mysql"
  host: "localhost"
  port: 13306
  username: "root"
  password: "password"
  database: "bright_chat"

# JWT 设置
auth:
  jwt_secret_key: "your-secret-key"
  jwt_access_token_expire_minutes: 1440

# IAS 设置
ias:
  base_url: "http://localhost:8080/api/v1"
  timeout: 30
  max_retries: 3
```

## 开发指南

### 代码规范

项目使用以下工具维护代码质量：

- **Black**: 代码格式化
- **isort**: 导入排序
- **flake8**: 代码检查
- **mypy**: 类型检查

运行代码质量检查：

```bash
# 格式化代码
black app/
isort app/

# 代码检查
flake8 app/
mypy app/
```

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov

# 运行测试
pytest

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

### 数据库迁移

使用 Alembic 进行数据库版本管理：

```bash
# 创建迁移文件
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 部署指南

### 生产环境部署

1. **配置生产环境变量**：
```bash
export APP_DEBUG=false
export JWT_SECRET_KEY=your-production-secret-key
```

2. **使用 Gunicorn 部署**：
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

3. **使用 Nginx 反向代理**：
```nginx
server {
    listen 80;
    server_name api.bright-chat.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Docker 部署

使用提供的 `docker-compose.yml`：

```bash
# 生产环境构建
docker-compose -f docker-compose.yml up -d

# 开发环境构建
docker-compose -f docker-compose.dev.yml up -d
```

## 监控与日志

### Prometheus 指标

服务已集成 Prometheus 指标收集，默认访问地址：`/metrics`

### 日志配置

日志配置在 `config/settings.yaml` 中，支持：

- 不同日志级别
- 文件输出
- 日志轮转
- 结构化日志

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库配置
   - 确认数据库服务正在运行

2. **JWT 认证失败**
   - 检查 JWT_SECRET_KEY 配置
   - 确认 token 未过期

3. **IAS API 调用失败**
   - 检查 IAS_BASE_URL 配置
   - 确认网络连通性

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# Docker 环境日志
docker-compose logs -f api
```

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目主页: https://github.com/bright-chat/api
- 问题反馈: https://github.com/bright-chat/api/issues
- 邮箱: api@bright-chat.com