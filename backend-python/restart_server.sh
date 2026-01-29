#!/bin/bash
# 重启 Bright-Chat 后端服务器

echo "=========================================="
echo "重启 Bright-Chat 后端服务器"
echo "=========================================="

# 停止当前运行的服务器
echo ""
echo "[1/3] 停止当前服务器..."
pkill -f "python.*minimal_api.py" || true
sleep 2

# 确认进程已停止
if ps aux | grep -q "[p]ython.*minimal_api.py"; then
    echo "  强制停止服务器..."
    pkill -9 -f "python.*minimal_api.py" || true
    sleep 1
fi

echo "  ✓ 服务器已停止"

# 启动新服务器
echo ""
echo "[2/3] 启动新服务器..."
cd /data1/allresearchProject/Bright-Chat/backend-python
nohup python3 minimal_api.py > server.log 2>&1 &
sleep 3

# 检查服务器是否启动成功
echo ""
echo "[3/3] 验证服务器状态..."
if ps aux | grep -q "[p]ython.*minimal_api.py"; then
    echo "  ✓ 服务器启动成功"

    # 等待服务器完全初始化
    echo "  等待服务器初始化..."
    sleep 3

    # 健康检查
    response=$(curl -s http://localhost:18080/health)
    if [ $? -eq 0 ]; then
        echo "  ✓ 健康检查通过"
        echo "  响应: $response"
    else
        echo "  ✗ 健康检查失败"
    fi

    echo ""
    echo "=========================================="
    echo "服务器重启完成"
    echo "=========================================="
    echo ""
    echo "日志文件: /data1/allresearchProject/Bright-Chat/backend-python/server.log"
    echo "查看日志: tail -f server.log"
    echo ""
else
    echo "  ✗ 服务器启动失败"
    echo "  请检查日志: tail -f server.log"
fi
