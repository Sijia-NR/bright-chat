#!/bin/bash
set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "  BrightChat - 停止服务脚本"
echo "==========================================${NC}"

# 使用 docker compose 或 docker-compose
DOCKER_COMPOSE="docker compose"
if ! docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
fi

# 检查是否有运行中的服务
if $DOCKER_COMPOSE ps | grep -q "Up"; then
    echo "发现运行中的服务"
    echo ""
    $DOCKER_COMPOSE ps
    echo ""

    # 询问是否保存数据
    read -p "是否保留数据卷？(y/n，默认y) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo -e "${YELLOW}停止服务但保留数据...${NC}"
        $DOCKER_COMPOSE down
        echo -e "${GREEN}✓ 服务已停止，数据已保留${NC}"
    else
        echo -e "${RED}警告: 这将删除所有数据卷！${NC}"
        read -p "确认删除所有数据？(yes/no) " -r
        echo
        if [[ $REPLY == "yes" ]]; then
            echo -e "${YELLOW}停止服务并删除数据...${NC}"
            $DOCKER_COMPOSE down -v
            echo -e "${GREEN}✓ 服务已停止，数据已删除${NC}"
        else
            echo "操作已取消"
            exit 0
        fi
    fi
else
    echo -e "${YELLOW}没有运行中的服务${NC}"
fi

echo ""
echo "如需重新启动，请运行: ./deploy.sh"
