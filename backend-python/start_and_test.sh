#!/bin/bash
# Bright-Chat 后端启动脚本（文档上传测试版）

set -e

echo "=== 🚀 启动 Bright-Chat 后端服务 ==="
echo ""

# 进入后端目录
cd /data1/allresearchProject/Bright-Chat/backend-python

# 设置环境变量
export CHROMADB_HOST=localhost
export CHROMADB_PORT=8002
export RAG_USE_CHROMADB_EMBEDDING=false
export BGE_MODEL_PATH=/data1/allresearchProject/Bright-Chat/models/Xorbits/bge-large-zh-v1.5

echo "📋 环境配置:"
echo "  CHROMADB_HOST=$CHROMADB_HOST"
echo "  CHROMADB_PORT=$CHROMADB_PORT"
echo "  RAG_USE_CHROMADB_EMBEDDING=$RAG_USE_CHROMADB_EMBEDDING"
echo "  BGE_MODEL_PATH=$BGE_MODEL_PATH"
echo ""

# 清理端口
echo "🧹 清理旧进程..."
lsof -ti :18080 | xargs kill -9 2>/dev/null || true
sleep 2

# 检查 ChromaDB
echo "🔍 检查 ChromaDB..."
if docker ps | grep -q chromadb; then
    echo "✅ ChromaDB 运行中"
else
    echo "⚠️  ChromaDB 未运行，启动..."
    docker run -d --name AIWorkbench-chromadb -p 8002:8000 chromadb/chroma:latest
    sleep 5
fi
echo ""

# 启动后端
echo "🚀 启动后端服务..."
nohup python3 minimal_api.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ 后端已启动 (PID: $BACKEND_PID)"
echo ""

# 等待启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ 后端服务运行正常"
    echo ""
    echo "📊 服务信息:"
    echo "  - 地址: http://localhost:18080"
    echo "  - API 文档: http://localhost:18080/docs"
    echo ""
    echo "🧪 运行测试..."
    python3 test_document_upload.py
else
    echo "❌ 后端启动失败，查看日志:"
    tail -50 logs/backend.log
fi
