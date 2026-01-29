#!/bin/bash
# 启动脚本：同时运行 Backend API 和 Agent Service

set -e

echo "🚀 启动 Bright-Chat Backend + Agent Service"
echo "=========================================="

# 设置环境变量
export PYTHONPATH=/app:/app/agent-service
export PYTHONUNBUFFERED=1

# 日志目录
mkdir -p logs agent-service/logs || true

# 启动 Backend API (后台运行)
echo "📡 启动 Backend API (端口 18080)..."
python minimal_api.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend API PID: $BACKEND_PID"

# 等待 Backend 启动
echo "⏳ 等待 Backend 启动..."
sleep 5

# 检查 Backend 是否启动成功
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend 启动失败"
    cat logs/backend.log
    exit 1
fi

echo "✅ Backend 启动成功"

# 启动 Agent Service (后台运行)
echo "🤖 启动 Agent Service (端口 8000)..."
cd /app/agent-service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/agent-service.log 2>&1 &
AGENT_PID=$!
echo "Agent Service PID: $AGENT_PID"

cd /app

# 等待 Agent Service 启动
echo "⏳ 等待 Agent Service 启动..."
sleep 5

# 检查 Agent Service 是否启动成功
if ! kill -0 $AGENT_PID 2>/dev/null; then
    echo "❌ Agent Service 启动失败"
    cat logs/agent-service.log
    exit 1
fi

echo "✅ Agent Service 启动成功"

# 显示服务信息
echo ""
echo "=========================================="
echo "✅ 所有服务已启动"
echo "=========================================="
echo "Backend API:  http://0.0.0.0:18080 (PID: $BACKEND_PID)"
echo "Agent Service: http://0.0.0.0:8000 (PID: $AGENT_PID)"
echo ""
echo "📝 日志文件:"
echo "  Backend:  logs/backend.log"
echo "  Agent:    logs/agent-service.log"
echo ""
echo "🔍 查看实时日志:"
echo "  tail -f logs/backend.log"
echo "  tail -f logs/agent-service.log"
echo ""

# 等待任意一个进程退出
# 如果其中一个退出，也关闭另一个
wait $BACKEND_PID $AGENT_PID
EXIT_CODE=$?

echo ""
echo "⚠️  服务已停止 (退出码: $EXIT_CODE)"

# 清理：关闭仍在运行的进程
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "🛑 关闭 Backend..."
    kill $BACKEND_PID 2>/dev/null || true
fi

if kill -0 $AGENT_PID 2>/dev/null; then
    echo "🛑 关闭 Agent Service..."
    kill $AGENT_PID 2>/dev/null || true
fi

exit $EXIT_CODE
