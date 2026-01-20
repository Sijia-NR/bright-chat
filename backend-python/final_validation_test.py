#!/usr/bin/env python3
"""
Final validation test for all Bright-Chat API endpoints
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:18080"

def get_auth_token():
    """Get authentication token"""
    data = {
        "username": "admin",
        "password": "pwd123"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=data)
    if response.status_code == 200:
        return response.json()['token']
    else:
        raise Exception(f"Login failed: {response.text}")

def test_all_endpoints():
    """Test all API endpoints"""
    print("=== Final API Validation Test ===")

    # Get auth token
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    print(f"✅ Auth token obtained")

    # Test 1: Get Users
    print("\n1. Testing GET /api/v1/admin/users")
    response = requests.get(f"{BASE_URL}/api/v1/admin/users", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    users = response.json()
    print(f"✅ Retrieved {len(users)} users")

    # Test 2: Create User
    print("\n2. Testing POST /api/v1/admin/users")
    new_user = {
        "username": f"final_test_{int(time.time())}",
        "password": "testpass123",
        "role": "user"
    }
    response = requests.post(f"{BASE_URL}/api/v1/admin/users", headers=headers, json=new_user)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    created_user = response.json()
    user_id = created_user['id']
    print(f"✅ Created user: {created_user['username']} ({created_user['role']})")

    # Test 3: Update User
    print("\n3. Testing PUT /api/v1/admin/users/{user_id}")
    update_data = {
        "username": f"updated_{int(time.time())}",
        "password": "newpass123",
        "role": "admin"
    }
    response = requests.put(f"{BASE_URL}/api/v1/admin/users/{user_id}", headers=headers, json=update_data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    updated_user = response.json()
    print(f"✅ Updated user: {updated_user['username']} ({updated_user['role']})")

    # Test 4: Create Session
    print("\n4. Testing POST /api/v1/sessions")
    session_data = {
        "title": "Final Test Session",
        "user_id": created_user['id']
    }
    response = requests.post(f"{BASE_URL}/api/v1/sessions", headers=headers, json=session_data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    session = response.json()
    session_id = session['id']
    print(f"✅ Created session: {session_id}")

    # Test 5: Save Messages
    print("\n5. Testing POST /api/v1/sessions/{session_id}/messages")
    messages_data = {
        "messages": [
            {
                "role": "user",
                "content": "Hello, final test!",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            {
                "role": "assistant",
                "content": "Hi there! Final test response.",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        ]
    }
    response = requests.post(f"{BASE_URL}/api/v1/sessions/{session_id}/messages", headers=headers, json=messages_data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("✅ Saved messages")

    # Test 6: Get Messages
    print("\n6. Testing GET /api/v1/sessions/{session_id}/messages")
    response = requests.get(f"{BASE_URL}/api/v1/sessions/{session_id}/messages", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    messages = response.json()
    # Verify messages are in correct order (by timestamp)
    assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}"
    assert messages[0]['role'] == 'user', "First message should be from user"
    assert messages[1]['role'] == 'assistant', "Second message should be from assistant"
    print(f"✅ Retrieved {len(messages)} messages in correct order")

    # Test 7: IAS Proxy
    print("\n7. Testing POST /api/v1/lmp-cloud-ias-server/api/llm/chat/completions/V2")
    ias_data = {
        "model": "test-model",
        "messages": [{"role": "user", "content": "Final test message"}],
        "stream": False,
        "temperature": 0.7
    }
    response = requests.post(f"{BASE_URL}/api/v1/lmp-cloud-ias-server/api/llm/chat/completions/V2", headers=headers, json=ias_data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    ias_response = response.json()
    assert 'choices' in ias_response, "IAS response should contain choices"
    print(f"✅ IAS proxy working: {ias_response['choices'][0]['message']['role']}")

    # Test 8: Get Sessions
    print("\n8. Testing GET /api/v1/sessions")
    response = requests.get(f"{BASE_URL}/api/v1/sessions?user_id={created_user['id']}", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    sessions = response.json()
    assert len(sessions) >= 1, f"Should have at least 1 session, got {len(sessions)}"
    print(f"✅ Retrieved {len(sessions)} sessions")

    # Test 9: Delete Session
    print("\n9. Testing DELETE /api/v1/sessions/{session_id}")
    response = requests.delete(f"{BASE_URL}/api/v1/sessions/{session_id}", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("✅ Deleted session")

    # Test 10: Delete User
    print("\n10. Testing DELETE /api/v1/admin/users/{user_id}")
    response = requests.delete(f"{BASE_URL}/api/v1/admin/users/{user_id}", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("✅ Deleted user")

    print("\n🎉 ALL TESTS PASSED! 🎉")
    print("✅ All endpoints are working correctly")
    print("✅ Message order is correct")
    print("✅ User CRUD operations work")
    print("✅ Session management works")
    print("✅ IAS proxy works")
    print("✅ Authentication works")

if __name__ == "__main__":
    test_all_endpoints()