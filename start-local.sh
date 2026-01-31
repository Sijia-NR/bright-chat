#!/bin/bash
# 本地启动脚本 - 简化版

set -e

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 项目路径
PROJECT_ROOT="/data1/allresearchProject/Bright-Chat"
BACKEND_DIR="$PROJECT_ROOT/backend-python"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
LOG_DIR="$PROJECT_ROOT/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Bright-Chat 本地启动${NC}"
echo -e "${GREEN}========================================${NC}"

# ============================================
# 1. 读取端口配置
# ============================================
echo -e "\n${YELLOW}[1/4] 读取端口配置...${NC}"

# 读取后端端口 (默认 18080)
BACKEND_PORT=$(grep -oP 'SERVER_PORT:\s*int\s*=\s*\K\d+' "$BACKEND_DIR/app/core/config.py" 2>/dev/null | head -1)
BACKEND_PORT=${BACKEND_PORT:-18080}

# 读取前端端口 (默认 3000)
FRONTEND_PORT=$(grep -oP 'port:\s*\K\d+' "$FRONTEND_DIR/vite.config.ts" 2>/dev/null | head -1)
FRONTEND_PORT=${FRONTEND_PORT:-3000}

echo -e "${GREEN}✓ 后端端口: $BACKEND_PORT${NC}"
echo -e "${GREEN}✓ 前端端口: $FRONTEND_PORT${NC}"

# ============================================
# 2. 停止旧进程
# ============================================
echo -e "\n${YELLOW}[2/4] 停止占用端口的旧进程...${NC}"

# 杀掉占用后端端口的进程
BACKEND_PIDS=$(lsof -t -i :$BACKEND_PORT 2>/dev/null || true)
if [ -n "$BACKEND_PIDS" ]; then
    echo -e "${YELLOW}停止后端进程 (端口 $BACKEND_PORT): $BACKEND_PIDS${NC}"
    kill -9 $BACKEND_PIDS 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✓ 后端旧进程已停止${NC}"
else
    echo -e "${GREEN}✓ 后端端口 $BACKEND_PORT 未被占用${NC}"
fi

# 杀掉占用前端端口的进程
FRONTEND_PIDS=$(lsof -t -i :$FRONTEND_PORT 2>/dev/null || true)
if [ -n "$FRONTEND_PIDS" ]; then
    echo -e "${YELLOW}停止前端进程 (端口 $FRONTEND_PORT): $FRONTEND_PIDS${NC}"
    kill -9 $FRONTEND_PIDS 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✓ 前端旧进程已停止${NC}"
else
    echo -e "${GREEN}✓ 前端端口 $FRONTEND_PORT 未被占用${NC}"
fi

# ============================================
# 3. 启动后端
# ============================================
echo -e "\n${YELLOW}[3/4] 启动后端服务...${NC}"

cd "$BACKEND_DIR"

# 检查虚拟环境
if [ ! -d "venv_py312" ]; then
    echo -e "${RED}虚拟环境不存在，请先创建: cd backend-python && python3 -m venv venv_py312${NC}"
    exit 1
fi

# 设置环境变量
export CHROMADB_HOST=localhost
export CHROMADB_PORT=8002
export BGE_MODEL_PATH=/data1/allresearchProject/Bright-Chat/models/Xorbits/bge-large-zh-v1.5

# 启动后端
nohup venv_py312/bin/uvicorn minimal_api:app \
    --host 0.0.0.0 \
    --port $BACKEND_PORT \
    --workers 1 \
    > "$LOG_DIR/backend.log" 2>&1 &

BACKEND_PID=$!
echo $BACKEND_PID > "$LOG_DIR/backend.pid"
echo -e "${GREEN}✓ 后端已启动 (PID: $BACKEND_PID, 端口: $BACKEND_PORT)${NC}"

# 等待后端就绪
echo -e "${YELLOW}等待后端服务就绪...${NC}"
for i in {1..20}; do
    if curl -s "http://localhost:$BACKEND_PORT/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端服务已就绪${NC}"
        break
    fi
    if [ $i -eq 20 ]; then
        echo -e "${RED}✗ 后端启动超时，查看日志: tail -f $LOG_DIR/backend.log${NC}"
        exit 1
    fi
    sleep 1
done

# ============================================
# 4. 启动前端
# ============================================
echo -e "\n${YELLOW}[4/4] 启动前端服务...${NC}"

cd "$FRONTEND_DIR"

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}安装前端依赖...${NC}"
    npm install
fi

# 启动前端
nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &

FRONTEND_PID=$!
echo $FRONTEND_PID > "$LOG_DIR/frontend.pid"
echo -e "${GREEN}✓ 前端已启动 (PID: $FRONTEND_PID, 端口: $FRONTEND_PORT)${NC}"

# 等待前端就绪
echo -e "${YELLOW}等待前端服务就绪...${NC}"
for i in {1..20}; do
    if curl -s "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ 前端服务已就绪${NC}"
        break
    fi
    if [ $i -eq 20 ]; then
        echo -e "${RED}✗ 前端启动超时，查看日志: tail -f $LOG_DIR/frontend.log${NC}"
        exit 1
    fi
    sleep 1
done

# ============================================
# 完成
# ============================================
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ 所有服务启动成功！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${YELLOW}服务地址：${NC}"
echo -e "  前端:  http://localhost:$FRONTEND_PORT"
echo -e "  后端:  http://localhost:$BACKEND_PORT"
echo -e "  API文档: http://localhost:$BACKEND_PORT/docs"
echo -e "\n${YELLOW}日志查看：${NC}"
echo -e "  后端: tail -f $LOG_DIR/backend.log"
echo -e "  前端: tail -f $LOG_DIR/frontend.log"
echo -e "\n${YELLOW}停止服务：${NC}"
echo -e "  kill \$(cat $LOG_DIR/backend.pid)"
echo -e "  kill \$(cat $LOG_DIR/frontend.pid)"
echo ""
