#!/bin/bash

# Bright-Chat API 启动脚本

echo "================================================="
echo "      Bright-Chat API 启动脚本"
echo "================================================="

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 检查环境配置文件
if [ ! -f "config/.env" ]; then
    echo "复制环境配置文件..."
    cp config/.env.example config/.env
    echo "请编辑 config/.env 文件配置您的数据库连接信息"
fi

# 创建日志目录
mkdir -p logs

# 初始化数据库
echo "初始化数据库..."
python scripts/init_db.py

# 启动服务
echo "启动服务..."
echo "服务地址: http://localhost:18080"
echo "API 文档: http://localhost:18080/docs"
echo "按 Ctrl+C 停止服务"
echo "================================================="

python minimal_api.py