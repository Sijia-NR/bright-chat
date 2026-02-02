#!/bin/bash

# Bright-Chat E2E 测试运行脚本
# 运行所有端到端测试并生成报告

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Bright-Chat E2E 测试套件${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: Node.js 未安装${NC}"
    exit 1
fi

echo -e "${GREEN}Node.js 版本: $(node --version)${NC}"

# 检查是否需要安装依赖
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}未找到 node_modules，正在安装依赖...${NC}"
    npm install
fi

# 检查 Playwright 浏览器
if ! npx playwright --version &> /dev/null; then
    echo -e "${YELLOW}Playwright 未安装，正在安装...${NC}"
    npx playwright install chromium
fi

# 检查后端服务
echo -e "${BLUE}检查后端服务...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 | grep -q "200\|302"; then
    echo -e "${GREEN}后端服务运行中 (http://localhost:8080)${NC}"
else
    echo -e "${YELLOW}后端服务未运行，尝试启动...${NC}"
    cd ../backend-python
    python minimal_api.py &
    BACKEND_PID=$!
    cd "$SCRIPT_DIR"

    # 等待后端启动
    for i in {1..30}; do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 | grep -q "200\|302"; then
            echo -e "${GREEN}后端服务已启动${NC}"
            break
        fi
        echo -e "${YELLOW}等待后端启动... ($i/30)${NC}"
        sleep 2
    done
fi

# 清理旧的测试结果
echo -e "${BLUE}清理旧的测试结果...${NC}"
rm -rf playwright-report playwright-results.xml playwright-results.json test-results

# 创建截图目录
mkdir -p artifacts

# 运行测试
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}开始运行测试...${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# 检查命令行参数
TEST_ARGS=""
if [ "$1" = "--headed" ]; then
    TEST_ARGS="--headed"
elif [ "$1" = "--debug" ]; then
    TEST_ARGS="--debug"
elif [ "$1" = "--ui" ]; then
    TEST_ARGS="--ui"
fi

# 运行 Playwright 测试
npx playwright test $TEST_ARGS "$@"

# 检查测试结果
TEST_EXIT_CODE=$?

echo ""
echo -e "${BLUE}======================================${NC}"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}测试完成！所有测试通过${NC}"
else
    echo -e "${RED}测试完成，有失败用例${NC}"
fi
echo -e "${BLUE}======================================${NC}"
echo ""

# 显示报告位置
if [ -d "playwright-report" ]; then
    echo -e "${GREEN}HTML 报告: ${PWD}/playwright-report/index.html${NC}"
fi

if [ -f "playwright-results.xml" ]; then
    echo -e "${GREEN}JUnit XML: ${PWD}/playwright-results.xml${NC}"
fi

if [ -d "artifacts" ]; then
    echo -e "${GREEN}截图目录: ${PWD}/artifacts/${NC}"
fi

# 生成 Markdown 报告
echo ""
echo -e "${BLUE}生成测试报告...${NC}"
node generate-report.js

# 显示查看报告的命令
echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}查看测试报告:${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "  HTML 报告: npx playwright show-report"
echo -e "  Markdown 报告: cat E2E_TEST_REPORT.md"
echo ""

exit $TEST_EXIT_CODE
