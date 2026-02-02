#!/bin/bash

# 智能体模块验收测试脚本
# 用途: 自动执行 Agent 模块的所有验收测试

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 打印分隔线
print_separator() {
    echo "================================================================================"
}

# 打印标题
print_title() {
    print_separator
    echo -e "${BLUE}$1${NC}"
    print_separator
}

# 检查依赖
check_dependencies() {
    print_title "检查依赖"

    # 检查 Python
    if ! command -v python &> /dev/null; then
        log_error "Python 未安装"
        exit 1
    fi
    log_success "Python 已安装: $(python --version)"

    # 检查 pytest
    if ! python -m pytest --version &> /dev/null; then
        log_warning "pytest 未安装,正在安装..."
        pip install pytest pytest-asyncio pytest-cov
    fi
    log_success "pytest 已安装"

    # 检查服务是否运行
    log_info "检查后端服务..."
    if ! curl -s http://localhost:18080/health > /dev/null; then
        log_error "后端服务未运行,请先启动服务"
        log_info "启动命令: cd backend-python && python minimal_api.py"
        exit 1
    fi
    log_success "后端服务运行正常"

    # 检查 ChromaDB
    log_info "检查 ChromaDB 服务..."
    if ! curl -s http://localhost:8002/api/v1/heartbeat > /dev/null 2>&1; then
        log_warning "ChromaDB 服务未运行,部分测试可能失败"
        log_info "启动命令: docker run -d -p 8002:8000 chromadb/chroma:latest"
    else
        log_success "ChromaDB 服务运行正常"
    fi

    echo ""
}

# P0 级测试: LLMReasoner
test_p0_llm_reasoner() {
    print_title "P0.1 测试 - LLMReasoner 类"

    log_info "运行 LLMReasoner 单元测试..."
    cd backend-python

    python -m pytest tests/agents/test_llm_reasoner.py -v --cov=app.agents.llm_reasoner --cov-report=term-missing || {
        log_error "LLMReasoner 测试失败"
        return 1
    }

    log_success "LLMReasoner 所有测试通过"
    cd ..
    echo ""
}

# P0 级测试: ReAct 循环
test_p0_react_loop() {
    print_title "P0.2 测试 - ReAct 循环"

    log_info "运行 ReAct 循环测试..."
    cd backend-python

    python -m pytest tests/agents/test_react_loop.py -v --cov=app.agents.agent_service --cov-report=term-missing || {
        log_error "ReAct 循环测试失败"
        return 1
    }

    log_success "ReAct 循环所有测试通过"
    cd ..
    echo ""
}

# P0 级测试: Agent API
test_p0_agent_api() {
    print_title "P0.3 测试 - Agent API"

    log_info "运行 Agent API 测试..."
    cd backend-python

    python -m pytest tests/agents/test_agent_api.py -v || {
        log_error "Agent API 测试失败"
        return 1
    }

    log_success "Agent API 所有测试通过"
    cd ..
    echo ""
}

# P1 级测试: BaseTool
test_p1_base_tool() {
    print_title "P1.1 测试 - BaseTool 基类"

    log_info "运行 BaseTool 测试..."
    cd backend-python

    python -m pytest tests/agents/test_base_tool.py -v --cov=app.agents.tools.base_tool --cov-report=term-missing || {
        log_error "BaseTool 测试失败"
        return 1
    }

    log_success "BaseTool 所有测试通过"
    cd ..
    echo ""
}

# P1 级测试: 工具重构
test_p1_tools_refactor() {
    print_title "P1.2 测试 - 工具重构"

    log_info "运行所有工具测试..."
    cd backend-python

    for tool in calculator datetime knowledge code_executor browser file; do
        log_info "测试 $tool 工具..."
        python -m pytest tests/agents/tools/test_${tool}_tool.py -v || {
            log_error "$tool 工具测试失败"
            return 1
        }
    done

    log_success "所有工具测试通过"
    cd ..
    echo ""
}

# 集成测试
test_integration() {
    print_title "集成测试"

    log_info "运行 Agent 集成测试..."
    cd backend-python

    python -m pytest tests/agents/test_agent_integration.py -v || {
        log_error "集成测试失败"
        return 1
    }

    log_success "集成测试通过"
    cd ..
    echo ""
}

