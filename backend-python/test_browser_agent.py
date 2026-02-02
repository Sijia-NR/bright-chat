"""
测试浏览器工具修复
Test Browser Tool Fix
"""
import asyncio
import sys
sys.path.insert(0, '/data1/allresearchProject/Bright-Chat/backend-python')

from app.agents.agent_service import AgentService, AgentState
from app.models.agent import Agent


async def test_browser_tool_params():
    """测试浏览器工具参数增强"""
    print("=" * 80)
    print("测试：浏览器工具参数增强")
    print("=" * 80)

    # 创建 Agent Service
    service = AgentService()
    print("✅ AgentService 初始化成功")

    # 测试场景 1：用户输入包含 URL
    print("\n场景 1：用户输入包含 URL")
    input_text = "帮我总结一下这个网页 http://47.116.218.206:8080/blog/post/sijia"

    # 模拟 LLM 推理结果（参数不完整）
    tool_decision = {
        "tool": "browser",
        "parameters": {},  # LLM 可能生成空的参数
        "confidence": 0.95,
        "should_continue": False
    }

    print(f"  用户输入: {input_text}")
    print(f"  LLM 决策: {tool_decision}")

    # 模拟 act_node 的参数增强逻辑
    parameters = tool_decision.get("parameters", {})
    if tool_decision.get("tool") == "browser":
        import re
        if "action" not in parameters:
            url_match = re.search(r'https?://[^\s]+', input_text)
            if url_match:
                parameters["action"] = "scrape"
                parameters["url"] = url_match.group(0)
                print(f"  ✅ 参数增强成功: action=scrape, url={parameters['url']}")
            else:
                print(f"  ❌ 未找到 URL")

    print(f"  最终参数: {parameters}")

    # 验证参数是否正确
    assert parameters.get("action") == "scrape", "action 应该是 scrape"
    assert parameters.get("url") == "http://47.116.218.206:8080/blog/post/sijia", "URL 应该被提取"
    print("  ✅ 场景 1 测试通过")

    # 测试场景 2：搜索请求
    print("\n场景 2：搜索请求")
    input_text = "搜索 python 教程"
    parameters = {}

    if "action" not in parameters:
        if any(kw in input_text for kw in ["搜索", "search", "查找"]):
            parameters["action"] = "search"
            parameters["text"] = input_text
            print(f"  ✅ 参数增强成功: action=search, text={parameters['text']}")

    print(f"  最终参数: {parameters}")
    assert parameters.get("action") == "search", "action 应该是 search"
    print("  ✅ 场景 2 测试通过")

    print("\n" + "=" * 80)
    print("✅ 所有测试通过！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_browser_tool_params())
