#!/usr/bin/env python3
"""
Comprehensive test script for Bright-Chat API endpoints
"""
import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:18080"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_login():
    """Test login endpoint"""
    print("\n=== Testing Login Endpoint ===")
    data = {
        "username": "admin",
        "password": "pwd123"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=data)
    print(f"Status: {response.status_code}")
    print(f"Request body: {json.dumps(data, indent=2)}")

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Login successful!")
        print(f"Response: {json.dumps(result, indent=2, default=str)}")
        return result
    else:
        print(f"❌ Error: {response.text}")
        return None

def test_logout(token):
    """Test logout endpoint"""
    print("\n=== Testing Logout Endpoint ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/v1/auth/logout", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    return response.status_code == 200

def test_get_users(token):
    """Test get users endpoint"""
    print("\n=== Testing Get Users Endpoint ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/admin/users", headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        users = response.json()
        print(f"✅ Got {len(users)} users:")
        for user in users:
            print(f"  - {user['username']} ({user['role']})")
        return users
    else:
        print(f"❌ Error: {response.text}")
        return None

def test_create_user(token):
    """Test create user endpoint"""
    print("\n=== Testing Create User Endpoint ===")
    headers = {"Authorization": f"Bearer {token}"}
    test_user = {
        "username": f"testuser_{int(time.time())}",
        "password": "testpass123",
        "role": "user"
    }

    print(f"Request body: {json.dumps(test_user, indent=2)}")
    response = requests.post(f"{BASE_URL}/api/v1/admin/users", headers=headers, json=test_user)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"✅ User created successfully:")
        print(f"Response: {json.dumps(result, indent=2, default=str)}")
        return result
    else:
        print(f"❌ Error: {response.text}")
        return None

def test_update_user(token):
    """Test update user endpoint"""
    print("\n=== Testing Update User Endpoint ===")
    # 首先创建一个用户
    users = test_get_users(token)
    if not users:
        print("❌ Cannot update user - no users found")
        return None

    user_id = users[-1]['id']
    headers = {"Authorization": f"Bearer {token}"}

    # 更新用户
    update_data = {
        "username": f"updated_user_{int(time.time())}",
        "password": "newpassword123",
        "role": "admin"
    }

    print(f"Updating user {user_id} with: {json.dumps(update_data, indent=2)}")

    try:
        response = requests.put(
            f"{BASE_URL}/api/v1/admin/users/{user_id}",
            headers=headers,
            json=update_data
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ User updated successfully:")
            print(f"Response: {json.dumps(result, indent=2, default=str)}")
            return result
        else:
            print(f"❌ Update failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_delete_user(token):
    """Test delete user endpoint"""
    print("\n=== Testing Delete User Endpoint ===")
    headers = {"Authorization": f"Bearer {token}"}

    # 首先创建一个临时用户
    temp_user_data = {
        "username": f"delete_user_{int(time.time())}",
        "password": "delete123",
        "role": "user"
    }

    # 创建用户
    create_response = requests.post(
        f"{BASE_URL}/api/v1/admin/users",
        headers=headers,
        json=temp_user_data
    )

    if create_response.status_code == 200:
        user_id = create_response.json()['id']
        print(f"Created temporary user: {user_id}")

        # 删除用户
        print(f"Deleting user {user_id}")
        delete_response = requests.delete(
            f"{BASE_URL}/api/v1/admin/users/{user_id}",
            headers=headers
        )

        print(f"Status: {delete_response.status_code}")
        print(f"Response: {delete_response.text}")

        if delete_response.status_code == 200:
            # 验证用户已被删除
            check_response = requests.get(f"{BASE_URL}/api/v1/admin/users", headers=headers)
            users = check_response.json()
            deleted_user = next((u for u in users if u['id'] == user_id), None)

            if not deleted_user:
                print("✅ User deleted successfully")
                return True
            else:
                print("❌ User still exists after deletion")
                return False
        else:
            print(f"❌ Delete failed: {delete_response.text}")
            return False
    else:
        print(f"❌ Failed to create user for deletion: {create_response.text}")
        return False

def test_sessions(token, user_id):
    """Test all session-related endpoints"""
    print("\n=== Testing Session Endpoints ===")

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get sessions
    print("\n--- Getting sessions ---")
    response = requests.get(f"{BASE_URL}/api/v1/sessions?user_id={user_id}", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        sessions = response.json()
        print(f"✅ Found {len(sessions)} sessions")
    else:
        print(f"❌ Error: {response.text}")
        return

    # 2. Create session
    print("\n--- Creating session ---")
    session_data = {
        "title": f"Test Session {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "user_id": user_id
    }

    print(f"Request: {json.dumps(session_data, indent=2)}")
    response = requests.post(f"{BASE_URL}/api/v1/sessions", headers=headers, json=session_data)

    if response.status_code == 200:
        session = response.json()
        session_id = session['id']
        print(f"✅ Session created: {session_id}")

        # 3. Save messages
        print("\n--- Saving messages ---")
        messages_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "Hello, this is a test message!",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                {
                    "role": "assistant",
                    "content": "Hi there! I'm here to help you.",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            ]
        }

        print(f"Request: {json.dumps(messages_data, indent=2)}")
        response = requests.post(
            f"{BASE_URL}/api/v1/sessions/{session_id}/messages",
            headers=headers,
            json=messages_data
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Messages saved successfully")

            # 4. Get messages
            print("\n--- Getting messages ---")
            response = requests.get(f"{BASE_URL}/api/v1/sessions/{session_id}/messages", headers=headers)

            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                messages = response.json()
                print(f"✅ Got {len(messages)} messages:")
                for msg in messages:
                    print(f"  - {msg['role']}: {msg['content']}")

            # 5. Delete session
            print("\n--- Deleting session ---")
            response = requests.delete(f"{BASE_URL}/api/v1/sessions/{session_id}", headers=headers)

            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Session deleted successfully")
            else:
                print(f"❌ Delete failed: {response.text}")

        else:
            print(f"❌ Save messages failed: {response.text}")
    else:
        print(f"❌ Create session failed: {response.text}")

def test_ias_proxy(token):
    """Test IAS API proxy endpoint"""
    print("\n=== Testing IAS API Proxy Endpoint ===")
    headers = {"Authorization": f"Bearer {token}"}

    # 测试数据
    chat_data = {
        "model": "test-model",
        "messages": [
            {
                "role": "user",
                "content": "Hello, this is a test!"
            }
        ],
        "stream": False,
        "temperature": 0.7
    }

    print(f"Request: {json.dumps(chat_data, indent=2)}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/lmp-cloud-ias-server/api/llm/chat/completions/V2",
            headers=headers,
            json=chat_data
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ IAS proxy call successful")
            print(f"Response: {response.text[:200]}...")
        else:
            print(f"❌ IAS proxy failed: {response.text}")
    except Exception as e:
        print(f"❌ IAS proxy error (expected in test environment): {str(e)}")

def main():
    """Run comprehensive tests"""
    print("Starting Comprehensive API Tests...")

    # Test health
    if not test_health():
        print("❌ Health check failed, exiting tests")
        return

    # Test login
    login_result = test_login()
    if not login_result:
        print("❌ Login failed, exiting tests")
        return

    token = login_result['token']
    user_id = login_result['id']

    # Test authentication endpoints
    test_logout(token)

    # Test admin endpoints
    test_get_users(token)
    created_user = test_create_user(token)
    test_update_user(token)
    test_delete_user(token)

    # Test session endpoints
    test_sessions(token, user_id)

    # Test IAS proxy
    test_ias_proxy(token)

    print("\n=== Comprehensive Tests Completed ===")

if __name__ == "__main__":
    main()