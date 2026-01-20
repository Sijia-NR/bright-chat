#!/bin/bash

echo "================================================="
echo "      停止 Bright-Chat 所有服务"
echo "================================================="

# 端口列表
PORTS=(3000 18080 18063)
STOPPED=0

for port in "${PORTS[@]}"; do
    # 查找占用端口的进程 PID
    PID=$(lsof -ti:$port 2>/dev/null)

    if [ -n "$PID" ]; then
        echo "停止端口 $port 上的进程 (PID: $PID)..."
        kill $PID 2>/dev/null
        sleep 1

        # 如果进程仍在运行，强制终止
        if lsof -ti:$port >/dev/null 2>&1; then
            echo "  强制终止端口 $port..."
            kill -9 $PID 2>/dev/null
        fi

        echo "  ✅ 端口 $port 已释放"
        ((STOPPED++))
    else
        echo "⚠️  端口 $port 没有运行的进程"
    fi
done

echo "================================================="
echo "已停止 $STOPPED 个服务"
echo "================================================="
