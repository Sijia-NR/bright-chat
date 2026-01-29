#!/bin/bash
# 本地启动脚本 - 启动 Front、Backend、Agent-Service
# Redis、MySQL、ChromaDB 继续使用容器服务

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/data1/allresearchProject/Bright-Chat"
BACKEND_DIR="$PROJECT_ROOT/backend-python"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# 日志目录
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# 日志文件(带时间戳)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKEND_LOG_FILE="$LOG_DIR/backend_${TIMESTAMP}.log"
FRONTEND_LOG_FILE="$LOG_DIR/frontend_${TIMESTAMP}.log"

# 同时创建不带时间戳的符号链接,方便查看
ln -sf "$BACKEND_LOG_FILE" "$LOG_DIR/backend.log"
ln -sf "$FRONTEND_LOG_FILE" "$LOG_DIR/frontend.log"

# PID 文件
BACKEND_PID_FILE="$LOG_DIR/backend.pid"
FRONTEND_PID_FILE="$LOG_DIR/frontend.pid"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Bright-Chat 本地启动脚本${NC}"
echo -e "${BLUE}========================================${NC}"

# ============================================
# 动态读取端口配置
# ============================================
echo -e "\n${YELLOW}[读取配置] 从配置文件读取端口信息...${NC}"

# 读取后端端口配置
BACKEND_PORT_CONFIG_FILE="$BACKEND_DIR/app/core/config.py"
if [ -f "$BACKEND_PORT_CONFIG_FILE" ]; then
    # 从配置文件中提取 SERVER_PORT
    BACKEND_PORT=$(grep -oP 'SERVER_PORT:\s*int\s*=\s*\K\d+' "$BACKEND_PORT_CONFIG_FILE" | head -1)
    if [ -z "$BACKEND_PORT" ]; then
        BACKEND_PORT=8080  # 默认值
    fi
else
    BACKEND_PORT=8080  # 默认值
fi

# 读取前端端口配置
FRONTEND_ENV_FILE="$FRONTEND_DIR/vite.config.ts"
if [ -f "$FRONTEND_ENV_FILE" ]; then
    # 从 vite.config.ts 中提取端口号（格式：port: 3000）
    FRONTEND_PORT=$(grep -oP 'port:\s*\K\d+' "$FRONTEND_ENV_FILE" | head -1)
    if [ -z "$FRONTEND_PORT" ]; then
        FRONTEND_PORT=3000  # 默认值
    fi
else
    FRONTEND_PORT=3000  # 默认值
fi

echo -e "${GREEN}✓ 后端端口: $BACKEND_PORT${NC}"
echo -e "${GREEN}✓ 前端端口: $FRONTEND_PORT${NC}"

# ============================================
# 进程管理函数
# ============================================

# 根据端口查找进程
find_process_by_port() {
    local port=$1
    local pids=$(lsof -t -i :$port 2>/dev/null)
    echo "$pids"
}

# 强制终止函数
force_kill() {
    local pid=$1
    local name=$2
    local max_wait=3

    if [ -z "$pid" ]; then
        return 1
    fi

    # 检查进程是否存在
    if ! ps -p "$pid" > /dev/null 2>&1; then
        return 0
    fi

    echo -e "${YELLOW}  正在停止 $name (PID: $pid)...${NC}"

    # 先尝试优雅终止 (SIGTERM)
    kill "$pid" 2>/dev/null || true

    # 等待进程终止
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt $max_wait ]; do
        sleep 1
        count=$((count + 1))
    done

    # 如果进程仍在运行，强制终止 (SIGKILL)
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${YELLOW}  强制终止 $name...${NC}"
        kill -9 "$pid" 2>/dev/null || true
        sleep 1
    fi

    # 最终检查
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${RED}✗ $name 停止失败 (PID: $pid)${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $name 已停止${NC}"
        return 0
    fi
}

# 根据端口停止服务
kill_service_by_port() {
    local port=$1
    local service_name=$2

    echo -e "\n${YELLOW}检查端口 $port ($service_name)...${NC}"

    # 查找占用该端口的进程
    local pids=$(find_process_by_port "$port")

    if [ -z "$pids" ]; then
        echo -e "${GREEN}✓ 端口 $port ($service_name) 未被占用${NC}"
        return 0
    fi

    # 显示找到的进程
    for pid in $pids; do
        local cmd=$(ps -p "$pid" -o comm= 2>/dev/null | tr -d ' ')
        echo -e "${YELLOW}  发现进程: $cmd (PID: $pid)${NC}"

        # 如果是我们要管理的前端/后端服务，则停止
        if [[ "$cmd" == *"uvicorn"* ]] || [[ "$cmd" == *"vite"* ]] || [[ "$cmd" == *"npm"* ]] || [[ "$cmd" == *"node"* ]]; then
            force_kill "$pid" "$service_name (端口 $port)"
        else
            echo -e "${YELLOW}  💡 这是其他服务（如 frpc），跳过${NC}"
        fi
    done
}

