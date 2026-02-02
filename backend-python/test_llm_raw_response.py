#!/usr/bin/env python3
"""直接测试 LLM 推理器的原始响应"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agents.llm_reasoner import LLMReasoner


async def test_raw_response():
    """测试原始 LLM 响应"""
    reasoner = LLMReasoner()

    # 初始化（从数据库加载配置）
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.database import DATABASE_URL

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    await reasoner.initialize(db)

    question = "使用代码帮我计算909090*787978等于多少"
    available_tools = ["code_executor", "calculator", "datetime"]
    agent_config = {"knowledge_base_ids": []}

    print("=" * 80)
    print("直接测试 LLM 响应")
    print("=" * 80)
    print(f"问题: {question}")
    print(f"可用工具: {available_tools}")
    print()

    # 调用 reason 方法
    decision = await reasoner.reason(
        question=question,
        available_tools=available_tools,
        conversation_history=[],
        previous_steps=[],
        agent_config=agent_config
    )

    print("=" * 80)
    print("决策结果:")
    print("=" * 80)
    print(f"推理: {decision.get('reasoning', 'N/A')}")
    print(f"工具: {decision.get('tool', 'N/A')}")
    print(f"参数: {decision.get('parameters', {})}")
    print(f"置信度: {decision.get('confidence', 0)}")
    print(f"继续执行: {decision.get('should_continue', False)}")

    db.close()


if __name__ == "__main__":
    asyncio.run(test_raw_response())