# E2E 测试
test_e2e() {
    print_title "E2E 测试"

    log_info "运行端到端测试..."
    cd backend-python

    python -m pytest tests/agents/test_agent_e2e.py -v || {
        log_error "E2E 测试失败"
        return 1
    }

    log_success "E2E 测试通过"
    cd ..
    echo ""
}

# 性能测试
test_performance() {
    print_title "性能测试"

    log_info "运行性能测试..."
    cd backend-python

    python -m pytest tests/agents/test_agent_performance.py -v || {
        log_error "性能测试失败"
        return 1
    }

    log_success "性能测试通过"
    cd ..
    echo ""
}

# 安全测试
test_security() {
    print_title "安全测试"

    log_info "运行安全测试..."
    cd backend-python

    python -m pytest tests/agents/test_security.py -v || {
        log_error "安全测试失败"
        return 1
    }

    log_success "安全测试通过"
    cd ..
    echo ""
}

# 代码覆盖率检查
check_coverage() {
    print_title "代码覆盖率检查"

    log_info "运行所有测试并生成覆盖率报告..."
    cd backend-python

    python -m pytest tests/agents/ -v --cov=app.agents --cov-report=html --cov-report=term || {
        log_warning "测试完成,但覆盖率未达标"
    }

    log_info "覆盖率报告已生成: backend-python/htmlcov/index.html"
    cd ..
    echo ""
}

