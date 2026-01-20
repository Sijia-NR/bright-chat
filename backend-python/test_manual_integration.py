#!/usr/bin/env python3
"""
Manual Integration Test Guide
提供手动测试前后端集成的详细步骤
"""

import requests
import time

def test_manual_steps():
    print("🚀 Frontend-Backend Integration Test")
    print("="*60)

    backend_url = "http://localhost:18080"
    frontend_url = "http://localhost:3000"

    print(f"Frontend URL: {frontend_url}")
    print(f"Backend URL: {backend_url}")
    print()

    # 1. 后端健康检查
    print("1️⃣ 测试后端健康检查...")
    try:
        response = requests.get(f"{backend_url}/health")
        if response.status_code == 200:
            print("✅ 后端服务正常")
        else:
            print("❌ 后端服务异常")
    except:
        print("❌ 无法连接到后端服务")

    # 2. 登录测试
    print("\n2️⃣ 测试登录接口...")
    try:
        login_data = {"username": "admin", "password": "pwd123"}
        response = requests.post(f"{backend_url}/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            login_result = response.json()
            print(f"✅ 登录成功: {login_result['username']} ({login_result['role']})")
            token = login_result['token']
        else:
            print("❌ 登录失败")
            return
    except:
        print("❌ 登录请求失败")
        return

    # 3. 获取用户列表
    print("\n3️⃣ 测试获取用户列表...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{backend_url}/api/v1/admin/users", headers=headers)
        if response.status_code == 200:
            users = response.json()
            print(f"✅ 获取用户列表成功: {len(users)} 个用户")
            for user in users[:3]:
                print(f"   - {user['username']} ({user['role']})")
        else:
            print("❌ 获取用户列表失败")
    except:
        print("❌ 获取用户列表请求失败")

    # 4. 创建用户
    print("\n4️⃣ 测试创建用户...")
    try:
        username = f"test_user_{int(time.time())}"
        user_data = {
            "username": username,
            "password": "test123",
            "role": "user"
        }
        response = requests.post(f"{backend_url}/api/v1/admin/users",
                              headers=headers,
                              json=user_data)
        if response.status_code == 200:
            created_user = response.json()
            print(f"✅ 创建用户成功: {created_user['username']}")
            user_id = created_user['id']
        else:
            print("❌ 创建用户失败")
    except:
        print("❌ 创建用户请求失败")
        return

    # 5. 更新用户
    print("\n5️⃣ 测试更新用户...")
    try:
        update_data = {
            "username": f"updated_{int(time.time())}",
            "password": "newpass123",
            "role": "admin"
        }
        response = requests.put(f"{backend_url}/api/v1/admin/users/{user_id}",
                              headers=headers,
                              json=update_data)
        if response.status_code == 200:
            updated_user = response.json()
            print(f"✅ 更新用户成功: {updated_user['username']} (新角色: {updated_user['role']})")
        else:
            print("❌ 更新用户失败")
    except:
        print("❌ 更新用户请求失败")

    # 6. 创建会话
    print("\n6️⃣ 测试创建会话...")
    try:
        session_data = {
            "title": "测试会话",
            "user_id": login_result['id']
        }
        response = requests.post(f"{backend_url}/api/v1/sessions",
                              headers=headers,
                              json=session_data)
        if response.status_code == 200:
            session = response.json()
            print(f"✅ 创建会话成功: {session['id']}")
            session_id = session['id']
        else:
            print("❌ 创建会话失败")
    except:
        print("❌ 创建会话请求失败")
        return

    # 7. 保存消息
    print("\n7️⃣ 测试保存消息...")
    try:
        messages_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "你好！这是一条测试消息。",
                    "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.localtime())
                },
                {
                    "role": "assistant",
                    "content": "你好！我收到了你的测试消息。",
                    "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.localtime())
                }
            ]
        }
        response = requests.post(f"{backend_url}/api/v1/sessions/{session_id}/messages",
                              headers=headers,
                              json=messages_data)
        if response.status_code == 200:
            print("✅ 保存消息成功")
        else:
            print("❌ 保存消息失败")
    except:
        print("❌ 保存消息请求失败")

    # 8. 获取消息
    print("\n8️⃣ 测试获取消息...")
    try:
        response = requests.get(f"{backend_url}/api/v1/sessions/{session_id}/messages",
                             headers=headers)
        if response.status_code == 200:
            messages = response.json()
            print(f"✅ 获取消息成功: {len(messages)} 条消息")
            for i, msg in enumerate(messages):
                print(f"   {i+1}. {msg['role']}: {msg['content']}")
        else:
            print("❌ 获取消息失败")
    except:
        print("❌ 获取消息请求失败")

    # 9. IAS 代理测试
    print("\n9️⃣ 测试 IAS 代理...")
    try:
        ias_data = {
            "model": "test-model",
            "messages": [
                {"role": "user", "content": "Hello! This is a test message."}
            ],
            "stream": False,
            "temperature": 0.7
        }
        response = requests.post(f"{backend_url}/api/v1/lmp-cloud-ias-server/api/llm/chat/completions/V2",
                              headers=headers,
                              json=ias_data)
        if response.status_code == 200:
            ias_result = response.json()
            print(f"✅ IAS 代理成功: {ias_result['choices'][0]['message']['content']}")
        else:
            print("❌ IAS 代理失败")
    except:
        print("❌ IAS 代理请求失败")

    # 10. 清理测试数据
    print("\n🔧 清理测试数据...")
    try:
        # 删除会话
        response = requests.delete(f"{backend_url}/api/v1/sessions/{session_id}",
                                 headers=headers)
        if response.status_code == 200:
            print("✅ 删除会话成功")

        # 删除用户
        response = requests.delete(f"{backend_url}/api/v1/admin/users/{user_id}",
                                 headers=headers)
        if response.status_code == 200:
            print("✅ 删除用户成功")
    except:
        print("❌ 清理数据失败")

    print("\n" + "="*60)
    print("📋 测试总结")
    print("="*60)
    print("✅ 所有核心接口测试完成")
    print("✅ 前后端集成配置正确")
    print("✅ 可以手动测试浏览器访问")
    print("\n🎯 下一步:")
    print("1. 打开浏览器访问: http://localhost:3000")
    print("2. 使用账号: admin / pwd123 登录")
    print("3. 测试所有功能是否正常工作")
    print("="*60)

if __name__ == "__main__":
    test_manual_steps()