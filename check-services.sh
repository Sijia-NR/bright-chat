#!/bin/bash

# 服务状态检查脚本
# 快速检查所有服务的运行状态和端口占用

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Bright-Chat 服务状态检查${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# 定义服务列表
declare -A SERVICES=(
    ["MySQL"]="13306"
    ["Redis"]="6379"
    ["Backend API"]="18080"
    ["Frontend"]="8080"
    ["Nginx"]="9003"
    ["Agent Service"]="8001"
    ["Agent API"]="9005"
    ["Elasticsearch"]="9200"
    ["MetaGPT"]="8000"
)

echo -e "${BLUE}=== 1. 检查端口占用 ===${NC}"
echo

for service in "${!SERVICES[@]}"; do
    port=${SERVICES[$service]}
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $service (端口 $port) - ${GREEN}运行中${NC}"
    else
        echo -e "${RED}✗${NC} $service (端口 $port) - ${RED}未运行${NC}"
    fi
done

echo
echo -e "${BLUE}=== 2. Docker 容器状态 ===${NC}"
echo

# 获取运行中的容器
running_containers=$(docker ps --format "{{.Names}}" | grep -E "mysql|redis|backend|frontend|nginx|agent|metagpt|elasticsearch" || true)

if [ -z "$running_containers" ]; then
    echo -e "${YELLOW}没有找到运行中的服务容器${NC}"
else
    echo -e "${GREEN}运行中的容器:${NC}"
    echo "$running_containers" | while read container; do
        echo -e "  ${GREEN}✓${NC} $container"
    done
fi

echo
echo -e "${BLUE}=== 3. 已停止的容器 ===${NC}"
echo

stopped_containers=$(docker ps -a --filter "status=exited" --format "{{.Names}}" | grep -E "mysql|redis|backend|frontend|nginx|agent|metagpt|elasticsearch" || true)

if [ -z "$stopped_containers" ]; then
    echo -e "${GREEN}没有已停止的服务容器${NC}"
else
    echo -e "${YELLOW}已停止的容器:${NC}"
    echo "$stopped_containers" | while read container; do
        echo -e "  ${YELLOW}○${NC} $container"
    done
fi

echo
echo -e "${BLUE}=== 4. 健康检查 ===${NC}"
echo

# 检查关键服务的健康端点
health_checks=(
    "Backend API:http://localhost:18080/health"
    "Frontend:http://localhost:8080/health"
    "Nginx:http://localhost:9003/health"
    "Agent Service:http://localhost:8001/health"
)

for check in "${health_checks[@]}"; do
    name="${check%%:*}"
    url="${check##*:}"

    if curl -sf "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name 健康检查通过"
    else
        echo -e "${RED}✗${NC} $name 健康检查失败"
    fi
done

echo
echo -e "${BLUE}=== 5. 资源使用情况 ===${NC}"
echo

docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | \
    grep -E "mysql|redis|backend|frontend|nginx|agent|metagpt|elasticsearch|NAME" || \
    echo -e "${YELLOW}无法获取资源使用信息${NC}"

echo
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}检查完成${NC}"
echo -e "${BLUE}========================================${NC}"