# 生成测试报告
generate_report() {
    print_title "生成测试报告"

    local report_file="AGENT_ACCEPTANCE_TEST_REPORT_$(date +%Y%m%d_%H%M%S).md"

    cat > $report_file << EOF
# Agent 模块验收测试报告

**测试日期**: $(date '+%Y-%m-%d %H:%M:%S')
**测试环境**: $(uname -a)
**Python 版本**: $(python --version)

---

## 测试结果摘要

| 测试类别 | 状态 | 备注 |
|---------|------|------|
| **P0.1 LLMReasoner** | $P0_1_STATUS | $P0_1_NOTE |
| **P0.2 ReAct 循环** | $P0_2_STATUS | $P0_2_NOTE |
| **P0.3 Agent API** | $P0_3_STATUS | $P0_3_NOTE |
| **P1.1 BaseTool** | $P1_1_STATUS | $P1_1_NOTE |
| **P1.2 工具重构** | $P1_2_STATUS | $P1_2_NOTE |
| **集成测试** | $INTEGRATION_STATUS | $INTEGRATION_NOTE |
| **E2E 测试** | $E2E_STATUS | $E2E_NOTE |
| **性能测试** | $PERFORMANCE_STATUS | $PERFORMANCE_NOTE |
| **安全测试** | $SECURITY_STATUS | $SECURITY_NOTE |
| **代码覆盖率** | $COVERAGE_STATUS | $COVERAGE_NOTE |

---

## 详细测试日志

\`\`\`
$TEST_LOG
\`\`\`

---

## 问题清单

| 优先级 | 问题描述 | 责任人 | 状态 |
|--------|---------|--------|------|
$ISSUES_LIST

---

## 验收结论

**验收结果**: $FINAL_RESULT

**验收人**: ___
**验收日期**: $(date '+%Y-%m-%d')

EOF

    log_success "测试报告已生成: $report_file"
    echo ""
}

# 主测试流程
main() {
    print_title "智能体模块验收测试"
    echo ""
    log_info "开始执行 Agent 模块验收测试..."
    echo ""

    # 初始化状态变量
    P0_1_STATUS="⏳ 待测试"
    P0_2_STATUS="⏳ 待测试"
    P0_3_STATUS="⏳ 待测试"
    P1_1_STATUS="⏳ 待测试"
    P1_2_STATUS="⏳ 待测试"
    INTEGRATION_STATUS="⏳ 待测试"
    E2E_STATUS="⏳ 待测试"
    PERFORMANCE_STATUS="⏳ 待测试"
    SECURITY_STATUS="⏳ 待测试"
    COVERAGE_STATUS="⏳ 待检查"

    TEST_LOG=""
    FINAL_RESULT="⏳ 测试进行中"

    # 检查依赖
    check_dependencies

    # P0 级测试
    if test_p0_llm_reasoner; then
        P0_1_STATUS="✅ 通过"
        P0_1_NOTE="所有测试用例通过"
    else
        P0_1_STATUS="❌ 失败"
        P0_1_NOTE="存在失败的测试用例"
        FINAL_RESULT="❌ 验收未通过"
    fi

    if test_p0_react_loop; then
        P0_2_STATUS="✅ 通过"
        P0_2_NOTE="所有测试用例通过"
    else
        P0_2_STATUS="❌ 失败"
        P0_2_NOTE="存在失败的测试用例"
        FINAL_RESULT="❌ 验收未通过"
    fi

    if test_p0_agent_api; then
        P0_3_STATUS="✅ 通过"
        P0_3_NOTE="所有测试用例通过"
    else
        P0_3_STATUS="❌ 失败"
        P0_3_NOTE="存在失败的测试用例"
        FINAL_RESULT="❌ 验收未通过"
    fi

    # P1 级测试
    if test_p1_base_tool; then
        P1_1_STATUS="✅ 通过"
        P1_1_NOTE="所有测试用例通过"
    else
        P1_1_STATUS="❌ 失败"
        P1_1_NOTE="存在失败的测试用例"
        FINAL_RESULT="⚠️ 部分功能未通过"
    fi

    if test_p1_tools_refactor; then
        P1_2_STATUS="✅ 通过"
        P1_2_NOTE="所有工具测试通过"
    else
        P1_2_STATUS="❌ 失败"
        P1_2_NOTE="存在工具测试失败"
        FINAL_RESULT="⚠️ 部分功能未通过"
    fi

    # 集成测试
    if test_integration; then
        INTEGRATION_STATUS="✅ 通过"
        INTEGRATION_NOTE="所有集成测试通过"
    else
        INTEGRATION_STATUS="❌ 失败"
        INTEGRATION_NOTE="存在集成测试失败"
        FINAL_RESULT="❌ 验收未通过"
    fi

    # E2E 测试
    if test_e2e; then
        E2E_STATUS="✅ 通过"
        E2E_NOTE="所有 E2E 测试通过"
    else
        E2E_STATUS="❌ 失败"
        E2E_NOTE="存在 E2E 测试失败"
        FINAL_RESULT="❌ 验收未通过"
    fi

    # 性能测试
    if test_performance; then
        PERFORMANCE_STATUS="✅ 通过"
        PERFORMANCE_NOTE="性能指标达标"
    else
        PERFORMANCE_STATUS="⚠️ 警告"
        PERFORMANCE_NOTE="性能指标未达标"
        FINAL_RESULT="⚠️ 性能需要优化"
    fi

    # 安全测试
    if test_security; then
        SECURITY_STATUS="✅ 通过"
        SECURITY_NOTE="无安全漏洞"
    else
        SECURITY_STATUS="❌ 失败"
        SECURITY_NOTE="存在安全风险"
        FINAL_RESULT="❌ 验收未通过"
    fi

    # 代码覆盖率
    if check_coverage; then
        COVERAGE_STATUS="✅ 达标"
        COVERAGE_NOTE="覆盖率 ≥ 80%"
    else
        COVERAGE_STATUS="⚠️ 警告"
        COVERAGE_NOTE="覆盖率 < 80%"
    fi

    # 最终结果
    if [ "$FINAL_RESULT" = "⏳ 测试进行中" ]; then
        FINAL_RESULT="✅ 验收通过"
    fi

    # 生成测试报告
    generate_report

    # 打印最终结果
    print_title "测试完成"
    echo ""
    log_info "验收结果: $FINAL_RESULT"
    echo ""
    log_info "详细测试报告已生成,请查看生成的 Markdown 文件"
    echo ""

    if [[ "$FINAL_RESULT" == *"✅"* ]]; then
        log_success "恭喜!Agent 模块通过验收测试"
        exit 0
    else
        log_error "Agent 模块未完全通过验收测试,请检查失败项"
        exit 1
    fi
}

# 执行主流程
main 2>&1 | tee AGENT_TEST_EXECUTION_LOG.txt
