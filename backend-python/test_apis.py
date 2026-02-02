#!/usr/bin/env python3
"""
API 接口测试脚本
"""

import requests
import json

API_BASE = "http://localhost:8080/api/v1"

# 登录
print("=== 1. 登录 ===")
resp = requests.post(f"{API_BASE}/auth/login", json={
    "username": "admin",
    "password": "pwd123"
})
resp.raise_for_status()
token = resp.json()["token"]
print(f"✅ 登录成功")

# 测试接口 1: 获取文档列表
print("\n=== 2. 测试 GET /api/v1/knowledge/bases/6f51c030-1ce0-44a1-adf6-ad5ee8d9c5c6/documents ===")
kb_id = "6f51c030-1ce0-44a1-adf6-ad5ee8d9c5c6"

try:
    resp = requests.get(
        f"{API_BASE}/knowledge/bases/{kb_id}/documents",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    docs = resp.json()
    print(f"✅ 接口 1 成功 - 返回 {len(docs)} 个文档")
    for doc in docs[:2]:
        print(f"   - {doc['filename']}: {doc['upload_status']}")
except Exception as e:
    print(f"❌ 接口 1 失败: {e}")

# 测试接口 2: 获取文档切片
print("\n=== 3. 测试 GET /api/v1/knowledge/bases/{kb_id}/documents/{doc_id}/chunks ===")
doc_id = "25d59850-9f44-400d-ad34-37d266bad8dd"

try:
    resp = requests.get(
        f"{API_BASE}/knowledge/bases/{kb_id}/documents/{doc_id}/chunks",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    chunks = resp.json()
    print(f"✅ 接口 2 成功 - 返回 {len(chunks.get('chunks', []))} 个切片")
except Exception as e:
    print(f"❌ 接口 2 失败: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"   响应: {e.response.text}")

print("\n=== 测试完成 ===")
