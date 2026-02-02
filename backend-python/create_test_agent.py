#!/usr/bin/env python3
"""创建测试 Agent（包含所有工具）"""

import requests
import json

BASE_URL = "http://localhost:8080/api/v1"

# 1. 登录
resp = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "pwd123"})
token = resp.json()["token"]

# 2. 创建测试 Agent
agent_data = {
    "name": "test_all_tools",
    "display_name": "全工具测试",
    "description": "用于测试所有工具的 Agent",
    "agent_type": "tool",
    "system_prompt": "你是一个测试 Agent，可以使用各种工具来回答用户问题。",
    "knowledge_base_ids": [],
    "tools": ["code_executor", "calculator", "datetime", "knowledge_search", "browser", "file"],
    "config": {
        "temperature": 0.7,
        "max_steps": 10,
        "timeout": 300
    },
    "enable_knowledge": True,
    "is_active": True
}

print("创建测试 Agent...")
resp = requests.post(
    f"{BASE_URL}/agents/",
    headers={"Authorization": f"Bearer {token}"},
    json=agent_data
)

if resp.status_code == 200:
    agent = resp.json()
    print(f"✅ Agent 创建成功:")
    print(f"  ID: {agent.get('id')}")
    print(f"  名称: {agent.get('display_name')}")
    print(f"  工具: {agent.get('tools', [])}")
    print(f"\n你可以使用这个 Agent ID 进行测试: {agent.get('id')}")
else:
    print(f"❌ 创建失败: {resp.status_code}")
    print(resp.text)
