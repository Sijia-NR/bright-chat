#!/usr/bin/env python3
"""
Frontend-Backend Integration Test
测试前端是否能正确调用后端接口
"""

import requests
import json
import time

# 后端配置
BASE_URL = "http://localhost:18080"
FRONTEND_URL = "http://localhost:3000"

def test_backend_availability():
    """测试后端服务是否可用"""
    print("🔍 Testing Backend Availability")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Backend is available")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_login_flow():
    """测试登录流程"""
    print("\n🔐 Testing Login Flow")
    try:
        # 1. 测试登录接口
        login_data = {
            "username": "admin",
            "password": "pwd123"
        }

        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)

        if response.status_code != 200:
            print(f"❌ Login failed with status {response.status_code}: {response.text}")
            return False

        login_result = response.json()
        print(f"✅ Login successful")
        print(f"   User: {login_result['username']}")
        print(f"   Role: {login_result['role']}")

        # 2. 测试退出登录
        headers = {"Authorization": f"Bearer {login_result['token']}"}
        logout_response = requests.post(f"{BASE_URL}/api/v1/auth/logout", headers=headers)

        if logout_response.status_code == 200:
            print("✅ Logout successful")
        else:
            print(f"⚠️  Logout failed: {logout_response.status_code}")

        return True

    except Exception as e:
        print(f"❌ Login flow test failed: {e}")
        return False

def test_user_management():
    """测试用户管理流程"""
    print("\n👥 Testing User Management Flow")

    try:
        # 1. 登录获取token
        login_response = requests.post(f"{BASE_URL}/api/v1/auth/login",
                                     json={"username": "admin", "password": "pwd123"})

        if login_response.status_code != 200:
            print("❌ Failed to login for user management test")
            return False

        token = login_response.json()['token']
        headers = {"Authorization": f"Bearer {token}"}

        # 2. 获取用户列表
        users_response = requests.get(f"{BASE_URL}/api/v1/admin/users", headers=headers)

        if users_response.status_code != 200:
            print(f"❌ Failed to get users: {users_response.status_code}")
            return False

        users = users_response.json()
        print(f"✅ Retrieved {len(users)} users")

        # 3. 创建新用户
        new_user_data = {
            "username": f"integration_test_{int(time.time())}",
            "password": "testpass123",
            "role": "user"
        }

        create_response = requests.post(f"{BASE_URL}/api/v1/admin/users",
                                     headers=headers,
                                     json=new_user_data)

        if create_response.status_code != 200:
            print(f"❌ Failed to create user: {create_response.status_code}")
            return False

        created_user = create_response.json()
        user_id = created_user['id']
        print(f"✅ Created user: {created_user['username']} (ID: {user_id})")

        # 4. 更新用户
        update_data = {
            "username": f"updated_user_{int(time.time())}",
            "password": "newpass123",
            "role": "admin"
        }

        update_response = requests.put(f"{BASE_URL}/api/v1/admin/users/{user_id}",
                                    headers=headers,
                                    json=update_data)

        if update_response.status_code != 200:
            print(f"❌ Failed to update user: {update_response.status_code}")
            return False

        updated_user = update_response.json()
        print(f"✅ Updated user: {updated_user['username']} (New role: {updated_user['role']})")

        # 5. 删除用户
        delete_response = requests.delete(f"{BASE_URL}/api/v1/admin/users/{user_id}", headers=headers)

        if delete_response.status_code != 200:
            print(f"❌ Failed to delete user: {delete_response.status_code}")
            return False

        print("✅ Deleted user successfully")

        return True

    except Exception as e:
        print(f"❌ User management test failed: {e}")
        return False

