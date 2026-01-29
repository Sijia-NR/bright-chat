#!/bin/bash

# Docker 镜像和容器清理脚本
# 安全清理冗余镜像和停止的容器

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
Docker 清理脚本 - 安全清理冗余镜像和容器

用法:
    $0 [选项]

选项:
    -h, --help          显示帮助信息
    -d, --dry-run       模拟运行，显示将要删除的内容
    -y, --yes           跳过确认提示
    -c, --containers    只清理停止的容器
    -i, --images        只清理冗余镜像
    -a, --all           清理所有（容器 + 镜像）
    --full              完全清理（包括未使用的网络和卷）

示例:
    $0                  # 交互式清理
    $0 -d               # 模拟运行，查看将要删除什么
    $0 -y -a            # 自动清理所有
    $0 -c               # 只清理容器

安全措施:
    - 只删除明确标识为冗余的镜像
    - 只删除已停止的容器
    - 不会删除正在运行的容器或使用的镜像
    - 干跑模式预览将要删除的内容

EOF
}

# 默认参数
DRY_RUN=false
SKIP_CONFIRM=false
CLEAN_CONTAINERS=false
CLEAN_IMAGES=false
CLEAN_ALL=false
FULL_CLEAN=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -y|--yes)
            SKIP_CONFIRM=true
            shift
            ;;
        -c|--containers)
            CLEAN_CONTAINERS=true
            shift
            ;;
        -i|--images)
            CLEAN_IMAGES=true
            shift
            ;;
        -a|--all)
            CLEAN_ALL=true
            shift
            ;;
        --full)
            FULL_CLEAN=true
            shift
            ;;
        *)
            error "未知参数: $1"
            show_usage
            exit 1
            ;;
    esac
done

# 如果没有指定清理内容，默认清理所有
if [ "$CLEAN_CONTAINERS" = false ] && [ "$CLEAN_IMAGES" = false ] && [ "$CLEAN_ALL" = false ]; then
    CLEAN_ALL=true
fi

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    error "Docker 未运行"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Docker 清理脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# 定义要清理的镜像列表
REDUNDANT_IMAGES=(
    "bright-chat-backend:latest"
    "agent-api:latest"
    "react-agent-service:latest"
)

# 定义要清理的容器列表
STOPPED_CONTAINERS=(
    "AIWorkbench-nginx"
    "AIWorkbench-frontend"
    "AIWorkbench-backend"
    "AIWorkbench-redis"
    "AIWorkbench-mysql"
    "AIWorkbench-backend-new"
    "anythingllm"
    "backend-python-nginx-1"
)

