#!/usr/bin/env python3
"""
Simple and focused API test
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:18080"

def test_all_interfaces():
    print("🧪 Testing All API Interfaces")
    print("=" * 50)

    # 1. Health Check
    print("\n1️⃣  Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code} - {response.json()}")

    # 2. Login
    print("\n2️⃣  Login")
    login_data = {"username": "admin", "password": "pwd123"}
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json()['token']
        print(f"   ✅ Login successful - Token: {token[:30]}...")
    else:
        print(f"   ❌ Login failed: {response.text}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get Users
    print("\n3️⃣  Get Users")
    response = requests.get(f"{BASE_URL}/api/v1/admin/users", headers=headers)
    print(f"   Status: {response.status_code} - Users: {len(response.json())}")

    # 4. Create User
    print("\n4️⃣  Create User")
    username = f"test_{int(time.time())}"
    user_data = {"username": username, "password": "test123", "role": "user"}
    response = requests.post(f"{BASE_URL}/api/v1/admin/users", headers=headers, json=user_data)
    if response.status_code == 200:
        user_id = response.json()['id']
        print(f"   ✅ Created user: {username} (ID: {user_id})")
    else:
        print(f"   ❌ Create failed: {response.text}")
        return

    # 5. Update User
    print("\n5️⃣  Update User")
    update_data = {"username": f"updated_{int(time.time())}", "password": "newpass", "role": "admin"}
    response = requests.put(f"{BASE_URL}/api/v1/admin/users/{user_id}", headers=headers, json=update_data)
    print(f"   Status: {response.status_code} - Updated to: {response.json()['role']}")

    # 6. Create Session
    print("\n6️⃣  Create Session")
    session_data = {"title": "Test Session", "user_id": user_id}
    response = requests.post(f"{BASE_URL}/api/v1/sessions", headers=headers, json=session_data)
    if response.status_code == 200:
        session_id = response.json()['id']
        print(f"   ✅ Created session: {session_id}")
    else:
        print(f"   ❌ Session create failed: {response.text}")
        return

    # 7. Save Messages (correct order)
    print("\n7️⃣  Save Messages")
    messages_data = {
        "messages": [
            {"role": "user", "content": "Hello!", "timestamp": datetime.utcnow().isoformat() + "Z"},
            {"role": "assistant", "content": "Hi there!", "timestamp": datetime.utcnow().isoformat() + "Z"},
            {"role": "user", "content": "How are you?", "timestamp": datetime.utcnow().isoformat() + "Z"}
        ]
    }
    response = requests.post(f"{BASE_URL}/api/v1/sessions/{session_id}/messages", headers=headers, json=messages_data)
    print(f"   Status: {response.status_code}")

    # 8. Get Messages
    print("\n8️⃣  Get Messages")
    response = requests.get(f"{BASE_URL}/api/v1/sessions/{session_id}/messages", headers=headers)
    if response.status_code == 200:
        messages = response.json()
        print(f"   Status: {response.status_code} - Got {len(messages)} messages:")
        for i, msg in enumerate(messages):
            print(f"      {i+1}. {msg['role']}: {msg['content']}")
    else:
        print(f"   ❌ Get messages failed: {response.text}")

    # 9. Get Sessions
    print("\n9️⃣  Get Sessions")
    response = requests.get(f"{BASE_URL}/api/v1/sessions?user_id={user_id}", headers=headers)
    print(f"   Status: {response.status_code} - Sessions: {len(response.json())}")

    # 10. IAS Proxy
    print("\n🔟 IAS Proxy")
    ias_data = {
        "model": "test",
        "messages": [{"role": "user", "content": "Hello test!"}],
        "stream": False
    }
    response = requests.post(f"{BASE_URL}/api/v1/lmp-cloud-ias-server/api/llm/chat/completions/V2", headers=headers, json=ias_data)
    if response.status_code == 200:
        result = response.json()
        print(f"   Status: {response.status_code} - Response: {result['choices'][0]['message']['content']}")
    else:
        print(f"   ❌ IAS failed: {response.text}")

    # 11. Delete Session
    print("\n1️⃣1️⃣ Delete Session")
    response = requests.delete(f"{BASE_URL}/api/v1/sessions/{session_id}", headers=headers)
    print(f"   Status: {response.status_code}")

    # 12. Delete User
    print("\n1️⃣2️⃣ Delete User")
    response = requests.delete(f"{BASE_URL}/api/v1/admin/users/{user_id}", headers=headers)
    print(f"   Status: {response.status_code}")

    # 13. Logout
    print("\n1️⃣3️⃣ Logout")
    response = requests.post(f"{BASE_URL}/api/v1/auth/logout", headers=headers)
    print(f"   Status: {response.status_code} - {response.json()}")

    print("\n🎉 Interface Test Complete!")

if __name__ == "__main__":
    test_all_interfaces()