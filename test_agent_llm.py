#!/usr/bin/env python3
"""测试 Agent LLM 推理"""

import requests
import json

BASE_URL = "http://localhost:8080/api/v1"

# 1. 登录获取 token
print("1. 登录...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "admin", "password": "pwd123"}
)
token = login_response.json()["token"]
print(f"✅ 登录成功，token: {token[:50]}...")

# 2. 测试 Agent 聊天
print("\n2. 测试 Agent 聊天...")
chat_response = requests.post(
    f"{BASE_URL}/agents/3a3cefd6-df31-4da0-aa49-1525fd5e642f/chat",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "query": "什么是大模型？",
        "knowledge_base_ids": ["042240fe-1f48-4b3a-b8f6-5b85754837b7"]
    },
    stream=True
)

print(f"状态码: {chat_response.status_code}")
if chat_response.status_code == 200:
    print(f"✅ Agent 聊天成功（流式响应）")
    print("\n接收流式数据:")
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
                    print(f"  事件类型: {event_type}")
                    if event_type == 'complete':
                        print(f"  执行ID: {event.get('execution_id')}")
                        print(f"  步骤数: {event.get('steps')}")
                        print(f"  工具调用: {event.get('tools_called_count')}")
                        print(f"  输出预览: {event.get('output', '')[:200]}...")
                except json.JSONDecodeError:
                    pass
else:
    print(f"❌ 错误: {chat_response.text}")
