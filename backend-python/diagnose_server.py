#!/usr/bin/env python3
"""
诊断 API 服务器状态
"""

import requests
import sys

BASE_URL = "http://localhost:18080"

def check_server():
    """检查服务器状态"""
    print("="*80)
    print("Bright-Chat API 服务器诊断")
    print("="*80)

    # 1. 健康检查
    print("\n[1] 健康检查")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ 服务器运行正常")
            print(f"  响应: {response.json()}")
        else:
            print(f"✗ 服务器响应异常: {response.status_code}")
    except Exception as e:
        print(f"✗ 无法连接到服务器: {e}")
        return False

    # 2. API文档检查
    print("\n[2] API文档检查")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print(f"✓ Swagger文档可访问")
        else:
            print(f"✗ Swagger文档不可访问: {response.status_code}")
    except Exception as e:
        print(f"✗ 文档访问失败: {e}")

    # 3. 登录测试
    print("\n[3] 登录测试")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"username": "admin", "password": "pwd123"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 登录成功")
            print(f"  用户: {data.get('username')}")
            print(f"  角色: {data.get('role')}")
            return data.get('token')
        else:
            print(f"✗ 登录失败: {response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"✗ 登录请求失败: {e}")

    return False

def test_knowledge_groups(token):
    """测试知识库分组"""
    print("\n[4] 知识库分组测试")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/knowledge/groups",
            json={
                "name": "test_group",
                "description": "测试分组",
                "color": "#FF5733"
            },
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            print(f"✓ 创建知识库分组成功")
            data = response.json()
            group_id = data.get('id')
            print(f"  分组ID: {group_id}")

            # 清理
            requests.delete(
                f"{BASE_URL}/api/v1/knowledge/groups/{group_id}",
                headers=headers
            )
            print(f"✓ 清理测试数据完成")
        else:
            print(f"✗ 创建知识库分组失败: {response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"✗ 知识库分组测试失败: {e}")

def test_agents(token):
    """测试数字员工"""
    print("\n[5] 数字员工测试")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/agents",
            json={
                "name": "test_agent",
                "display_name": "测试数字员工",
                "description": "自动化测试",
                "agent_type": "custom"
            },
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            print(f"✓ 创建数字员工成功")
            data = response.json()
            agent_id = data.get('id')
            print(f"  Agent ID: {agent_id}")

            # 清理
            requests.delete(
                f"{BASE_URL}/api/v1/agents/{agent_id}",
                headers=headers
            )
            print(f"✓ 清理测试数据完成")
        else:
            print(f"✗ 创建数字员工失败: {response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"✗ 数字员工测试失败: {e}")

if __name__ == "__main__":
    token = check_server()

    if token:
        test_knowledge_groups(token)
        test_agents(token)

        print("\n" + "="*80)
        print("诊断完成")
        print("="*80)
        print("\n建议:")
        print("1. 如果所有测试通过，服务器运行正常，请重新运行集成测试")
        print("2. 如果知识库或Agent测试失败，需要重启后端服务器:")
        print("   cd /data1/allresearchProject/Bright-Chat/backend-python")
        print("   pkill -f 'python.*minimal_api.py'")
        print("   nohup python3 minimal_api.py > server.log 2>&1 &")
    else:
        print("\n" + "="*80)
        print("服务器未运行或无法连接")
        print("="*80)
        print("\n请先启动后端服务器:")
        print("cd /data1/allresearchProject/Bright-Chat/backend-python")
        print("python3 minimal_api.py")