# ============================================
# 检查容器服务状态
# ============================================
echo -e "\n${YELLOW}[1/5] 检查容器服务状态...${NC}"
check_container() {
    local container=$1
    if docker ps --format '{{.Names}}' | grep -q "^AIWorkbench-$container$"; then
        echo -e "${GREEN}✓ $container 容器运行中${NC}"
        return 0
    else
        echo -e "${RED}✗ $container 容器未运行${NC}"
        return 1
    fi
}

check_container "mysql" || exit 1
check_container "redis" || exit 1
check_container "chromadb" || exit 1

# ============================================
# 停止已有服务（根据端口）
# ============================================
echo -e "\n${YELLOW}[2/5] 停止已有服务（根据配置的端口）...${NC}"

# 先根据PID文件停止（如果存在）
if [ -f "$BACKEND_PID_FILE" ]; then
    backend_pid=$(cat "$BACKEND_PID_FILE")
    if [ -n "$backend_pid" ] && ps -p "$backend_pid" > /dev/null 2>&1; then
        force_kill "$backend_pid" "Backend (PID文件)"
    fi
    rm -f "$BACKEND_PID_FILE"
fi

if [ -f "$FRONTEND_PID_FILE" ]; then
    frontend_pid=$(cat "$FRONTEND_PID_FILE")
    if [ -n "$frontend_pid" ] && ps -p "$frontend_pid" > /dev/null 2>&1; then
        force_kill "$frontend_pid" "Frontend (PID文件)"
    fi
    rm -f "$FRONTEND_PID_FILE"
fi

# 再根据端口停止（防止没有PID文件的情况）
kill_service_by_port "$BACKEND_PORT" "Backend"
kill_service_by_port "$FRONTEND_PORT" "Frontend"

sleep 2

# ============================================
# 启动后端服务
# ============================================
echo -e "\n${YELLOW}[3/5] 启动 Backend 服务 (端口 $BACKEND_PORT)...${NC}"
echo -e "${BLUE}日志文件: $BACKEND_LOG_FILE${NC}"

cd "$BACKEND_DIR"
if [ ! -d "venv_py312" ]; then
    echo -e "${RED}Backend 虚拟环境不存在，正在创建...${NC}"
    python3 -m venv venv_py312
    source venv_py312/bin/activate
    pip install -q -r requirements.txt
fi

# 启动 Backend,记录详细日志
# 使用 minimal_api.py 以获得完整功能（包含 admin/models 和 knowledge 路由）
# 设置环境变量以正确连接 ChromaDB 容器和本地模型
export CHROMADB_HOST=localhost
export CHROMADB_PORT=8002
export BGE_MODEL_PATH=/data1/allresearchProject/Bright-Chat/models/Xorbits/bge-large-zh-v1.5

nohup venv_py312/bin/uvicorn minimal_api:app \
    --host 0.0.0.0 \
    --port "$BACKEND_PORT" \
    --workers 1 \
    --log-level info \
    --access-log \
    > "$BACKEND_LOG_FILE" 2>&1 &

BACKEND_PID=$!
echo $BACKEND_PID > "$BACKEND_PID_FILE"
echo -e "${GREEN}✓ Backend 服务已启动 (PID: $BACKEND_PID, 端口: $BACKEND_PORT)${NC}"

# 等待后端启动
echo -e "${YELLOW}等待 Backend 服务启动...${NC}"
sleep 5

# 检查后端健康状态
for i in {1..30}; do
    if curl -s "http://localhost:$BACKEND_PORT/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend 服务已就绪 (端口: $BACKEND_PORT)${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Backend 服务启动失败${NC}"
        echo -e "${RED}查看日志: tail -f $BACKEND_LOG_FILE${NC}"
        exit 1
    fi
    sleep 1
done

# ============================================
# 启动前端服务
# ============================================
echo -e "\n${YELLOW}[4/5] 启动 Frontend 服务 (端口 $FRONTEND_PORT)...${NC}"
echo -e "${BLUE}日志文件: $FRONTEND_LOG_FILE${NC}"

cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Frontend 依赖未安装，正在安装...${NC}"
    npm install
fi

# 启动 Frontend，记录详细日志
nohup npm run dev > "$FRONTEND_LOG_FILE" 2>&1 &

FRONTEND_PID=$!
echo $FRONTEND_PID > "$FRONTEND_PID_FILE"
echo -e "${GREEN}✓ Frontend 服务已启动 (PID: $FRONTEND_PID, 端口: $FRONTEND_PORT)${NC}"

# 等待前端启动
echo -e "${YELLOW}等待 Frontend 服务启动...${NC}"
sleep 5

# 检查前端服务
for i in {1..30}; do
    if curl -s "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend 服务已就绪 (端口: $FRONTEND_PORT)${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Frontend 服务启动失败${NC}"
        echo -e "${RED}查看日志: tail -f $FRONTEND_LOG_FILE${NC}"
        exit 1
    fi
    sleep 1
done

# ============================================
# 显示服务信息
# ============================================
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}所有服务启动成功！${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "\n${YELLOW}🎯 服务地址：${NC}"
echo -e "  Frontend:     ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
echo -e "  Backend API:  ${GREEN}http://localhost:$BACKEND_PORT${NC}"
echo -e "  API Docs:     ${GREEN}http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "\n${YELLOW}📝 配置端口：${NC}"
echo -e "  Frontend 端口: $FRONTEND_PORT (从 vite.config.ts 读取)"
echo -e "  Backend 端口: $BACKEND_PORT (从 app/core/config.py 读取)"
echo -e "\n${YELLOW}📋 日志查看：${NC}"
echo -e "  Backend:  tail -f $LOG_DIR/backend.log"
echo -e "  Frontend: tail -f $LOG_DIR/frontend.log"
echo -e "\n${YELLOW}🛑 停止服务：${NC}"
echo -e "  ./stop-local.sh"
echo -e ""

# ============================================
# 创建停止脚本
# ============================================
cat > "$PROJECT_ROOT/stop-local.sh" << 'STOPSCRIPT'
#!/bin/bash
# 停止本地服务脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

LOG_DIR="/data1/allresearchProject/Bright-Chat/logs"

echo -e "${YELLOW}停止本地服务...${NC}"

# 读取配置的端口
BACKEND_DIR="/data1/allresearchProject/Bright-Chat/backend-python"
FRONTEND_DIR="/data1/allresearchProject/Bright-Chat/frontend"

BACKEND_PORT=$(grep -oP 'SERVER_PORT:\s*int\s*=\s*\K\d+' "$BACKEND_DIR/app/core/config.py" 2>/dev/null | head -1)
BACKEND_PORT=${BACKEND_PORT:-8080}

FRONTEND_PORT=$(grep -oP 'port:\s*\K\d+' "$FRONTEND_DIR/vite.config.ts" 2>/dev/null | head -1)
FRONTEND_PORT=${FRONTEND_PORT:-3000}

# 根据 PID 文件停止
if [ -f "$LOG_DIR/frontend.pid" ]; then
    pid=$(cat "$LOG_DIR/frontend.pid")
    if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${YELLOW}停止 Frontend (PID: $pid, 端口: $FRONTEND_PORT)...${NC}"
        kill "$pid" 2>/dev/null || true
        sleep 2
        # 如果还在运行，强制杀死
        if ps -p "$pid" > /dev/null 2>&1; then
            kill -9 "$pid" 2>/dev/null || true
        fi
        echo -e "${GREEN}✓ Frontend 已停止${NC}"
    fi
    rm -f "$LOG_DIR/frontend.pid"
fi

if [ -f "$LOG_DIR/backend.pid" ]; then
    pid=$(cat "$LOG_DIR/backend.pid")
    if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${YELLOW}停止 Backend (PID: $pid, 端口: $BACKEND_PORT)...${NC}"
        kill "$pid" 2>/dev/null || true
        sleep 2
        # 如果还在运行，强制杀死
        if ps -p "$pid" > /dev/null 2>&1; then
            kill -9 "$pid" 2>/dev/null || true
        fi
        echo -e "${GREEN}✓ Backend 已停止${NC}"
    fi
    rm -f "$LOG_DIR/backend.pid"
fi

echo -e "${GREEN}所有服务已停止${NC}"
STOPSCRIPT

chmod +x "$PROJECT_ROOT/stop-local.sh"
echo -e "${GREEN}✓ 停止脚本已更新: $PROJECT_ROOT/stop-local.sh${NC}"
