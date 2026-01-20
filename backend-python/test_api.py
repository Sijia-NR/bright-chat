#!/usr/bin/env python3
"""
Test script for Bright-Chat API endpoints
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:18080"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_login():
    """Test login endpoint"""
    print("\n=== Testing Login Endpoint ===")
    data = {
        "username": "admin",
        "password": "pwd123"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Login successful!")
        print(f"Token: {result['token'][:50]}...")
        return result['token']
    else:
        print(f"Error: {response.text}")
        return None

def test_get_users(token):
    """Test get users endpoint"""
    print("\n=== Testing Get Users Endpoint ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/admin/users", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_create_session(token):
    """Test create session endpoint"""
    print("\n=== Testing Create Session Endpoint ===")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "title": "Test Session Python",
        "user_id": "d611c422-721f-4aaa-b6fd-10ecccb21f92"  # Admin user ID
    }
    response = requests.post(f"{BASE_URL}/api/v1/sessions", headers=headers, json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Session created: {result['id']}")
        return result['id']
    else:
        print(f"Error: {response.text}")
        return None

def test_get_sessions(token, user_id):
    """Test get sessions endpoint"""
    print("\n=== Testing Get Sessions Endpoint ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/sessions?user_id={user_id}", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_save_messages(token, session_id):
    """Test save messages endpoint"""
    print("\n=== Testing Save Messages Endpoint ===")
    headers = {"Authorization": f"Bearer {token}"}

    # Simple message data without complex escaping
    data = {
        "messages": [
            {
                "role": "user",
                "content": "Hello from test!",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        ]
    }

    print(f"Sending data: {json.dumps(data)}")
    response = requests.post(
        f"{BASE_URL}/api/v1/sessions/{session_id}/messages",
        headers=headers,
        json=data
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Messages saved successfully")
    else:
        print(f"Error: {response.text}")

def test_get_messages(token, session_id):
    """Test get messages endpoint"""
    print("\n=== Testing Get Messages Endpoint ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/sessions/{session_id}/messages", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def main():
    """Run all tests"""
    print("Starting Bright-Chat API Tests...")

    # Test health
    test_health()

    # Test login
    token = test_login()
    if not token:
        print("Login failed, exiting tests")
        return

    # Test admin endpoints
    test_get_users(token)

    # Test session endpoints
    session_id = test_create_session(token)
    if session_id:
        user_id = "d611c422-721f-4aaa-b6fd-10ecccb21f92"
        test_get_sessions(token, user_id)
        test_save_messages(token, session_id)
        test_get_messages(token, session_id)

    print("\n=== All Tests Completed ===")

if __name__ == "__main__":
    main()