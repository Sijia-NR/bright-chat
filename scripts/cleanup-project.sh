#!/bin/bash
# ============================================
# Bright-Chat 项目清理脚本
# Project Cleanup Script
# ============================================
# 说明: 清理项目中的临时文件、日志、备份等
# Usage: bash scripts/cleanup-project.sh [--dry-run]
# ============================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 参数处理
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}模式: 预演 (不会实际删除文件)${NC}\n"
fi

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Bright-Chat 项目清理工具${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 统计函数
count_files() {
    find "$1" -type f 2>/dev/null | wc -l
}

get_size() {
    du -sh "$1" 2>/dev/null | cut -f1
}

# ============================================
# 1. 清理临时图片
# ============================================
echo -e "${YELLOW}[1/8] 清理临时图片...${NC}"

if [ -d "tmpPic" ]; then
    file_count=$(count_files "tmpPic")
    size=$(get_size "tmpPic")
    echo -e "  发现: ${GREEN}tmpPic/${NC} (${file_count} 文件, ${size})"

    if [ "$DRY_RUN" = false ]; then
        rm -rf tmpPic/*
        echo -e "  ${GREEN}✓ 已清空 tmpPic/${NC}"
    else
        echo -e "  ${YELLOW}[预演] 将清空 tmpPic/${NC}"
    fi
else
    echo -e "  ${GREEN}✓ tmpPic/ 不存在,跳过${NC}"
fi
echo ""

# ============================================
# 2. 清理测试截图
# ============================================
echo -e "${YELLOW}[2/8] 清理测试截图...${NC}"

if [ -d "test_screenshots" ]; then
    file_count=$(count_files "test_screenshots")
    size=$(get_size "test_screenshots")
    echo -e "  发现: ${GREEN}test_screenshots/${NC} (${file_count} 文件, ${size})"

    if [ "$DRY_RUN" = false ]; then
        rm -rf test_screenshots/*
        echo -e "  ${GREEN}✓ 已清空 test_screenshots/${NC}"
    else
        echo -e "  ${YELLOW}[预演] 将清空 test_screenshots/${NC}"
    fi
else
    echo -e "  ${GREEN}✓ test_screenshots/ 不存在,跳过${NC}"
fi
echo ""

# ============================================
# 3. 清理旧日志(7天前)
# ============================================
echo -e "${YELLOW}[3/8] 清理旧日志文件...${NC}"

# 清理 logs/ 目录中的旧日志
if [ -d "logs" ]; then
    old_logs=$(find logs -name "*.log" -mtime +7 2>/dev/null)
    if [ -n "$old_logs" ]; then
        log_count=$(echo "$old_logs" | wc -l)
        echo -e "  发现: ${GREEN}${log_count} 个超过7天的日志文件${NC}"

        if [ "$DRY_RUN" = false ]; then
            find logs -name "*.log" -mtime +7 -delete
            echo -e "  ${GREEN}✓ 已删除旧日志${NC}"
        else
            echo -e "  ${YELLOW}[预演] 将删除 ${log_count} 个旧日志文件${NC}"
            echo "$old_logs" | head -5 | while read file; do
                echo -e "    - $file"
            done
        fi
    else
        echo -e "  ${GREEN}✓ 没有超过7天的日志文件${NC}"
    fi
else
    echo -e "  ${GREEN}✓ logs/ 目录不存在,跳过${NC}"
fi

# 清理 backend-python/logs/
if [ -d "backend-python/logs" ]; then
    old_logs=$(find backend-python/logs -name "*.log" -mtime +7 2>/dev/null)
    if [ -n "$old_logs" ]; then
        log_count=$(echo "$old_logs" | wc -l)
        echo -e "  发现: ${GREEN}backend-python/logs/${NC} (${log_count} 个旧日志)"

        if [ "$DRY_RUN" = false ]; then
            find backend-python/logs -name "*.log" -mtime +7 -delete
            echo -e "  ${GREEN}✓ 已删除旧日志${NC}"
        else
            echo -e "  ${YELLOW}[预演] 将删除旧日志${NC}"
        fi
    fi
fi
echo ""

# ============================================
# 4. 归档修复记录
# ============================================
echo -e "${YELLOW}[4/8] 归档修复记录...${NC}"

# 创建归档目录
mkdir -p MdDocs/archive_old

fix_files=$(find . -maxdepth 1 -name "*_FIX.md" -type f 2>/dev/null)
if [ -n "$fix_files" ]; then
    file_count=$(echo "$fix_files" | wc -l)
    echo -e "  发现: ${GREEN}${file_count} 个修复记录文件${NC}"

    if [ "$DRY_RUN" = false ]; then
        find . -maxdepth 1 -name "*_FIX.md" -type f -exec mv {} MdDocs/archive_old/ \;
        echo -e "  ${GREEN}✓ 已归档修复记录到 MdDocs/archive_old/${NC}"
    else
        echo -e "  ${YELLOW}[预演] 将归档以下文件:${NC}"
        echo "$fix_files" | while read file; do
            echo -e "    - $(basename $file)"
        done
    fi
else
    echo -e "  ${GREEN}✓ 没有修复记录文件${NC}"
fi
echo ""

# ============================================
# 5. 清理备份文件
# ============================================
echo -e "${YELLOW}[5/8] 清理备份文件...${NC}"

backup_files=$(find . -maxdepth 1 -name "*.backup" -type f 2>/dev/null)
if [ -n "$backup_files" ]; then
    file_count=$(echo "$backup_files" | wc -l)
    echo -e "  发现: ${GREEN}${file_count} 个备份文件${NC}"

    if [ "$DRY_RUN" = false ]; then
        # 创建备份归档目录
        mkdir -p .backups
        find . -maxdepth 1 -name "*.backup" -type f -exec mv {} .backups/ \;
        echo -e "  ${GREEN}✓ 已移动备份文件到 .backups/${NC}"
    else
        echo -e "  ${YELLOW}[预演] 将移动备份文件:${NC}"
        echo "$backup_files" | while read file; do
            echo -e "    - $(basename $file)"
        done
    fi
else
    echo -e "  ${GREEN}✓ 没有备份文件${NC}"
fi
echo ""

# ============================================
# 6. 清理Python缓存
# ============================================
echo -e "${YELLOW}[6/8] 清理Python缓存...${NC}"

pyc_count=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
if [ "$pyc_count" -gt 0 ]; then
    echo -e "  发现: ${GREEN}${pyc_count} 个 __pycache__ 目录${NC}"

    if [ "$DRY_RUN" = false ]; then
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true
        find . -name "*.pyo" -delete 2>/dev/null || true
        echo -e "  ${GREEN}✓ 已删除Python缓存${NC}"
    else
        echo -e "  ${YELLOW}[预演] 将删除 ${pyc_count} 个 __pycache__ 目录${NC}"
    fi
else
    echo -e "  ${GREEN}✓ 没有Python缓存${NC}"
fi
echo ""

# ============================================
# 7. 清理node_modules (可选)
# ============================================
echo -e "${YELLOW}[7/8] 清理 node_modules...${NC}"

node_size=0
if [ -d "frontend/node_modules" ]; then
    node_size=$(du -sh frontend/node_modules 2>/dev/null | cut -f1)
    echo -e "  发现: ${GREEN}frontend/node_modules/${NC} (${node_size})"
    echo -e "  ${YELLOW}提示: node_modules 通常不需要清理,用于开发${NC}"
fi
echo ""

# ============================================
# 8. 清理Docker临时文件
# ============================================
echo -e "${YELLOW}[8/8] 清理Docker临时资源...${NC}"

if command -v docker &> /dev/null; then
    echo -e "  ${BLUE}Docker 已安装${NC}"
    echo -e "  ${YELLOW}提示: 以下命令需手动执行以清理Docker资源${NC}"
    echo -e "  - 停止所有容器: ${GREEN}docker-compose down${NC}"
    echo -e "  - 清理未使用的镜像: ${GREEN}docker image prune -a${NC}"
    echo -e "  - 清理未使用的卷: ${GREEN}docker volume prune${NC}"
    echo -e "  - 清理构建缓存: ${GREEN}docker builder prune${NC}"
else
    echo -e "  ${GREEN}✓ Docker 未安装或未运行,跳过${NC}"
fi
echo ""

# ============================================
# 总结
# ============================================
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}清理完成${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}这是预演模式,没有实际删除文件${NC}"
    echo -e "${YELLOW}要实际执行清理,请运行: ${GREEN}bash scripts/cleanup-project.sh${NC}"
else
    echo -e "${GREEN}✓ 项目清理完成!${NC}"
    echo ""
    echo -e "${YELLOW}建议:${NC}"
    echo -e "  1. 定期运行此脚本(建议每周一次)"
    echo -e "  2. 提交代码前运行: ${GREEN}bash scripts/cleanup-project.sh${NC}"
    echo -e "  3. 清理前可先预演: ${GREEN}bash scripts/cleanup-project.sh --dry-run${NC}"
    echo -e "  4. 检查 .gitignore 是否包含了正确的排除规则"
fi

echo ""
echo -e "${BLUE}项目大小统计:${NC}"
echo -e "  项目总大小: $(get_size .)"
echo -e "  data/ 大小: $(get_size data 2>/dev/null || echo 'N/A')"
echo -e "  logs/ 大小: $(get_size logs 2>/dev/null || echo 'N/A')"
echo ""
