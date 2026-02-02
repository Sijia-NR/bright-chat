#!/usr/bin/env python3
"""测试规则引擎"""

import re

def test_apply_rules(question, available_tools, has_knowledge_base):
    """测试规则引擎逻辑"""
    print(f"问题: {question}")
    print(f"可用工具: {available_tools}")
    print(f"有知识库: {has_knowledge_base}")

    # 规则 2: 代码执行（最高优先级）
    if any(keyword in question for keyword in ["使用代码", "执行代码", "用代码", "代码执行", "python代码", "运行代码"]):
        if "code_executor" in available_tools:
            print("✅ 匹配规则 2: 代码执行关键词")
            # 提取表达式
            expr_match = re.search(r'(\d+(?:\s*[\*\+\-\/]\s*\d+)+)', question)
            if expr_match:
                expression = expr_match.group(1)
                code = f"print({expression})"
            else:
                code = question
            return {
                "reasoning": "用户明确要求使用代码执行",
                "tool": "code_executor",
                "parameters": {"code": code},
                "confidence": 0.98,
                "should_continue": False
            }

    print("❌ 无匹配规则")
    return None

# 测试
result = test_apply_rules(
    "使用代码帮我计算909090*787978等于多少",
    ["code_executor", "calculator", "datetime"],
    False
)

print(f"\n结果: {result}")
