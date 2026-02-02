"""测试知识库传递修复"""
import asyncio
import sys
sys.path.insert(0, '/data1/allresearchProject/Bright-Chat/backend-python')

from app.agents.agent_service import get_agent_service
from app.models.agent import Agent
from app.core.database import get_db

async def test():
    print("=" * 80)
    print("测试知识库传递")
    print("=" * 80)
    
    # 获取 agent service
    agent_service = get_agent_service()
    
    # 创建模拟的 agent 对象
    class MockAgent:
        def __init__(self):
            self.id = "test-agent-id"
            self.name = "test_agent"
            self.display_name = "测试 Agent"
            self.agent_type = "tool"
            self.tools = ["knowledge_search", "calculator"]
            self.knowledge_base_ids = []  # Agent 默认没有知识库
            self.config = {"max_steps": 5}
            self.llm_model_id = None
    
    agent = MockAgent()
    
    # 模拟前端传入运行时知识库 ID
    runtime_kb_ids = ["042240fe-1f48-4b3a-b8f6-5b85754837b7"]
    
    print(f"Agent 默认知识库 IDs: {agent.knowledge_base_ids}")
    print(f"运行时知识库 IDs: {runtime_kb_ids}")
    
    # 创建 workflow
    graph = await agent_service.create_agent_graph(
        agent=agent,
        user_id="test-user",
        session_id="test-session",
        runtime_knowledge_base_ids=runtime_kb_ids
    )
    
    print("\n✅ Workflow 创建成功")
    
    # 测试 agent_config
    effective_ids = runtime_kb_ids if runtime_kb_ids else agent.knowledge_base_ids
    agent_config = {
        "agent_id": agent.id,
        "tools": agent.tools,
        "knowledge_base_ids": effective_ids,
        "config": agent.config
    }
    
    print(f"\n📋 agent_config['knowledge_base_ids']: {agent_config['knowledge_base_ids']}")
    print(f"📋 长度: {len(agent_config['knowledge_base_ids'])}")
    print(f"📋 has_knowledge_base: {len(agent_config['knowledge_base_ids']) > 0}")

if __name__ == "__main__":
    asyncio.run(test())
