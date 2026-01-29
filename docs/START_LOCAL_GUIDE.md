# start-local.sh 使用说明

## 📋 脚本功能

`start-local.sh` 是本地开发环境的启动脚本，用于启动前端和后端服务。

---

## 🎯 主要特性

### 1. 动态端口配置 ✅ NEW!

**不再硬编码端口号**，而是从配置文件动态读取：

#### 后端端口
- **配置文件**: `backend-python/app/core/config.py`
- **配置项**: `SERVER_PORT: int = 8080`

#### 前端端口
- **配置文件**: `frontend/vite.config.ts`
- **配置项**: `server.port: 3000`

**修改端口的方法**：
1. 编辑相应的配置文件
2. 修改端口号
3. 运行 `./start-local.sh` - 自动读取新端口

---

### 2. 智能进程管理 ✅ NEW!

#### 两阶段停止机制

**阶段 1**: 根据 PID 文件停止
```bash
# 读取 logs/backend.pid 和 logs/frontend.pid
# 停止记录的进程
```

**阶段 2**: 根据端口查找并停止
```bash
# 查找占用端口的进程
# 智能识别是否是我们的服务
# 停止 uvicorn/vite/npm/node 进程
# 保留其他服务（如 frpc）
```

#### 进程识别逻辑

脚本会识别以下进程：
- ✅ **uvicorn** - Python 后端服务
- ✅ **vite** - 前端开发服务器
- ✅ **npm** - Node 包管理器
- ✅ **node** - Node.js 运行时

脚本会跳过以下进程：
- ⏭️ **frpc** - 内网穿透工具
- ⏭️ **其他系统服务**

---

### 3. 优雅停止机制

```bash
1. 尝试 SIGTERM (优雅终止)
   ↓
2. 等待最多 3 秒
   ↓
3. 如果仍在运行，使用 SIGKILL (强制终止)
```

---

## 🚀 使用方法

### 基本使用

```bash
# 启动所有服务
./start-local.sh

# 停止所有服务
./stop-local.sh
```

---

### 修改端口配置

#### 场景 1: 修改后端端口

1. 编辑配置文件：
```bash
vim backend-python/app/core/config.py
```

2. 修改端口：
```python
SERVER_PORT: int = 8888  # 从 8080 改为 8888
```

3. 保存并运行脚本：
```bash
./start-local.sh
```

**输出**：
```
[读取配置] 从配置文件读取端口信息...
✓ 后端端口: 8888
✓ 前端端口: 3000
```

---

#### 场景 2: 修改前端端口

1. 编辑配置文件：
```bash
vim frontend/vite.config.ts
```

2. 修改端口：
```typescript
export default defineConfig({
  server: {
    port: 8888,  // 从 3000 改为 8888
  }
  // ...
});
```

3. 保存并运行脚本：
```bash
./start-local.sh
```

**输出**：
```
[读取配置] 从配置文件读取端口信息...
✓ 后端端口: 8080
✓ 前端端口: 8888
```

---

#### 场景 3: 同时修改两个端口

按照上述步骤分别修改两个配置文件即可。

---

## 📊 执行流程

```
1. [读取配置] 显示读取的端口信息
   ├─ 后端端口: 8080
   └─ 前端端口: 3000

2. [1/5] 检查容器服务状态
   ├─ MySQL 容器
   ├─ Redis 容器
   └─ ChromaDB 容器

3. [2/5] 停止已有服务（根据配置的端口）
   ├─ 读取 PID 文件
   ├─ 根据 PID 文件停止进程
   ├─ 根据端口查找进程
   ├─ 智能识别并停止前端/后端进程
   └─ 跳过其他服务（如 frpc）

4. [3/5] 启动 Backend 服务 (配置的端口)
   ├─ 创建虚拟环境（如果不存在）
   ├─ 启动 uvicorn
   ├─ 记录 PID
   └─ 等待健康检查通过

5. [4/5] 启动 Frontend 服务 (配置的端口)
   ├─ 安装依赖（如果需要）
   ├─ 启动 npm run dev
   ├─ 记录 PID
   └─ 等待服务可用

6. ✅ 显示服务地址和日志查看方法
```

---

## 🔍 故障排查

### 问题 1: 端口被占用

**现象**：
```
⚠ 端口 8080 (Backend) 被占用
  发现进程: uvicorn (PID: 12345)
  正在停止 Backend (端口 8080)...
```

**解决方案**：
- 脚本会自动停止占用端口的进程
- 如果无法停止，请手动停止：`kill 12345`

---

### 问题 2: 其他服务占用端口

**现象**：
```
⚠ 端口 8080 (Backend) 被其他进程占用: frpc (PID: 12345)
💡 提示: 如果这是 frpc 或其他服务，请忽略此警告
```

**解决方案**：
- 这是正常的，脚本会跳过 frpc
- 如果是其他服务，可以继续运行

---

### 问题 3: 服务启动失败

**现象**：
```
✗ Backend 服务启动失败
查看日志: tail -f logs/backend.log
```

**解决方案**：
1. 查看日志：`tail -f logs/backend.log`
2. 检查端口是否正确：`lsof -i :8080`
3. 检查容器服务：`docker ps`

---

## 📋 日志文件

### 后端日志
- **当前日志**: `logs/backend.log` (符号链接)
- **完整日志**: `logs/backend_20260129_183045.log`
- **查看方法**: `tail -f logs/backend.log`

### 前端日志
- **当前日志**: `logs/frontend.log` (符号链接)
- **完整日志**: `logs/frontend_20260129_183045.log`
- **查看方法**: `tail -f logs/frontend.log`

---

## 🔧 配置示例

### 示例 1: 默认配置

**后端** (`app/core/config.py`):
```python
SERVER_PORT: int = 8080
```

**前端** (`vite.config.ts`):
```typescript
export default defineConfig({
  server: {
    port: 3000
  }
});
```

**运行结果**:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8080`

---

### 示例 2: 自定义端口

**后端** (`app/core/config.py`):
```python
SERVER_PORT: int = 8888
```

**前端** (`vite.config.ts`):
```typescript
export default defineConfig({
  server: {
    port: 9999
  }
});
```

**运行结果**:
- Frontend: `http://localhost:9999`
- Backend: `http://localhost:8888`

---

## ⚠️ 注意事项

1. **端口冲突**:
   - 确保配置的端口没有被其他系统服务占用
   - 如果冲突，脚本会自动停止我们的服务，但不会停止其他服务（如 frpc）

2. **配置文件优先级**:
   - 修改配置文件后，无需修改脚本
   - 脚本会在每次运行时读取最新配置

3. **权限**:
   - 脚本需要执行权限：`chmod +x start-local.sh`
   - 已包含可执行权限，可直接运行

4. **容器依赖**:
   - 脚本会检查 MySQL、Redis、ChromaDB 容器
   - 确保这些容器正在运行

---

## 🎉 总结

✅ **动态配置** - 自动读取配置文件中的端口
✅ **智能管理** - 识别并只停止我们自己的服务
✅ **优雅停止** - SIGTERM + SIGKILL 两阶段机制
✅ **详细日志** - 清晰的执行过程和错误信息

现在修改端口配置后，无需修改脚本，直接运行即可！