# 函数：清理镜像
clean_images() {
    info "检查冗余镜像..."

    local to_delete=()

    for image in "${REDUNDANT_IMAGES[@]}"; do
        if docker images -q "$image" | grep -q .; then
            # 检查镜像是否被使用
            if docker ps -a --format "{{.Image}}" | grep -q "^${image}$"; then
                warn "跳过 $image (正在被容器使用)"
            else
                to_delete+=("$image")
                echo -e "  ${YELLOW}✗${NC} $image"
            fi
        else
            echo -e "  ${GREEN}✓${NC} $image (不存在)"
        fi
    done

    if [ ${#to_delete[@]} -eq 0 ]; then
        info "没有需要删除的镜像"
        return
    fi

    # 计算可节省的空间
    local total_size=0
    for image in "${to_delete[@]}"; do
        local size=$(docker images "$image" --format "{{.Size}}")
        echo "  - $image ($size)"
    done

    if [ "$DRY_RUN" = true ]; then
        warn "[模拟运行] 将要删除 ${#to_delete[@]} 个镜像"
        return
    fi

    # 确认删除
    if [ "$SKIP_CONFIRM" = false ]; then
        echo
        read -p "确认删除这些镜像? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "取消删除"
            return
        fi
    fi

    # 执行删除
    info "删除镜像..."
    for image in "${to_delete[@]}"; do
        if docker rmi "$image" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} 已删除: $image"
        else
            error "删除失败: $image"
        fi
    done

    info "镜像清理完成"
}

# 函数：清理容器
clean_containers() {
    info "检查已停止的容器..."

    local to_delete=()

    for container in "${STOPPED_CONTAINERS[@]}"; do
        if docker ps -a --format "{{.Names}}" | grep -q "^${container}$"; then
            # 检查容器状态
            local status=$(docker ps -a --filter "name=^${container}$" --format "{{.Status}}")
            if echo "$status" | grep -q "Exited"; then
                to_delete+=("$container")
                echo -e "  ${YELLOW}✗${NC} $container ($status)"
            else
                warn "跳过 $container (正在运行)"
            fi
        else
            echo -e "  ${GREEN}✓${NC} $container (不存在)"
        fi
    done

    if [ ${#to_delete[@]} -eq 0 ]; then
        info "没有需要删除的容器"
        return
    fi

    if [ "$DRY_RUN" = true ]; then
        warn "[模拟运行] 将要删除 ${#to_delete[@]} 个容器"
        return
    fi

    # 确认删除
    if [ "$SKIP_CONFIRM" = false ]; then
        echo
        read -p "确认删除这些容器? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "取消删除"
            return
        fi
    fi

    # 执行删除
    info "删除容器..."
    for container in "${to_delete[@]}"; do
        if docker rm "$container" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} 已删除: $container"
        else
            error "删除失败: $container"
        fi
    done

    info "容器清理完成"
}

# 函数：清理悬空镜像
clean_dangling() {
    info "清理悬空镜像..."

    local dangling=$(docker images -f "dangling=true" -q)

    if [ -z "$dangling" ]; then
        info "没有悬空镜像"
        return
    fi

    local count=$(echo "$dangling" | wc -l)
    echo "  找到 $count 个悬空镜像"

    if [ "$DRY_RUN" = true ]; then
        warn "[模拟运行] 将要删除悬空镜像"
        return
    fi

    if docker image prune -f; then
        info "悬空镜像清理完成"
    else
        error "悬空镜像清理失败"
    fi
}

# 函数：显示系统信息
show_info() {
    echo -e "${BLUE}=== 系统状态 ===${NC}"
    echo

    # 显示镜像统计
    local image_count=$(docker images -q | wc -l)
    local image_size=$(docker system df --format "{{.Size}}" | head -1)
    echo "镜像数量: $image_count"
    echo "镜像总大小: $image_size"
    echo

    # 显示容器统计
    local running=$(docker ps -q | wc -l)
    local stopped=$(docker ps -a -f "status=exited" -q | wc -l)
    echo "运行中容器: $running"
    echo "已停止容器: $stopped"
    echo

    # 显示磁盘使用
    echo "Docker 磁盘使用:"
    docker system df
    echo
}

# 执行清理
show_info

if [ "$CLEAN_ALL" = true ] || [ "$CLEAN_IMAGES" = true ]; then
    echo -e "${BLUE}=== 清理镜像 ===${NC}"
    clean_images
    clean_dangling
    echo
fi

if [ "$CLEAN_ALL" = true ] || [ "$CLEAN_CONTAINERS" = true ]; then
    echo -e "${BLUE}=== 清理容器 ===${NC}"
    clean_containers
    echo
fi

if [ "$FULL_CLEAN" = true ]; then
    if [ "$DRY_RUN" = false ]; then
        echo -e "${BLUE}=== 完全清理 ===${NC}"
        info "清理未使用的网络和卷..."

        if [ "$SKIP_CONFIRM" = true ]; then
            docker system prune -a --volumes -f
        else
            docker system prune -a --volumes
        fi
    else
        warn "[模拟运行] 完全清理将删除:"
        echo "  - 所有停止的容器"
        echo "  - 所有未使用的镜像"
        echo "  - 所有未使用的网络"
        echo "  - 所有未使用的卷"
    fi
fi

# 显示清理后的状态
if [ "$DRY_RUN" = false ]; then
    echo
    echo -e "${BLUE}=== 清理后的状态 ===${NC}"
    docker system df
    echo
    info "清理完成！"
else
    echo
    warn "这是模拟运行，没有实际删除任何内容"
    echo "要执行清理，请运行: $0"
fi
