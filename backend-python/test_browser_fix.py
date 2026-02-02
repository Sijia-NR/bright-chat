"""
测试浏览器工具完整流程
"""
import asyncio
import sys
sys.path.insert(0, '/data1/allresearchProject/Bright-Chat/backend-python')

from app.agents.llm_reasoner import LLMReasoner


async def test_json_parsing():
    """测试 JSON 解析"""
    print("=" * 80)
    print("测试：LLM 响应的 JSON 解析")
    print("=" * 80)

    reasoner = LLMReasoner()

    # 模拟 LLM 的响应（包含 ```json 代码块）
    llm_response = '''```json
{
  "reasoning": "用户要求总结网页内容，需要使用browser工具抓取页面",
  "tool": "browser",
  "parameters": {
    "action": "scrape",
    "url": "http://47.116.218.206:8080/blog/post/sijia/%E5%A4%A7%E6%A8%A1%E5%9E%8B%E6%8E%A5%E5%85%A5%E6%96%B9%E5%BC%8F"
  },
  "confidence": 0.95,
  "should_continue": false
}
```'''

    available_tools = ['code_executor', 'calculator', 'datetime', 'knowledge_search', 'browser', 'file']

    print(f"\nLLM 响应:\n{llm_response[:200]}...")
    print(f"\n可用工具: {available_tools}")

    # 解析决策
    decision = reasoner._parse_decision(llm_response, available_tools)

    print(f"\n✅ 解析结果:")
    print(f"  - reasoning: {decision['reasoning'][:100]}...")
    print(f"  - tool: {decision['tool']}")
    print(f"  - parameters: {decision['parameters']}")
    print(f"  - confidence: {decision['confidence']}")
    print(f"  - should_continue: {decision['should_continue']}")

    # 验证解析结果
    assert decision['tool'] == 'browser', f"工具应该是 browser，实际是 {decision['tool']}"
    assert decision['parameters']['action'] == 'scrape', f"action 应该是 scrape"
    assert 'url' in decision['parameters'], f"应该包含 url 参数"
    assert decision['confidence'] == 0.95, f"置信度应该是 0.95"

    print("\n" + "=" * 80)
    print("✅ JSON 解析测试通过！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_json_parsing())
