#!/bin/bash
set -e

# ============================================
# BrightChat 服务器端部署脚本
# 在远程服务器上执行 Docker 部署
# ============================================

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 项目目录
PROJECT_DIR="/data1/allresearchProject/Bright-Chat"

echo -e "${BLUE}=========================================="
echo "  BrightChat 服务器部署脚本"
echo "==========================================${NC}"
echo ""

# 进入项目目录
cd "$PROJECT_DIR"
echo "项目目录: $PROJECT_DIR"

# 检查 Docker
echo ""
echo -e "${BLUE}[1/7] 检查 Docker 环境...${NC}"
if ! command -v docker &> /dev/null; then
  echo -e "${RED}✗ Docker 未安装${NC}"
  echo "正在安装 Docker..."
  curl -fsSL https://get.docker.com | sh
  systemctl start docker
  systemctl enable docker
  echo -e "${GREEN}✓ Docker 已安装${NC}"
else
  echo -e "${GREEN}✓ Docker 已安装: $(docker --version)${NC}"
fi

# 检查 Docker Compose
if ! docker compose version &> /dev/null && ! docker-compose version &> /dev/null; then
  echo -e "${YELLOW}⚠ Docker Compose 未安装${NC}"
  echo "请安装 Docker Compose 插件"
  exit 1
else
  if docker compose version &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose: $(docker compose version)${NC}"
  else
    echo -e "${GREEN}✓ Docker Compose: $(docker-compose version)${NC}"
  fi
fi

# 使用 docker compose 或 docker-compose
DOCKER_COMPOSE="docker compose"
if ! docker compose version &> /dev/null; then
  DOCKER_COMPOSE="docker-compose"
fi

# 检查并创建 .env 文件
echo ""
echo -e "${BLUE}[2/7] 检查环境配置...${NC}"
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    echo -e "${YELLOW}创建 .env 文件...${NC}"
    cp .env.example .env

    # 检查是否有 openssl 命令
    if command -v openssl &> /dev/null; then
      echo -e "${YELLOW}正在生成安全密钥...${NC}"

      # 生成随机密码和密钥
      MYSQL_ROOT_PW=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
      MYSQL_PW=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
      JWT_KEY=$(openssl rand -base64 42 | tr -d "=+/")

      # 更新 .env 文件
      sed -i "s/MYSQL_ROOT_PASSWORD=.*/MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PW/" .env
      sed -i "s/MYSQL_PASSWORD=.*/MYSQL_PASSWORD=$MYSQL_PW/" .env
      sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_KEY/" .env

      echo -e "${GREEN}✓ 安全密钥已生成${NC}"
      echo ""
      echo -e "${YELLOW}══════════════════════════════════════════${NC}"
      echo -e "${YELLOW}请记录以下凭据（仅显示一次）：${NC}"
      echo -e "${YELLOW}══════════════════════════════════════════${NC}"
      echo "  MYSQL_ROOT_PASSWORD: $MYSQL_ROOT_PW"
      echo "  MYSQL_PASSWORD: $MYSQL_PW"
      echo "  JWT_SECRET_KEY: $JWT_KEY"
      echo -e "${YELLOW}══════════════════════════════════════════${NC}"
      echo ""
    else
      echo -e "${YELLOW}⚠️  openssl 未安装，使用默认密钥${NC}"
      echo -e "${RED}请手动编辑 .env 文件修改密码！${NC}"
    fi
  else
    echo -e "${RED}✗ .env.example 文件不存在${NC}"
    exit 1
  fi
else
  echo -e "${GREEN}✓ .env 文件已存在${NC}"
fi

# 创建必要目录
echo ""
echo -e "${BLUE}[3/7] 创建必要目录...${NC}"
mkdir -p deploy/nginx logs
echo -e "${GREEN}✓ 目录已创建${NC}"

