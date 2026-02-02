#!/usr/bin/env python3
"""
测试 LLM Reasoner Bug - 用户明确要求使用工具但未被识别

Bug 现象：
- 用户问："能不能使用代码帮我计算909090*787978等于多少"
- 预期：使用 code_executor 工具执行计算
- 实际：返回文字说明，未使用任何工具

根本原因：
1. 提示词没有强调"必须使用工具"的原则
2. 规则引擎没有处理"使用代码"这类明确指令
3. 工具选择置信度过低，导致选择 none
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agents.llm_reasoner import LLMReasoner


async def test_code_execution_request():
    """测试用户明确要求使用代码执行"""
    print("=" * 80)
    print("测试案例: 用户明确要求使用代码执行计算")
    print("=" * 80)

    reasoner = LLMReasoner()
    # 使用模拟的模型配置（触发规则引擎）
    reasoner._model_config = None

    question = "能不能使用代码帮我计算909090*787978等于多少"
    available_tools = ["code_executor", "calculator", "datetime"]
    agent_config = {"knowledge_base_ids": []}

    print(f"\n📝 用户问题: {question}")
    print(f"🔧 可用工具: {available_tools}")

    # 执行推理
    decision = await reasoner.reason(
        question=question,
        available_tools=available_tools,
        conversation_history=[],
        previous_steps=[],
        agent_config=agent_config
    )

    print(f"\n📊 推理结果:")
    print(f"  - 推理链: {decision.get('reasoning', 'N/A')[:100]}...")
    print(f"  - 选择的工具: {decision.get('tool', 'N/A')}")
    print(f"  - 工具参数: {decision.get('parameters', {})}")
    print(f"  - 置信度: {decision.get('confidence', 0)}")
    print(f"  - 继续执行: {decision.get('should_continue', False)}")

    # 验证结果
    print(f"\n✅ 测试验证:")
    expected_tool = "code_executor"
    actual_tool = decision.get('tool')

    if actual_tool == expected_tool:
        print(f"  ✅ PASS: 正确识别工具 {expected_tool}")
        return True
    else:
        print(f"  ❌ FAIL: 期望工具 '{expected_tool}'，实际工具 '{actual_tool}'")
        print(f"  💡 建议: 规则引擎需要增加 '使用代码' 关键词检测")
        return False


async def test_simple_calculation():
    """测试简单计算请求"""
    print("\n" + "=" * 80)
    print("测试案例: 简单计算请求（应该使用 calculator）")
    print("=" * 80)

    reasoner = LLMReasoner()
    reasoner._model_config = None

    question = "帮我计算 123 * 456"
    available_tools = ["calculator", "code_executor"]
    agent_config = {"knowledge_base_ids": []}

    print(f"\n📝 用户问题: {question}")
    print(f"🔧 可用工具: {available_tools}")

    decision = await reasoner.reason(
        question=question,
        available_tools=available_tools,
        conversation_history=[],
        previous_steps=[],
        agent_config=agent_config
    )

    print(f"\n📊 推理结果:")
    print(f"  - 选择的工具: {decision.get('tool', 'N/A')}")
    print(f"  - 置信度: {decision.get('confidence', 0)}")

    expected_tool = "calculator"
    actual_tool = decision.get('tool')

    if actual_tool == expected_tool:
        print(f"  ✅ PASS: 正确识别工具 {expected_tool}")
        return True
    else:
        print(f"  ❌ FAIL: 期望工具 '{expected_tool}'，实际工具 '{actual_tool}'")
        return False


async def test_greeting():
    """测试问候（不应该使用工具）"""
    print("\n" + "=" * 80)
    print("测试案例: 问候（不应该使用工具）")
    print("=" * 80)

    reasoner = LLMReasoner()
    reasoner._model_config = None

    question = "你好，最近怎么样？"
    available_tools = ["calculator", "datetime", "code_executor"]
    agent_config = {"knowledge_base_ids": []}

    print(f"\n📝 用户问题: {question}")

    decision = await reasoner.reason(
        question=question,
        available_tools=available_tools,
        conversation_history=[],
        previous_steps=[],
        agent_config=agent_config
    )

    print(f"\n📊 推理结果:")
    print(f"  - 选择的工具: {decision.get('tool', 'N/A')}")
    print(f"  - 置信度: {decision.get('confidence', 0)}")

    actual_tool = decision.get('tool')

    if actual_tool is None:
        print(f"  ✅ PASS: 问候不需要使用工具")
        return True
    else:
        print(f"  ❌ FAIL: 问候不应该使用工具 '{actual_tool}'")
        return False


async def main():
    """运行所有测试"""
    print("🧪 LLM Reasoner Bug 复现测试\n")

    results = []

    # 测试 1: 代码执行请求
    results.append(await test_code_execution_request())

    # 测试 2: 简单计算
    results.append(await test_simple_calculation())

    # 测试 3: 问候
    results.append(await test_greeting())

    # 汇总结果
    print("\n" + "=" * 80)
    print("📋 测试结果汇总")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("✅ 所有测试通过")
        return 0
    else:
        print("❌ 存在失败的测试")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
