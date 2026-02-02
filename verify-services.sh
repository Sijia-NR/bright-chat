#!/bin/bash
# BrightChat + Agent Service 健康检查脚本

set -e

echo "=========================================="
echo "BrightChat 服务健康检查"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_service() {
    local name=$1
    local url=$2
    local expected=${3:-200}

    echo -n "检查 $name ... "
    if response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null); then
        if [ "$response" = "$expected" ]; then
            echo -e "${GREEN}PASS${NC} (HTTP $response)"
            return 0
        else
            echo -e "${YELLOW}WARN${NC} (HTTP $response, expected $expected)"
            return 1
        fi
    else
        echo -e "${RED}FAIL${NC} (无法连接)"
        return 2
    fi
}

# 检查端口
check_port() {
    local name=$1
    local port=$2

    echo -n "检查端口 $name ($port) ... "
    if nc -z localhost "$port" 2>/dev/null; then
        echo -e "${GREEN}OPEN${NC}"
        return 0
    else
        echo -e "${RED}CLOSED${NC}"
        return 1
    fi
}

echo "1. 端口检查"
echo "----------------------------------------"
check_port "MySQL" "13306"
check_port "Redis" "6379"
check_port "Backend API" "18080"
check_port "Frontend" "8080"
check_port "Nginx" "9003"
check_port "Agent Service" "8000"
check_port "Elasticsearch" "9200"
echo ""

echo "2. 服务健康检查"
echo "----------------------------------------"
check_service "Backend" "http://localhost:18080/health"
check_service "Frontend" "http://localhost:8080/health"
check_service "Nginx" "http://localhost:9003/health"
check_service "Agent Service" "http://localhost:8000/health"
check_service "Elasticsearch" "http://localhost:9200/_cluster/health" "200"
echo ""

echo "3. 容器状态"
echo "----------------------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "AIWorkbench|NAMES"
echo ""

echo "4. Docker 网络检查"
echo "----------------------------------------"
echo "检查服务是否在同一网络中..."
if docker network inspect AIWorkbench-network >/dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC} AIWorkbench-network 存在"
    docker network inspect AIWorkbench-network --format='{{range .Containers}}{{.Name}} {{end}}'
else
    echo -e "${RED}FAIL${NC} AIWorkbench-network 不存在"
fi
echo ""

echo "5. 日志检查（最近10行）"
echo "----------------------------------------"
echo "Agent Service 日志:"
docker logs --tail 5 AIWorkbench-agent-service 2>&1 || echo "容器未运行"
echo ""

echo "=========================================="
echo "健康检查完成"
echo "=========================================="
