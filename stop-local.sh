#!/bin/bash
LOG_DIR="/data1/allresearchProject/Bright-Chat/logs"

echo "停止本地服务..."

if [ -f "$LOG_DIR/frontend.pid" ]; then
    kill $(cat "$LOG_DIR/frontend.pid") 2>/dev/null && echo "✓ 停止 Frontend"
    rm -f "$LOG_DIR/frontend.pid"
fi

if [ -f "$LOG_DIR/backend.pid" ]; then
    kill $(cat "$LOG_DIR/backend.pid") 2>/dev/null && echo "✓ 停止 Backend"
    rm -f "$LOG_DIR/backend.pid"
fi

echo "所有服务已停止"
