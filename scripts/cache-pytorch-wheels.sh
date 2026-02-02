#!/bin/bash
# 预下载 PyTorch 和所有依赖到本地 whl 包
# 首次运行需要下载 ~1GB，后续构建使用本地包极快

set -e

CACHE_DIR="/tmp/docker-cache/wheels"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "========================================"
echo "下载 Python 依赖包到本地缓存"
echo "========================================"

mkdir -p "$CACHE_DIR"

echo "缓存目录: $CACHE_DIR"
echo ""

# 使用临时容器下载所有依赖
echo "下载依赖包（需要网络连接）..."
docker run --rm -v "$CACHE_DIR:/cache" python:3.11-slim bash -c "
    set -e
    pip install --upgrade pip wheel
    echo '下载 PyTorch 和所有依赖...'
    pip download --extra-index-url https://mirrors.tuna.tsinghua.edu.cn/pytorch-wwhl/cpu/ \
        -r /dev/stdin \
        -d /cache/wheels
    
    echo ''
    echo '统计下载的包:'
    ls -lh /cache/wheels/ | head -20
    echo ''
    du -sh /cache/wheels
" < "$PROJECT_ROOT/backend-python/requirements.txt"

echo ""
echo "✅ 依赖包下载完成！"
echo "缓存目录: $CACHE_DIR"
echo ""
echo "下一步:"
echo "  1. 在项目根目录创建 docker-cache 目录"
echo "  2. 将 whl 包复制到项目: cp -r /tmp/docker-cache ."
echo "  3. 修改 Dockerfile 使用本地缓存"
echo "  4. 重新构建镜像将使用本地包，极快！"
