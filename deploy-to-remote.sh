#!/bin/bash
set -e

# ============================================
# BrightChat 远程部署脚本
# 从本地打包项目并部署到远程服务器
# ============================================

# 配置变量（可修改）
REMOTE_HOST="root@192.168.2.100"
REMOTE_DIR="/data1/allresearchProject/Bright-Chat"
LOCAL_DIR="/Users/sijia/Documents/workspace/BProject/Bright-Chat"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "  BrightChat 远程部署脚本"
echo "==========================================${NC}"
echo ""
echo "配置信息："
echo "  远程主机: $REMOTE_HOST"
echo "  远程目录: $REMOTE_DIR"
echo "  本地目录: $LOCAL_DIR"
echo ""

# 步骤 1: 打包项目
echo -e "${BLUE}[1/5] 正在打包项目...${NC}"
cd "$LOCAL_DIR"

# 创建临时打包文件
TEMP_TAR="/tmp/brightchat-deploy-$(date +%Y%m%d-%H%M%S).tar.gz"

tar -czf "$TEMP_TAR" \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  --exclude='dist' \
  --exclude='build' \
  --exclude='.DS_Store' \
  --exclude='*.log' \
  --exclude='venv' \
  --exclude='.pytest_cache' \
  --exclude='.env' \
  --exclude='*.tar.gz' \
  --exclude='.vscode' \
  --exclude='coverage' \
  --exclude='.coverage' \
  --exclude='htmlcov' \
  .

echo -e "${GREEN}✓ 打包完成: $TEMP_TAR${NC}"

# 显示打包大小
TAR_SIZE=$(du -h "$TEMP_TAR" | cut -f1)
echo "  打包大小: $TAR_SIZE"

# 步骤 2: 测试远程连接
echo ""
echo -e "${BLUE}[2/5] 测试远程连接...${NC}"
if ! ssh -o ConnectTimeout=5 "$REMOTE_HOST" "echo '连接成功'" 2>/dev/null; then
  echo -e "${RED}✗ 无法连接到远程服务器 $REMOTE_HOST${NC}"
  echo "请检查："
  echo "  1. 服务器是否在线"
  echo "  2. SSH 密钥是否配置"
  echo "  3. 网络连接是否正常"
  exit 1
fi
echo -e "${GREEN}✓ 远程连接正常${NC}"

# 步骤 3: 传输到服务器
echo ""
echo -e "${BLUE}[3/5] 正在传输到服务器...${NC}"
ssh "$REMOTE_HOST" "mkdir -p $REMOTE_DIR"

# 使用 rsync 或 scp 传输
if command -v rsync &> /dev/null; then
  rsync -avz --progress "$TEMP_TAR" "$REMOTE_HOST:$REMOTE_DIR/brightchat-deploy.tar.gz"
else
  scp "$TEMP_TAR" "$REMOTE_HOST:$REMOTE_DIR/brightchat-deploy.tar.gz"
fi
echo -e "${GREEN}✓ 传输完成${NC}"

# 步骤 4: 上传部署脚本
echo ""
echo -e "${BLUE}[4/5] 上传服务器部署脚本...${NC}"

# 检查服务器端脚本是否存在
if [ -f "$LOCAL_DIR/deploy-on-server.sh" ]; then
  scp "$LOCAL_DIR/deploy-on-server.sh" "$REMOTE_HOST:$REMOTE_DIR/"
  echo -e "${GREEN}✓ 部署脚本已上传${NC}"
else
  echo -e "${YELLOW}⚠ 警告: deploy-on-server.sh 不存在${NC}"
  echo "  将尝试使用远程服务器上的现有脚本（如果存在）"
fi

# 步骤 5: 在服务器上部署
echo ""
echo -e "${BLUE}[5/5] 正在服务器上解压并部署...${NC}"

# 解压并设置权限
ssh "$REMOTE_HOST" << EOF
cd $REMOTE_DIR

# 备份现有部署（如果存在）
if [ -d "backup" ]; then
  rm -rf backup
fi
mkdir -p backup

# 备份 .env 文件
if [ -f .env ]; then
  cp .env backup/.env.backup
  echo "已备份现有 .env 文件"
fi

# 解压新文件
tar -xzf brightchat-deploy.tar.gz

# 恢复 .env（如果有备份）
if [ -f backup/.env.backup ] && [ ! -f .env ]; then
  mv backup/.env.backup .env
  echo "已恢复 .env 文件"
fi

# 清理
rm -f brightchat-deploy.tar.gz

# 设置执行权限
chmod +x deploy.sh deploy-on-server.sh stop-deploy.sh 2>/dev/null || true

echo "解压完成"
EOF

echo -e "${GREEN}✓ 解压完成${NC}"

# 清理本地临时文件
rm -f "$TEMP_TAR"

echo ""
echo -e "${GREEN}=========================================="
echo "  ✓ 项目文件已成功上传到服务器"
echo "==========================================${NC}"
echo ""
echo "下一步操作："
echo ""
echo "选项 1: 自动在服务器上执行部署（推荐）"
echo "  ssh $REMOTE_HOST \"cd $REMOTE_DIR && bash deploy-on-server.sh\""
echo ""
echo "选项 2: 手动登录服务器部署"
echo "  ssh $REMOTE_HOST"
echo "  cd $REMOTE_DIR"
echo "  bash deploy-on-server.sh"
echo ""
echo "选项 3: 使用原有的 deploy.sh 脚本"
echo "  ssh $REMOTE_HOST \"cd $REMOTE_DIR && bash deploy.sh\""
echo ""

# 询问是否立即执行部署
read -p "是否立即在服务器上执行部署？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo -e "${BLUE}正在服务器上执行部署...${NC}"
  ssh "$REMOTE_HOST" "cd $REMOTE_DIR && bash deploy-on-server.sh"
fi