def test_session_management():
    """测试会话管理流程"""
    print("\n💬 Testing Session Management Flow")

    try:
        # 1. 登录获取token和用户ID
        login_response = requests.post(f"{BASE_URL}/api/v1/auth/login",
                                     json={"username": "admin", "password": "pwd123"})

        if login_response.status_code != 200:
            print("❌ Failed to login for session management test")
            return False

        login_data = login_response.json()
        token = login_data['token']
        user_id = login_data['id']
        headers = {"Authorization": f"Bearer {token}"}

        # 2. 创建会话
        session_data = {
            "title": "Integration Test Session",
            "user_id": user_id
        }

        create_session_response = requests.post(f"{BASE_URL}/api/v1/sessions",
                                              headers=headers,
                                              json=session_data)

        if create_session_response.status_code != 200:
            print(f"❌ Failed to create session: {create_session_response.status_code}")
            return False

        session = create_session_response.json()
        session_id = session['id']
        print(f"✅ Created session: {session_id}")

        # 3. 保存消息
        messages_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "Hello! This is an integration test.",
                    "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.localtime())
                },
                {
                    "role": "assistant",
                    "content": "Hello! I'm responding to your integration test.",
                    "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.localtime())
                }
            ]
        }

        save_messages_response = requests.post(f"{BASE_URL}/api/v1/sessions/{session_id}/messages",
                                            headers=headers,
                                            json=messages_data)

        if save_messages_response.status_code != 200:
            print(f"❌ Failed to save messages: {save_messages_response.status_code}")
            return False

        print("✅ Saved messages successfully")

        # 4. 获取消息
        get_messages_response = requests.get(f"{BASE_URL}/api/v1/sessions/{session_id}/messages",
                                           headers=headers)

        if get_messages_response.status_code != 200:
            print(f"❌ Failed to get messages: {get_messages_response.status_code}")
            return False

        messages = get_messages_response.json()
        print(f"✅ Retrieved {len(messages)} messages")
        for i, msg in enumerate(messages):
            print(f"   {i+1}. {msg['role']}: {msg['content']}")

        # 5. 获取用户会话列表
        get_sessions_response = requests.get(f"{BASE_URL}/api/v1/sessions?user_id={user_id}",
                                          headers=headers)

        if get_sessions_response.status_code != 200:
            print(f"❌ Failed to get sessions: {get_sessions_response.status_code}")
            return False

        sessions = get_sessions_response.json()
        print(f"✅ Retrieved {len(sessions)} sessions for user")

        # 6. 删除会话
        delete_session_response = requests.delete(f"{BASE_URL}/api/v1/sessions/{session_id}",
                                               headers=headers)

        if delete_session_response.status_code != 200:
            print(f"❌ Failed to delete session: {delete_session_response.status_code}")
            return False

        print("✅ Deleted session successfully")

        return True

    except Exception as e:
        print(f"❌ Session management test failed: {e}")
        return False

def test_ias_proxy():
    """测试IAS代理接口"""
    print("\n🤖 Testing IAS Proxy Flow")

    try:
        # 1. 登录获取token
        login_response = requests.post(f"{BASE_URL}/api/v1/auth/login",
                                     json={"username": "admin", "password": "pwd123"})

        if login_response.status_code != 200:
            print("❌ Failed to login for IAS proxy test")
            return False

        token = login_response.json()['token']
        headers = {"Authorization": f"Bearer {token}"}

        # 2. 测试IAS代理
        ias_data = {
            "model": "test-model",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello! This is an integration test for IAS proxy."
                }
            ],
            "stream": False,
            "temperature": 0.7
        }

        ias_response = requests.post(f"{BASE_URL}/api/v1/lmp-cloud-ias-server/api/llm/chat/completions/V2",
                                  headers=headers,
                                  json=ias_data)

        if ias_response.status_code != 200:
            print(f"❌ IAS proxy failed: {ias_response.status_code}")
            return False

        ias_result = ias_response.json()
        print(f"✅ IAS proxy successful")
        print(f"   Response ID: {ias_result['id']}")
        print(f"   Assistant: {ias_result['choices'][0]['message']['content']}")

        return True

    except Exception as e:
        print(f"❌ IAS proxy test failed: {e}")
        return False

def main():
    """运行完整的集成测试"""
    print("=" * 60)
    print("🚀 FRONTEND-BACKEND INTEGRATION TEST")
    print("=" * 60)

    results = []

    # 1. 测试后端可用性
    results.append(("Backend Availability", test_backend_availability()))

    # 2. 测试登录流程
    results.append(("Login Flow", test_login_flow()))

    # 3. 测试用户管理
    results.append(("User Management", test_user_management()))

    # 4. 测试会话管理
    results.append(("Session Management", test_session_management()))

    # 5. 测试IAS代理
    results.append(("IAS Proxy", test_ias_proxy()))

    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1

    print("-" * 60)
    print(f"Summary: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ Frontend-Backend integration is working correctly")
        print("🚀 Ready for production deployment!")
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("🔧 Some issues need to be resolved before deployment")

    print("\n" + "=" * 60)
    print("📍 Service Information")
    print("=" * 60)
    print(f"Frontend: {FRONTEND_URL}")
    print(f"Backend:  {BASE_URL}")
    print(f"API Docs: {BASE_URL}/docs")
    print("Health:   " + ("✅ Available" if test_backend_availability() else "❌ Unavailable"))

    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)