#!/usr/bin/env python3
"""
全面的 LLM Reasoner 测试套件

测试场景：
1. 用户明确要求使用工具（代码执行、搜索等）
2. 隐含的工具使用需求（计算、时间等）
3. 不应该使用工具的场景（问候、闲聊）
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agents.llm_reasoner import LLMReasoner


async def run_test(name, question, available_tools, expected_tool, agent_config=None):
    """运行单个测试"""
    if agent_config is None:
        agent_config = {"knowledge_base_ids": []}

    print(f"\n📝 测试: {name}")
    print(f"   问题: {question}")
    print(f"   可用工具: {available_tools}")

    reasoner = LLMReasoner()
    reasoner._model_config = None  # 强制使用规则引擎

    decision = await reasoner.reason(
        question=question,
        available_tools=available_tools,
        conversation_history=[],
        previous_steps=[],
        agent_config=agent_config
    )

    actual_tool = decision.get('tool')
    confidence = decision.get('confidence', 0)

    print(f"   期望工具: {expected_tool}")
    print(f"   实际工具: {actual_tool}")
    print(f"   置信度: {confidence:.2f}")

    if actual_tool == expected_tool:
        print(f"   ✅ PASS")
        return True
    else:
        print(f"   ❌ FAIL")
        return False


async def main():
    """运行所有测试"""
    print("=" * 80)
    print("🧪 LLM Reasoner 全面测试套件")
    print("=" * 80)

    results = []

    # ===== 代码执行类测试 =====
    print("\n" + "=" * 80)
    print("📂 类别 1: 代码执行（高优先级）")
    print("=" * 80)

    results.append(await run_test(
        "明确要求使用代码计算",
        "能不能使用代码帮我计算909090*787978等于多少",
        ["code_executor", "calculator"],
        "code_executor"
    ))

    results.append(await run_test(
        "执行代码计算",
        "执行代码计算 100 * 200",
        ["code_executor", "calculator"],
        "code_executor"
    ))

    results.append(await run_test(
        "用代码执行",
        "用代码算一下 50 * 60",
        ["code_executor", "calculator"],
        "code_executor"
    ))

    # ===== 计算类测试 =====
    print("\n" + "=" * 80)
    print("📂 类别 2: 数学计算")
    print("=" * 80)

    results.append(await run_test(
        "简单计算",
        "帮我计算 123 * 456",
        ["calculator"],
        "calculator"
    ))

    results.append(await run_test(
        "加法计算",
        "100 加 200 等于多少",
        ["calculator"],
        "calculator"
    ))

    results.append(await run_test(
        "复杂表达式",
        "计算 (100 + 200) * 3",
        ["calculator"],
        "calculator"
    ))

    # ===== 时间日期类测试 =====
    print("\n" + "=" * 80)
    print("📂 类别 3: 时间日期")
    print("=" * 80)

    results.append(await run_test(
        "询问时间",
        "现在几点了？",
        ["datetime"],
        "datetime"
    ))

    results.append(await run_test(
        "询问日期",
        "今天是什么日期？",
        ["datetime"],
        "datetime"
    ))

    results.append(await run_test(
        "当前时间",
        "告诉我现在的时间",
        ["datetime"],
        "datetime"
    ))

    # ===== 搜索类测试 =====
    print("\n" + "=" * 80)
    print("📂 类别 4: 知识搜索")
    print("=" * 80)

    results.append(await run_test(
        "知识搜索",
        "搜索 Python 教程",
        ["knowledge_search", "browser"],
        "knowledge_search"
    ))

    results.append(await run_test(
        "查找信息",
        "查找 AI 的发展历史",
        ["knowledge_search"],
        "knowledge_search"
    ))

    # ===== 问候类测试 =====
    print("\n" + "=" * 80)
    print("📂 类别 5: 问候和闲聊（不使用工具）")
    print("=" * 80)

    results.append(await run_test(
        "打招呼",
        "你好",
        ["calculator", "datetime", "code_executor"],
        None
    ))

    results.append(await run_test(
        "问候",
        "你好，最近怎么样？",
        ["calculator", "datetime"],
        None
    ))

    results.append(await run_test(
        "打招呼2",
        "嗨，在吗？",
        ["calculator", "datetime"],
        None
    ))

    results.append(await run_test(
        "闲聊",
        "最近过得怎么样？",
        ["calculator", "datetime"],
        None
    ))

    # ===== 知识库选择测试 =====
    print("\n" + "=" * 80)
    print("📂 类别 6: 知识库优先级")
    print("=" * 80)

    results.append(await run_test(
        "有知识库时的搜索",
        "什么是 AI？",
        ["knowledge_search", "calculator", "datetime"],
        "knowledge_search",
        agent_config={"knowledge_base_ids": ["kb-123"]}
    ))

    # ===== 边界情况测试 =====
    print("\n" + "=" * 80)
    print("📂 类别 7: 边界情况")
    print("=" * 80)

    results.append(await run_test(
        "空问题",
        "",
        ["calculator"],
        None
    ))

    results.append(await run_test(
        "模糊问题",
        "嗯...",
        ["calculator", "datetime"],
        None
    ))

    # ===== 汇总结果 =====
    print("\n" + "=" * 80)
    print("📋 测试结果汇总")
    print("=" * 80)

    passed = sum(results)
    total = len(results)

    print(f"\n总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"通过率: {(passed / total * 100):.1f}%")

    if passed == total:
        print("\n✅ 所有测试通过！LLM Reasoner 工作正常")
        return 0
    else:
        print(f"\n❌ 有 {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
