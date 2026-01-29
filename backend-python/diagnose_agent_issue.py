#!/usr/bin/env python3
"""
诊断 Agent 问题
1. 检查前后端工具列表不一致
2. 验证上线/下线按钮实际行为
"""
import requests
import json

BASE_URL = "http://localhost:9003/api/v1"
USERNAME = "admin"
PASSWORD = "pwd123"

print("=" * 80)
print("Agent 问题诊断")
print("=" * 80)

# 1. 登录
print("\n步骤1: 登录")
resp = requests.post(f"{BASE_URL}/auth/login", json={
    "username": USERNAME,
    "password": PASSWORD
})
token = resp.json()["token"]
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
print("✓ 登录成功")

# 2. 检查后端可用的工具
print("\n步骤2: 检查后端可用工具")
# 后端定义的可用工具
AVAILABLE_TOOLS = [
    "knowledge_search",
    "web_search",
    "calculator",
    "code_interpreter",
    "database_query"
]
print(f"后端 AVAILABLE_TOOLS: {AVAILABLE_TOOLS}")
print(f"前端 AVAILABLE_TOOLS: {['knowledge_search', 'calculator', 'web_search', 'datetime']}")
print(f"不一致: 前端有 'datetime'，后端没有")

# 3. 尝试创建带 datetime 工具的 Agent
print("\n步骤3: 尝试创建带 datetime 工具的 Agent")
test_agent_data = {
    "name": "test_datetime_agent",
    "display_name": "测试时间工具",
    "description": "测试 datetime 工具",
    "agent_type": "tool",
    "system_prompt": "你是一个测试助手",
    "tools": ["datetime"],  # 使用前端定义但后端不支持的工具
    "knowledge_base_ids": []
}

resp = requests.post(
    f"{BASE_URL}/agents",
    headers=headers,
    json=test_agent_data
)

print(f"HTTP 状态码: {resp.status_code}")
print(f"响应内容: {resp.text[:500]}")

if resp.status_code == 400:
    print("✗ 错误：后端不支持 'datetime' 工具")
    print(f"  错误详情: {resp.json()}")
elif resp.status_code == 200:
    print("✓ Agent 创建成功（但后端可能不处理 datetime 工具）")
    agent = resp.json()
    agent_id = agent["id"]

    # 4. 测试上线/下线
    print("\n步骤4: 测试上线/下线功能")
    print(f"Agent 当前状态: is_active = {agent.get('is_active')}")

    # 尝试切换状态
    resp = requests.put(
        f"{BASE_URL}/agents/{agent_id}",
        headers=headers,
        json={"is_active": False}
    )

    print(f"PUT 请求状态码: {resp.status_code}")

    if resp.status_code == 200:
        print("✓ PUT 请求成功")
        result = resp.json()
        print(f"  更新后状态: is_active = {result.get('is_active')}")

        # 验证 Agent 仍存在
        resp2 = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=headers)
        if resp2.status_code == 200:
            print("✓ Agent 仍然存在（未被删除）")
        else:
            print("✗ Agent 不存在（被意外删除）")
    else:
        print(f"✗ PUT 请求失败: {resp.text[:200]}")

    # 5. 清理测试 Agent
    print("\n步骤5: 清理测试 Agent")
    resp = requests.delete(f"{BASE_URL}/agents/{agent_id}", headers=headers)
    if resp.status_code == 200:
        print("✓ 测试 Agent 已删除")
else:
    print(f"✗ 创建失败: {resp.status_code}")

print("\n" + "=" * 80)
print("诊断完成")
print("=" * 80)