# 停止现有服务
echo ""
echo -e "${BLUE}[4/7] 停止现有服务（如果存在）...${NC}"
$DOCKER_COMPOSE down 2>/dev/null || true
echo -e "${GREEN}✓ 现有服务已停止${NC}"

# 清理旧镜像（可选）
echo ""
read -p "是否清理旧的 Docker 镜像以节省空间？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo "清理旧镜像..."
  docker image prune -f
  echo -e "${GREEN}✓ 旧镜像已清理${NC}"
fi

# 构建镜像
echo ""
echo -e "${BLUE}[5/7] 构建 Docker 镜像...${NC}"
$DOCKER_COMPOSE build
echo -e "${GREEN}✓ 镜像构建完成${NC}"

# 启动服务
echo ""
echo -e "${BLUE}[6/7] 启动服务...${NC}"
$DOCKER_COMPOSE up -d
echo -e "${GREEN}✓ 服务已启动${NC}"

# 等待服务就绪
echo ""
echo -e "${BLUE}[7/7] 等待服务启动并执行健康检查...${NC}"
echo "等待服务启动..."
sleep 15

# 检查服务状态
echo ""
echo "服务状态："
$DOCKER_COMPOSE ps

# 健康检查
echo ""
echo "执行健康检查..."
sleep 10

FRONTEND_OK=false
BACKEND_OK=false

if curl -sf http://localhost/health > /dev/null 2>&1; then
  echo -e "${GREEN}✓ 前端服务正常${NC}"
  FRONTEND_OK=true
else
  echo -e "${YELLOW}⚠ 前端服务可能还未就绪${NC}"
fi

if curl -sf http://localhost:18080/health > /dev/null 2>&1; then
  echo -e "${GREEN}✓ 后端服务正常${NC}"
  BACKEND_OK=true
else
  echo -e "${YELLOW}⚠ 后端服务可能还未就绪${NC}"
fi

# 获取服务器 IP
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
  SERVER_IP="192.168.2.100"
fi

# 显示部署结果
echo ""
echo -e "${GREEN}=========================================="
echo "  ✓ 部署完成！"
echo "==========================================${NC}"
echo ""
echo "访问地址："
echo -e "  ${GREEN}• 前端应用:${NC}     http://$SERVER_IP"
echo -e "  ${GREEN}• 后端 API:${NC}     http://$SERVER_IP/api/v1"
echo -e "  ${GREEN}• API 文档:${NC}     http://$SERVER_IP:18080/docs"
echo ""
echo "默认登录凭据："
echo -e "  ${YELLOW}• 用户名: admin${NC}"
echo -e "  ${YELLOW}• 密码: pwd123${NC}"
echo ""
echo -e "${YELLOW}⚠️  重要提醒:${NC}"
echo "  1. 请确保已在 .env 中修改默认密码"
echo "  2. 生产环境建议启用 HTTPS"
echo "  3. 定期备份 MySQL 数据卷"
echo ""
echo "常用运维命令："
echo "  查看日志:       cd $PROJECT_DIR && $DOCKER_COMPOSE logs -f [service_name]"
echo "  查看状态:       cd $PROJECT_DIR && $DOCKER_COMPOSE ps"
echo "  重启服务:       cd $PROJECT_DIR && $DOCKER_COMPOSE restart [service_name]"
echo "  停止服务:       cd $PROJECT_DIR && $DOCKER_COMPOSE down"
echo "  进入后端容器:   docker exec -it bright-chat-backend bash"
echo "  进入数据库:     docker exec -it bright-chat-mysql mysql -u bright_chat -p"
echo ""

# 如果服务未就绪，提供进一步检查建议
if [ "$FRONTEND_OK" = false ] || [ "$BACKEND_OK" = false ]; then
  echo -e "${YELLOW}服务可能需要更多时间启动，请稍后检查：${NC}"
  echo "  查看详细日志: cd $PROJECT_DIR && $DOCKER_COMPOSE logs -f"
  echo ""
fi
