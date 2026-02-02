#!/usr/bin/env python3
"""
测试纯 LLM 推理方案

验证优化后的提示词是否能正确识别工具使用需求
"""

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

if login_response.status_code != 200:
    print(f"❌ 登录失败: {login_response.status_code}")
    exit(1)

token = login_response.json()["token"]
print(f"✅ 登录成功")

# 2. 测试 Agent 聊天 - 使用代码计算
print("\n" + "=" * 80)
print("2. 测试: 使用代码帮我计算909090*787978等于多少")
print("=" * 80)

agent_id = "3a3cefd6-df31-4da0-aa49-1525fd5e642f"  # klSearch Agent

chat_response = requests.post(
    f"{BASE_URL}/agents/{agent_id}/chat",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "query": "使用代码帮我计算909090*787978等于多少",
        "stream": True
    },
    stream=True
)

print(f"状态码: {chat_response.status_code}")

if chat_response.status_code == 200:
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

                    # 显示关键事件
                    if event_type == 'start':
                        print(f"📌 开始执行 (ID: {event.get('execution_id')})")

                    elif event_type == 'reasoning':
                        reasoning = event.get('reasoning', '')[:100]
                        tool_decision = event.get('tool_decision', {})
                        selected_tool = tool_decision.get('tool', 'none')
                        print(f"🧠 推理: {reasoning}...")
                        print(f"🔧 决策工具: {selected_tool}")

                        if selected_tool == 'code_executor':
                            print("  ✅ 正确识别: code_executor")
                        elif selected_tool == 'none':
                            print("  ❌ 错误: 未使用工具")
                        else:
                            print(f"  ⚠️  使用了其他工具: {selected_tool}")

                    elif event_type == 'step':
                        node = event.get('node', '')
                        print(f"📍 节点: {node}")

                    elif event_type == 'tool_call':
                        tool = event.get('tool', '')
                        print(f"🔨 调用工具: {tool}")
                        tools_used.append(tool)

                    elif event_type == 'complete':
                        final_output = event.get('output', '')
                        steps = event.get('steps', 0)
                        tools_count = event.get('tools_called_count', 0)
                        duration = event.get('duration', 0)

                        print(f"\n📊 执行完成:")
                        print(f"  - 总步骤数: {steps}")
                        print(f"  - 工具调用次数: {tools_count}")
                        print(f"  - 执行时长: {duration:.2f}秒")
                        print(f"  - 最终输出: {final_output[:200]}...")

                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON 解析失败: {e}")

    # 验证结果
    print("\n" + "=" * 80)
    print("3. 结果验证")
    print("=" * 80)

    if 'code_executor' in tools_used:
        print("✅ PASS: 成功使用 code_executor 工具")
        if '716270774220' in final_output or '716,270,774,220' in final_output:
            print("✅ PASS: 计算结果正确 (716,270,774,220)")
        else:
            print(f"⚠️  WARNING: 计算结果可能不正确")
    else:
        print("❌ FAIL: 未使用 code_executor 工具")
        if tools_used:
            print(f"   实际使用的工具: {tools_used}")
        else:
            print("   没有调用任何工具")

else:
    print(f"❌ 请求失败: {chat_response.status_code}")
    print(f"响应: {chat_response.text[:500]}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
