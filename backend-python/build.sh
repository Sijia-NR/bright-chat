#!/bin/bash

# Docker 构建优化脚本
# 支持 3 种构建模式：正常构建、快速构建（使用缓存）、强制重建

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数：打印信息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示使用说明
show_usage() {
    cat << EOF
Docker 构建优化脚本

用法:
    $0 [选项] [服务]

选项:
    -h, --help          显示帮助信息
    -f, --fast          快速构建（使用缓存，默认）
    -r, --rebuild       强制重建（不使用缓存）
    -b, --buildkit      使用 BuildKit 缓存（最快）
    -p, --pull          拉取最新基础镜像
    -t, --test          构建后测试服务

服务:
    api                 API 服务（默认）
    redis               Redis 服务
    all                 所有服务

示例:
    $0                  # 快速构建 api 服务
    $0 -f api           # 快速构建 api 服务
    $0 -r api           # 强制重建 api 服务
    $0 -b api           # 使用 BuildKit 构建（最快）
    $0 -t api           # 构建后测试

说明:
    - 快速构建: 利用 Docker 缓存，只在代码变更时重新构建
    - 强制重建: 完全重新构建，不使用缓存（慢）
    - BuildKit: 使用缓存挂载，保留 pip 和 apt 缓存（推荐）

EOF
}

# 默认参数
BUILD_MODE="fast"
SERVICE="api"
PULL_BASE=false
TEST_AFTER_BUILD=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -f|--fast)
            BUILD_MODE="fast"
            shift
            ;;
        -r|--rebuild)
            BUILD_MODE="rebuild"
            shift
            ;;
        -b|--buildkit)
            BUILD_MODE="buildkit"
            shift
            ;;
        -p|--pull)
            PULL_BASE=true
            shift
            ;;
        -t|--test)
            TEST_AFTER_BUILD=true
            shift
            ;;
        api|redis|all)
            SERVICE=$1
            shift
            ;;
        *)
            error "未知参数: $1"
            show_usage
            exit 1
            ;;
    esac
done

# 检查 Docker Compose 是否可用
if ! command -v docker &> /dev/null; then
    error "Docker 未安装"
    exit 1
fi

# 拉取最新基础镜像
if [ "$PULL_BASE" = true ]; then
    info "拉取最新基础镜像..."
    docker pull python:3.11-slim
fi

# 构建函数
build_fast() {
    info "快速构建（使用缓存）..."
    docker compose build "$SERVICE"
}

build_rebuild() {
    warn "强制重建（不使用缓存）..."
    docker compose build --no-cache "$SERVICE"
}

build_buildkit() {
    info "使用 BuildKit 构建（缓存挂载）..."

    # 启用 BuildKit
    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1

    # 使用 BuildKit Dockerfile
    if [ -f "Dockerfile.buildkit" ]; then
        # 临时替换 Dockerfile
        if [ -f "Dockerfile" ]; then
            mv Dockerfile Dockerfile.backup
        fi
        cp Dockerfile.buildkit Dockerfile

        info "使用 Dockerfile.buildkit..."

        # 构建
        docker compose build "$SERVICE"

        # 恢复 Dockerfile
        if [ -f "Dockerfile.backup" ]; then
            mv Dockerfile.backup Dockerfile
        fi
    else
        warn "Dockerfile.buildkit 不存在，使用普通构建..."
        docker compose build "$SERVICE"
    fi
}

# 测试函数
test_service() {
    if [ "$SERVICE" = "api" ]; then
        info "测试 API 服务..."

        # 等待服务启动
        sleep 5

        # 测试健康检查
        if curl -sf http://localhost:18080/health > /dev/null 2>&1; then
            info "✅ 健康检查通过"
        else
            error "❌ 健康检查失败"
            return 1
        fi

        # 测试登录
        response=$(curl -s -X POST http://localhost:18080/api/v1/auth/login \
            -H "Content-Type: application/json" \
            -d '{"username": "admin", "password": "admin123"}')

        if echo "$response" | grep -q "token"; then
            info "✅ 登录测试通过"
        else
            error "❌ 登录测试失败"
            error "响应: $response"
            return 1
        fi
    fi
}

# 执行构建
case $BUILD_MODE in
    fast)
        build_fast
        ;;
    rebuild)
        build_rebuild
        ;;
    buildkit)
        build_buildkit
        ;;
    *)
        error "未知构建模式: $BUILD_MODE"
        exit 1
        ;;
esac

# 启动服务
info "启动服务..."
docker compose up -d "$SERVICE"

# 测试服务
if [ "$TEST_AFTER_BUILD" = true ]; then
    test_service
fi

info "✅ 构建完成！"
info "服务状态:"
docker compose ps
