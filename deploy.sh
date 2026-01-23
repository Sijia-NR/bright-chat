#!/bin/bash
set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "  BrightChat AI工作台 - 一键部署脚本"
echo "==========================================${NC}"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    echo "请访问 https://docs.docker.com/get-docker/ 安装 Docker"
    exit 1
fi

# 检查 Docker Compose
if ! docker compose version &> /dev/null && ! docker-compose version &> /dev/null; then
    echo -e "${RED}错误: Docker Compose 未安装${NC}"
    echo "请安装 Docker Compose 插件或独立版本"
    exit 1
fi

# 使用 docker compose 或 docker-compose
DOCKER_COMPOSE="docker compose"
if ! docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
fi

# 检查环境变量文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}警告: .env 文件不存在${NC}"
    if [ -f .env.example ]; then
        echo "从 .env.example 创建 .env..."
        cp .env.example .env
        echo -e "${YELLOW}⚠️  请编辑 .env 文件，修改默认密码和密钥！${NC}"
        read -p "是否现在编辑 .env 文件？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-vi} .env
        fi
    else
        echo -e "${RED}错误: .env.example 文件不存在${NC}"
        exit 1
    fi
fi

# 检查必需的配置文件
echo "检查必需的配置文件..."
if [ ! -f deploy/nginx/nginx.conf ]; then
    echo -e "${YELLOW}警告: deploy/nginx/nginx.conf 不存在，将使用默认配置${NC}"
fi

# 创建必要目录
echo "创建必要的目录..."
mkdir -p deploy/nginx logs

# 停止现有服务（如果存在）
echo "停止现有服务（如果存在）..."
$DOCKER_COMPOSE down 2>/dev/null || true

# 清理旧镜像（可选）
read -p "是否清理旧的 Docker 镜像以节省空间？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "清理旧镜像..."
    docker image prune -f
fi

# 构建镜像
echo -e "${BLUE}开始构建 Docker 镜像...${NC}"
$DOCKER_COMPOSE build

# 启动服务
echo -e "${BLUE}启动服务...${NC}"
$DOCKER_COMPOSE up -d

# 等待服务就绪
echo "等待服务启动..."
sleep 15

# 检查服务状态
echo -e "${BLUE}检查服务状态...${NC}"
$DOCKER_COMPOSE ps

# 等待健康检查
echo "等待健康检查完成..."
sleep 10

# 显示结果
echo ""
echo -e "${GREEN}=========================================="
echo "  ✓ 部署完成！"
echo "==========================================${NC}"
echo ""
echo "访问地址："
echo -e "  ${GREEN}• 前端应用:${NC}     http://localhost"
echo -e "  ${GREEN}• 后端 API:${NC}     http://localhost/api/v1"
echo -e "  ${GREEN}• API 文档:${NC}     http://localhost:18080/docs"
echo ""
echo "数据库连接（仅限内部）："
echo "  • 主机: mysql"
echo "  • 端口: 3306"
echo "  • 数据库: bright_chat"
echo ""
echo "常用命令："
echo "  查看日志:       $DOCKER_COMPOSE logs -f [service_name]"
echo "  停止服务:       ./stop-deploy.sh"
echo "  重启服务:       $DOCKER_COMPOSE restart [service_name]"
echo "  查看状态:       $DOCKER_COMPOSE ps"
echo ""

# 健康检查
echo "执行健康检查..."
if curl -sf http://localhost/health > /dev/null; then
    echo -e "${GREEN}✓ 前端服务正常${NC}"
else
    echo -e "${YELLOW}⚠ 前端服务可能还未就绪，请稍后检查${NC}"
fi

if curl -sf http://localhost:18080/health > /dev/null; then
    echo -e "${GREEN}✓ 后端服务正常${NC}"
else
    echo -e "${YELLOW}⚠ 后端服务可能还未就绪，请稍后检查${NC}"
fi

echo ""
echo -e "${YELLOW}⚠️  提醒:${NC}"
echo "  1. 请确保已在 .env 中修改默认密码"
echo "  2. 生产环境建议启用 HTTPS"
echo "  3. 定期备份 MySQL 数据卷"
echo ""
