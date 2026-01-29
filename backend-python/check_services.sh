#!/bin/bash

echo "==================================="
echo "  Bright-Chat 服务状态检查"
echo "==================================="
echo ""

# 检查函数
check_service() {
    local name=$1
    local port=$2
    local url=$3
    
    if curl -s "$url" >/dev/null 2>&1; then
        echo "✅ $name"
        echo "   端口: $port"
        echo "   地址: http://localhost:$port"
        echo ""
        return 0
    else
        echo "❌ $name"
        echo "   端口: $port"
        echo "   状态: 未响应"
        echo ""
        return 1
    fi
}

# 检查容器服务
echo "【容器服务】"
docker ps --format "table {{.Names}}\t{{.Status}}" --filter "name=AIWorkbench" 2>/dev/null | grep -E "mysql|redis|chromadb|NAME"
echo ""

# 检查本地服务
echo "【本地服务】"
check_service "Frontend" "9006" "http://localhost:9006"
check_service "Backend API" "18080" "http://localhost:18080/health"
check_service "Agent Service" "8000" "http://localhost:8000/health"

# 显示进程信息
echo "【进程信息】"
echo "Frontend:"
lsof -i :9006 2>/dev/null | grep LISTEN | awk '{print "  PID " $2 " 正在监听端口 9006"}' || echo "  未运行"
echo ""
echo "Backend:"
lsof -i :18080 2>/dev/null | grep LISTEN | awk '{print "  PID " $2 " 正在监听端口 18080"}' || echo "  未运行"
echo ""
echo "Agent:"
lsof -i :8000 2>/dev/null | grep LISTEN | awk '{print "  PID " $2 " 正在监听端口 8000"}' || echo "  未运行"

echo ""
echo "==================================="
echo "服务状态检查完成"
echo "==================================="
