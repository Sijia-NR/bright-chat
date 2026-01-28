#!/usr/bin/env python3
"""测试知识检索功能"""
import requests
import json

BASE_URL = "http://localhost:8080/api/v1"

# 登录
resp = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "pwd123"})
token = resp.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 获取知识库
resp = requests.get(f"{BASE_URL}/knowledge/bases", headers=headers)
kbs = resp.json()

if not kbs:
    print("❌ 没有知识库")
    exit(1)

kb = kbs[0]
print(f"✅ 知识库: {kb['name']}")
print(f"   ID: {kb['id']}")

# 测试检索
test_queries = [
    "Bright-Chat的主要功能",
    "如何部署Bright-Chat",
    "技术栈"
]

print("\n" + "="*60)
print("知识检索测试")
print("="*60)

for query in test_queries:
    print(f"\n🔍 查询: {query}")
    resp = requests.get(
        f"{BASE_URL}/knowledge/search",
        headers=headers,
        params={"query": query, "knowledge_base_ids": kb["id"], "top_k": 2}
    )

    if resp.status_code == 200:
        result = resp.json()
        results = result.get("results", [])
        print(f"   ✅ 返回 {len(results)} 个结果")

        if results:
            for i, r in enumerate(results):
                content = r['content'][:100].replace('\n', ' ')
                score = r.get('score', 0)
                print(f"      [{i+1}] 相似度:{score:.3f}")
                print(f"          {content}...")
    else:
        print(f"   ❌ 错误: {resp.status_code} - {resp.text}")

print("\n" + "="*60)
print("✅ 知识检索测试完成！")
print("="*60)
