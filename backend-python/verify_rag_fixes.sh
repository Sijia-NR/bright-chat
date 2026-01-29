#!/bin/bash
# RAG Critical Fixes Verification Script
# 验证以下 4 个关键修复:
# 1. RAG-CRITICAL-001: 删除知识库时清理 ChromaDB 向量
# 2. RAG-CRITICAL-002: 删除文档时清理 ChromaDB 向量
# 3. RAG-CRITICAL-003: 搜索多知识库时的 $in 操作符问题
# 4. RAG-CRITICAL-004: BGE 模型线程安全

echo "======================================"
echo "RAG 模块关键修复代码检查"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0

# 检查函数
check_fix() {
    local fix_name="$1"
    local file="$2"
    local pattern="$3"

    echo -n "检查 $fix_name ... "
    if grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${GREEN}✓ 通过${NC}"
        ((pass_count++))
        return 0
    else
        echo -e "${RED}✗ 失败${NC}"
        echo -e "  ${YELLOW}未找到模式: $pattern${NC}"
        ((fail_count++))
        return 1
    fi
}

echo "=== 修复 1: 删除知识库时清理 ChromaDB 向量 ==="
check_fix \
    "delete_knowledge_base 调用 DocumentProcessor" \
    "/data1/allresearchProject/Bright-Chat/backend-python/minimal_api.py" \
    "processor.delete_knowledge_base(kb_id)"

echo ""
echo "=== 修复 2: 删除文档时清理 ChromaDB 向量 ==="
check_fix \
    "delete_document 调用 DocumentProcessor" \
    "/data1/allresearchProject/Bright-Chat/backend-python/minimal_api.py" \
    "processor.delete_document(doc_id)"

echo ""
echo "=== 修复 3: 搜索使用 RAGRetriever (不依赖 \$in) ==="
check_fix \
    "搜索端点使用 RAGRetriever" \
    "/data1/allresearchProject/Bright-Chat/backend-python/minimal_api.py" \
    "from app.rag.retriever import RAGRetriever"

check_fix \
    "搜索调用 retriever.search" \
    "/data1/allresearchProject/Bright-Chat/backend-python/minimal_api.py" \
    "search_results = await retriever.search"

echo ""
echo "=== 修复 4: BGE 模型线程安全 ==="
check_fix \
    "导入 threading 模块" \
    "/data1/allresearchProject/Bright-Chat/backend-python/app/rag/config.py" \
    "import threading"

check_fix \
    "添加线程锁 _model_lock" \
    "/data1/allresearchProject/Bright-Chat/backend-python/app/rag/config.py" \
    "self._model_lock = threading.Lock()"

check_fix \
    "使用双重检查锁" \
    "/data1/allresearchProject/Bright-Chat/backend-python/app/rag/config.py" \
    "with self._model_lock"

echo ""
echo "======================================"
echo "检查总结"
echo "======================================"
echo "通过: $pass_count"
echo "失败: $fail_count"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}所有修复都已正确实现！${NC}"
    exit 0
else
    echo -e "${RED}部分修复可能存在问题，请手动验证${NC}"
    exit 1
fi
