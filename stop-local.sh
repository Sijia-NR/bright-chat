#!/bin/bash
# 停止本地服务

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="/data1/allresearchProject/Bright-Chat"
LOG_DIR="$PROJECT_ROOT/logs"
BACKEND_DIR="$PROJECT_ROOT/backend-python"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo -e "${YELLOW}停止本地服务...${NC}"

# 读取端口
BACKEND_PORT=$(grep -oP 'SERVER_PORT:\s*int\s*=\s*\K\d+' "$BACKEND_DIR/app/core/config.py" 2>/dev/null | head -1)
BACKEND_PORT=${BACKEND_PORT:-18080}

FRONTEND_PORT=$(grep -oP 'port:\s*\K\d+' "$FRONTEND_DIR/vite.config.ts" 2>/dev/null | head -1)
FRONTEND_PORT=${FRONTEND_PORT:-3000}

# 根据 PID 文件停止
if [ -f "$LOG_DIR/backend.pid" ]; then
    PID=$(cat "$LOG_DIR/backend.pid")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}停止后端 (PID: $PID, 端口: $BACKEND_PORT)${NC}"
        kill "$PID" 2>/dev/null || true
        sleep 2
        kill -9 "$PID" 2>/dev/null || true
    fi
    rm -f "$LOG_DIR/backend.pid"
fi

if [ -f "$LOG_DIR/frontend.pid" ]; then
    PID=$(cat "$LOG_DIR/frontend.pid")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}停止前端 (PID: $PID, 端口: $FRONTEND_PORT)${NC}"
        kill "$PID" 2>/dev/null || true
        sleep 2
        kill -9 "$PID" 2>/dev/null || true
    fi
    rm -f "$LOG_DIR/frontend.pid"
fi

# 额外检查：根据端口停止（防止 PID 文件不存在的情况）
BACKEND_PIDS=$(lsof -t -i :$BACKEND_PORT 2>/dev/null || true)
if [ -n "$BACKEND_PIDS" ]; then
    echo -e "${YELLOW}清理后端端口 $BACKEND_PORT 的进程${NC}"
    kill -9 $BACKEND_PIDS 2>/dev/null || true
fi

FRONTEND_PIDS=$(lsof -t -i :$FRONTEND_PORT 2>/dev/null || true)
if [ -n "$FRONTEND_PIDS" ]; then
    echo -e "${YELLOW}清理前端端口 $FRONTEND_PORT 的进程${NC}"
    kill -9 $FRONTEND_PIDS 2>/dev/null || true
fi

echo -e "${GREEN}✓ 所有服务已停止${NC}"
