#!/usr/bin/env python3
"""
测试 Agent API - 验证 PUT 和 DELETE 请求
"""
import requests
import json

BASE_URL = "http://localhost:9003/api/v1"
USERNAME = "admin"
PASSWORD = "pwd123"

# 1. 登录获取 token
print("=" * 80)
print("步骤1: 登录")
resp = requests.post(f"{BASE_URL}/auth/login", json={
    "username": USERNAME,
    "password": PASSWORD
})
token = resp.json()["token"]
print(f"✓ 登录成功，token: {token[:50]}...")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 2. 获取 Agent 列表
print("\n步骤2: 获取 Agent 列表")
resp = requests.get(f"{BASE_URL}/agents", headers=headers)
agents = resp.json()
print(f"✓ 找到 {len(agents)} 个 Agent")

if len(agents) == 0:
    print("⚠️  没有 Agent，先创建一个测试 Agent")
    # 创建测试 Agent
    create_data = {
        "name": "test_agent",
        "display_name": "测试员工",
        "description": "用于测试的 Agent",
        "agent_type": "rag",
        "system_prompt": "你是一个测试助手",
        "tools": [],
        "knowledge_base_ids": []
    }
    resp = requests.post(f"{BASE_URL}/agents", headers=headers, json=create_data)
    agent = resp.json()
    print(f"✓ 创建测试 Agent: {agent['id']}")
else:
    agent = agents[0]
    print(f"  使用现有 Agent: {agent['id']}")

agent_id = agent["id"]
current_status = agent.get("is_active", True)
print(f"  当前状态: is_active = {current_status}")

# 3. 测试 PUT 请求（切换上线/下线）
print("\n步骤3: 测试 PUT 请求切换上线/下线")
print(f"  将 is_active 从 {current_status} 改为 {not current_status}")

update_data = {
    "is_active": not current_status
}

resp = requests.put(
    f"{BASE_URL}/agents/{agent_id}",
    headers=headers,
    json=update_data
)

print(f"  HTTP 状态码: {resp.status_code}")
print(f"  响应内容: {resp.text[:200]}")

if resp.status_code == 200:
    print("✓ PUT 请求成功 - Agent 状态已更新")
    result = resp.json()
    print(f"  新状态: is_active = {result.get('is_active')}")
elif resp.status_code == 404:
    print("✗ 404 错误 - Agent 不存在或路由问题")
elif resp.status_code == 405:
    print("✗ 405 错误 - 方法不允许（路由配置问题）")
else:
    print(f"✗ 其他错误: {resp.status_code}")

# 4. 验证 Agent 是否还存在（没有被删除）
print("\n步骤4: 验证 Agent 是否仍存在")
resp = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=headers)

if resp.status_code == 200:
    agent_check = resp.json()
    print(f"✓ Agent 仍然存在")
    print(f"  ID: {agent_check['id']}")
    print(f"  Name: {agent_check.get('display_name', agent_check['name'])}")
    print(f"  is_active: {agent_check.get('is_active')}")
elif resp.status_code == 404:
    print("✗ Agent 不存在 - 被意外删除了！")
else:
    print(f"✗ 其他错误: {resp.status_code}")

# 5. 恢复原始状态
print("\n步骤5: 恢复原始状态")
resp = requests.put(
    f"{BASE_URL}/agents/{agent_id}",
    headers=headers,
    json={"is_active": current_status}
)

if resp.status_code == 200:
    print("✓ 状态已恢复")
else:
    print(f"✗ 恢复失败: {resp.status_code}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
