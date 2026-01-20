#!/bin/bash

# Bright-Chat 系统启动脚本

echo "🚀 启动 Bright-Chat 系统..."

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ 端口 $port 已被占用，请先停止相关服务"
        exit 1
    fi
}

# 检查端口
check_port 3002
check_port 18063

# 启动 Mock Server
echo "🔧 启动 Mock Server..."
cd mockserver
python start.py &
MOCK_PID=$!
cd ..

# 等待 Mock Server 启动
echo "⏳ 等待 Mock Server 启动..."
sleep 3

# 检查 Mock Server 是否启动成功
if curl -s http://localhost:18063/ > /dev/null; then
    echo "✅ Mock Server 启动成功 (PID: $MOCK_PID)"
else
    echo "❌ Mock Server 启动失败"
    kill $MOCK_PID 2>/dev/null
    exit 1
fi

# 启动前端服务
echo "🌐 启动前端服务..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# 等待前端服务启动
echo "⏳ 等待前端服务启动..."
sleep 5

# 检查前端服务是否启动成功
if curl -s http://localhost:3002/ > /dev/null; then
    echo "✅ 前端服务启动成功 (PID: $FRONTEND_PID)"
else
    echo "❌ 前端服务启动失败"
    kill $MOCK_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎉 系统启动成功！"
echo ""
echo "📍 访问地址:"
echo "  - 前端应用: http://localhost:3002"
echo "  - Mock Server: http://localhost:18063"
echo "  - API文档: http://localhost:18063/docs"
echo ""
echo "📝 使用说明:"
echo "  - 前端使用 'admin/admin123' 登录"
echo "  - Mock Server 使用 'APP_KEY' 作为认证"
echo "  - 按 Ctrl+C 停止所有服务"
echo ""

# 保存进程ID
echo $MOCK_PID > .mock_server_pid
echo $FRONTEND_PID > .frontend_pid

# 等待用户中断
trap "echo '🛑 正在停止服务...'; kill \$(cat .mock_server_pid) 2>/dev/null; kill \$(cat .frontend_pid) 2>/dev/null; rm -f .mock_server_pid .frontend_pid; exit" INT

# 保持脚本运行
wait