"""
Agent API 测试脚本
测试 Agent 模块的完整功能
"""
import requests
import json
import time

BASE_URL = "http://localhost:8080/api/v1"

def get_admin_token():
    """获取 admin token"""
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "pwd123"
    })
    if resp.status_code != 200:
        raise Exception(f"登录失败: {resp.text}")
    return resp.json()["token"]

def test_health_check():
    """测试 Agent 服务健康检查"""
    print("\n" + "="*80)
    print("测试 1: Agent 服务健康检查")
    print("="*80)

    resp = requests.get(f"{BASE_URL}/agents/service-health")
    print(f"状态码: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")

    assert resp.status_code == 200, "健康检查失败"
    assert resp.json()["status"] == "healthy", "服务状态不健康"
    print("✅ 健康检查通过")

def test_list_tools():
    """测试工具列表"""
    print("\n" + "="*80)
    print("测试 2: 获取可用工具列表")
    print("="*80)

    resp = requests.get(f"{BASE_URL}/agents/tools")
    print(f"状态码: {resp.status_code}")

    data = resp.json()
    print(f"工具数量: {len(data['tools'])}")
    print("工具列表:")
    for tool in data["tools"]:
        print(f"  - {tool['display_name']} ({tool['name']}): {tool['description']}")

    assert resp.status_code == 200, "获取工具列表失败"
    assert len(data["tools"]) >= 3, "工具数量不足"
    print("✅ 工具列表获取成功")

def test_create_agent():
    """测试创建 Agent"""
    print("\n" + "="*80)
    print("测试 3: 创建 Agent")
    print("="*80)

    token = get_admin_token()

    agent_data = {
        "name": "test_calculator",
        "display_name": "测试计算助手",
        "description": "用于测试的计算助手",
        "agent_type": "tool",
        "tools": ["calculator", "datetime"],
        "config": {
            "temperature": 0.7,
            "max_steps": 10
        }
    }

    resp = requests.post(
        f"{BASE_URL}/agents/",
        headers={"Authorization": f"Bearer {token}"},
        json=agent_data
    )
    print(f"状态码: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")

    assert resp.status_code == 200, f"创建 Agent 失败: {resp.text}"
    agent_id = resp.json()["id"]
    print(f"✅ Agent 创建成功: {agent_id}")
    return agent_id

def test_list_agents():
    """测试列出 Agent"""
    print("\n" + "="*80)
    print("测试 4: 列出所有 Agent")
    print("="*80)

    token = get_admin_token()

    resp = requests.get(
        f"{BASE_URL}/agents/",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"状态码: {resp.status_code}")

    data = resp.json()
    agents = data["agents"]
    print(f"Agent 数量: {len(agents)}")

    if agents:
        print("Agent 列表:")
        for agent in agents[:5]:  # 只显示前5个
            print(f"  - {agent['display_name']} ({agent['name']}): {agent['description']}")
    else:
        print("  暂无 Agent")

    assert resp.status_code == 200, "获取 Agent 列表失败"
    print("✅ Agent 列表获取成功")

def test_agent_chat_calculator():
    """测试 Agent 计算器对话"""
    print("\n" + "="*80)
    print("测试 5: Agent 计算器对话")
    print("="*80)

    token = get_admin_token()

    # 先创建一个计算器 Agent
    agent_data = {
        "name": f"calc_agent_{int(time.time())}",
        "display_name": "计算器",
        "description": "数学计算助手",
        "agent_type": "tool",
        "tools": ["calculator"]
    }

    resp = requests.post(
        f"{BASE_URL}/agents/",
        headers={"Authorization": f"Bearer {token}"},
        json=agent_data
    )
    assert resp.status_code == 200, f"创建 Agent 失败: {resp.text}"
    agent_id = resp.json()["id"]
    print(f"✅ Agent 创建成功: {agent_id}")

    # 发送计算请求
    chat_request = {
        "query": "123 + 456 = ?",
        "stream": True
    }

    print(f"发送查询: {chat_request['query']}")

    resp = requests.post(
        f"{BASE_URL}/agents/{agent_id}/chat",
        headers={"Authorization": f"Bearer {token}"},
        json=chat_request,
        stream=True
    )

    print(f"状态码: {resp.status_code}")

    if resp.status_code == 200:
        print("开始接收流式响应:")
        for line in resp.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data:'):
                    data_str = line_text[5:].strip()
                    if data_str == '[DONE]':
                        print("✅ 响应完成")
                        break
                    try:
                        event = json.loads(data_str)
                        event_type = event.get('type')
                        if event_type == 'start':
                            print(f"  🚀 开始执行")
                        elif event_type == 'step':
                            print(f"  📍 步骤: {event.get('node')}")
                        elif event_type == 'tool_call':
                            print(f"  🔧 工具调用: {event.get('tool')}")
                        elif event_type == 'complete':
                            print(f"  ✅ 完成: {event.get('output')}")
                        elif event_type == 'error':
                            print(f"  ❌ 错误: {event.get('error')}")
                    except json.JSONDecodeError:
                        pass
    else:
        print(f"❌ 对话失败: {resp.text}")

    assert resp.status_code == 200, "Agent 对话失败"
    print("✅ Agent 计算器对话测试通过")

def test_agent_chat_datetime():
    """测试 Agent 时间查询"""
    print("\n" + "="*80)
    print("测试 6: Agent 时间查询")
    print("="*80)

    token = get_admin_token()

    # 创建一个时间查询 Agent
    agent_data = {
        "name": f"time_agent_{int(time.time())}",
        "display_name": "时间助手",
        "description": "查询当前时间",
        "agent_type": "tool",
        "tools": ["datetime"]
    }

    resp = requests.post(
        f"{BASE_URL}/agents/",
        headers={"Authorization": f"Bearer {token}"},
        json=agent_data
    )
    assert resp.status_code == 200, f"创建 Agent 失败: {resp.text}"
    agent_id = resp.json()["id"]
    print(f"✅ Agent 创建成功: {agent_id}")

    # 发送时间查询
    chat_request = {
        "query": "现在几点了？",
        "stream": True
    }

    print(f"发送查询: {chat_request['query']}")

    resp = requests.post(
        f"{BASE_URL}/agents/{agent_id}/chat",
        headers={"Authorization": f"Bearer {token}"},
        json=chat_request,
        stream=True
    )

    print(f"状态码: {resp.status_code}")

    if resp.status_code == 200:
        for line in resp.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data:'):
                    data_str = line_text[5:].strip()
                    if data_str == '[DONE]':
                        break
                    try:
                        event = json.loads(data_str)
                        if event.get('type') == 'complete':
                            print(f"✅ 查询结果: {event.get('output')}")
                    except json.JSONDecodeError:
                        pass
    else:
        print(f"❌ 对话失败: {resp.text}")

    assert resp.status_code == 200, "Agent 对话失败"
    print("✅ Agent 时间查询测试通过")

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print("开始 Agent API 测试")
    print("="*80)

    tests = [
        ("健康检查", test_health_check),
        ("工具列表", test_list_tools),
        ("创建 Agent", test_create_agent),
        ("列出 Agent", test_list_agents),
        ("计算器对话", test_agent_chat_calculator),
        ("时间查询", test_agent_chat_datetime),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"\n✅ {name} 测试通过")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} 测试失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("="*80)

    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
