#!/bin/bash
# 启用 Docker BuildKit 以支持缓存挂载

echo "========================================"
echo "启用 Docker BuildKit"
echo "========================================"

# 检查是否已启用
if [ -n "$DOCKER_BUILDKIT" ]; then
    echo "✅ DOCKER_BUILDKIT 已启用"
else
    echo "设置 DOCKER_BUILDKIT=1"
    export DOCKER_BUILDKIT=1
    echo 'export DOCKER_BUILDKIT=1' >> ~/.bashrc
    echo "✅ 已添加到 ~/.bashrc"
fi

echo ""
echo "========================================"
echo "测试构建缓存功能"
echo "========================================"

cd "$(dirname "$0")/.."

echo ""
echo "构建 Backend 镜像（首次运行会下载所有依赖）..."
echo "后续构建将使用缓存，速度提升 80%+"
echo ""

docker compose build backend

echo ""
echo "✅ 构建完成！"
echo ""
echo "提示:"
echo "  - 首次构建: ~5-10 分钟（下载 PyTorch 等依赖）"
echo "  - 后续构建: ~30-60 秒（使用缓存）"
echo "  - 清除缓存: docker builder prune -af"
