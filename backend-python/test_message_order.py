#!/usr/bin/env python3
"""
Test message ordering specifically
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:18080"

def test_message_order():
    print("🧪 Testing Message Order")
    print("=" * 30)

    # Login
    token = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"username": "admin", "password": "pwd123"}).json()['token']
    headers = {"Authorization": f"Bearer {token}"}

    # Create user
    username = f"order_test_{int(time.time())}"
    user_data = {"username": username, "password": "test123", "role": "user"}
    user_response = requests.post(f"{BASE_URL}/api/v1/admin/users", headers=headers, json=user_data)
    user_id = user_response.json()['id']

    # Create session
    session_data = {"title": "Order Test", "user_id": user_id}
    session_response = requests.post(f"{BASE_URL}/api/v1/sessions", headers=headers, json=session_data)
    session_id = session_response.json()['id']

    print(f"Created session: {session_id}")

    # Save messages in correct order
    messages_data = {
        "messages": [
            {
                "role": "user",
                "content": "User message 1",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            {
                "role": "assistant",
                "content": "Assistant response",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            {
                "role": "user",
                "content": "User message 2",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        ]
    }

    response = requests.post(f"{BASE_URL}/api/v1/sessions/{session_id}/messages", headers=headers, json=messages_data)
    print(f"Save messages status: {response.status_code}")

    # Get messages and check order
    response = requests.get(f"{BASE_URL}/api/v1/sessions/{session_id}/messages", headers=headers)
    print(f"Get messages status: {response.status_code}")

    if response.status_code == 200:
        messages = response.json()
        print(f"Got {len(messages)} messages:")

        expected_order = ["user", "assistant", "user"]
        actual_order = [msg['role'] for msg in messages]

        print(f"Expected order: {expected_order}")
        print(f"Actual order:   {actual_order}")

        if actual_order == expected_order:
            print("✅ Message order is CORRECT!")
        else:
            print("❌ Message order is WRONG!")

        for i, msg in enumerate(messages):
            print(f"  {i+1}. {msg['role']}: {msg['content']}")
    else:
        print(f"❌ Failed to get messages: {response.text}")

    # Cleanup
    requests.delete(f"{BASE_URL}/api/v1/sessions/{session_id}", headers=headers)
    requests.delete(f"{BASE_URL}/api/v1/admin/users/{user_id}", headers=headers)

if __name__ == "__main__":
    test_message_order()