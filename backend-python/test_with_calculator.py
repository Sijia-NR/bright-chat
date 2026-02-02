#!/usr/bin/env python3
"""测试规则引擎 - 使用有 calculator 工具的 Agent"""

import requests
import json

BASE_URL = "http://localhost:8080/api/v1"

# 1. 登录
print("=" * 80)
print("1. 登录系统...")
print("=" * 80)

login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "admin", "password": "pwd123"}
)

token = login_response.json()["token"]
print(f"✅ 登录成功")

# 2. 获取 Agent 列表，找到有 code_executor 或 calculator 的 Agent
print("\n" + "=" * 80)
print("2. 查找合适的 Agent...")
print("=" * 80)

agents_response = requests.get(
    f"{BASE_URL}/agents/",
    headers={"Authorization": f"Bearer {token}"}
)

agents = agents_response.json().get("agents", [])

# 查找有 code_executor 或 calculator 的 Agent
test_agent = None
for agent in agents:
    tools = agent.get("tools", [])
    if "code_executor" in tools:
        print(f"✅ 找到有 code_executor 的 Agent: {agent.get('display_name')}")
        test_agent = agent
        break
    elif "calculator" in tools and not test_agent:
        print(f"⚠️  找到有 calculator 的 Agent: {agent.get('display_name')}")
        test_agent = agent

if not test_agent:
    print("❌ 没有找到合适的 Agent")
    exit(1)

print(f"\n选择的 Agent:")
print(f"  名称: {test_agent.get('display_name')}")
print(f"  ID: {test_agent.get('id')}")
print(f"  工具: {test_agent.get('tools', [])}")

agent_id = test_agent.get('id')

# 3. 测试计算查询
print("\n" + "=" * 80)
print("3. 测试: 帮我计算 123 * 456")
print("=" * 80)

chat_response = requests.post(
    f"{BASE_URL}/agents/{agent_id}/chat",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "query": "帮我计算 123 * 456",
        "stream": True
    },
    stream=True
)

if chat_response.status_code != 200:
    print(f"❌ 请求失败: {chat_response.status_code}")
    exit(1)

print("✅ 请求成功，接收流式响应...\n")

tools_used = []
final_output = ""

for line in chat_response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = line[6:]
            if data == '[DONE]':
                print("\n✅ 流式响应完成")
                break
            try:
                event = json.loads(data)
                event_type = event.get('type', 'unknown')

                if event_type == 'reasoning':
                    tool_decision = event.get('tool_decision', {})
                    selected_tool = tool_decision.get('tool', 'none')
                    print(f"🧠 决策工具: {selected_tool}")

                    if selected_tool in ['calculator', 'code_executor']:
                        print(f"  ✅ 正确使用了计算工具")
                    elif selected_tool == 'none':
                        print(f"  ❌ 未使用工具")

                elif event_type == 'tool_call':
                    tool = event.get('tool', '')
                    print(f"🔨 调用工具: {tool}")
                    tools_used.append(tool)

                elif event_type == 'complete':
                    final_output = event.get('output', '')
                    steps = event.get('steps', 0)
                    tools_count = event.get('tools_called_count', 0)

                    print(f"\n📊 执行完成:")
                    print(f"  - 总步骤数: {steps}")
                    print(f"  - 工具调用次数: {tools_count}")
                    print(f"  - 最终输出: {final_output[:200]}...")

            except json.JSONDecodeError:
                pass

# 验证结果
print("\n" + "=" * 80)
print("4. 结果验证")
print("=" * 80)

if tools_used:
    print(f"✅ PASS: 使用了工具 {tools_used}")
    if '56088' in final_output or '56088.0' in final_output:
        print("✅ PASS: 计算结果正确 (56088)")
    else:
        print(f"⚠️  WARNING: 计算结果可能不正确")
else:
    print("❌ FAIL: 未使用任何工具")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
