#!/usr/bin/env python3
"""
知识库检索接口测试脚本
"""

import requests
import json

API_BASE = "http://localhost:8080/api/v1"

def test_search():
    """测试知识库搜索接口"""

    # 1. 登录获取 token
    print("=" * 60)
    print("步骤1: 登录")
    print("=" * 60)

    login_resp = requests.post(f"{API_BASE}/auth/login", json={
        "username": "admin",
        "password": "pwd123"
    })

    if login_resp.status_code != 200:
        print(f"❌ 登录失败: {login_resp.status_code}")
        return

    login_data = login_resp.json()
    token = login_data.get("token")  # ✅ 修复：字段名是 token 而不是 access_token
    print(f"✅ 登录成功")
    print(f"Token: {token[:30]}...")

    headers = {"Authorization": f"Bearer {token}"}

    # 2. 测试搜索（所有知识库）
    print("\n" + "=" * 60)
    print("步骤2: 搜索所有知识库")
    print("=" * 60)

    search_resp = requests.get(
        f"{API_BASE}/knowledge/search",
        headers=headers,
        params={
            "query": "接口文档",
            "top_k": 5
        }
    )

    if search_resp.status_code != 200:
        print(f"❌ 搜索失败: {search_resp.status_code}")
        print(search_resp.text)
        return

    data = search_resp.json()
    print(f"✅ 搜索成功")
    print(f"查询: {data['query']}")
    print(f"找到 {data['total']} 个结果\n")

    for i, result in enumerate(data['results'], 1):
        print(f"结果 {i}:")
        print(f"  相似度: {result['similarity']}")
        print(f"  距离: {result['distance']}")
        print(f"  文件: {result['metadata']['filename']}")
        print(f"  内容预览: {result['content'][:80]}...")
        print()

    # 3. 测试搜索指定知识库
    print("=" * 60)
    print("步骤3: 搜索指定知识库")
    print("=" * 60)

    # 获取用户的知识库列表
    kb_resp = requests.get(
        f"{API_BASE}/knowledge/bases",
        headers=headers
    )

    if kb_resp.status_code == 200:
        kb_list = kb_resp.json()
        if kb_list:
            kb_id = kb_list[0]['id']
            kb_name = kb_list[0]['name']

            print(f"使用知识库: {kb_name} (ID: {kb_id})\n")

            search_resp2 = requests.get(
                f"{API_BASE}/knowledge/search",
                headers=headers,
                params={
                    "query": "API",
                    "knowledge_base_ids": kb_id,
                    "top_k": 3
                }
            )

            if search_resp2.status_code == 200:
                data2 = search_resp2.json()
                print(f"✅ 搜索成功，找到 {data2['total']} 个结果\n")

                for i, result in enumerate(data2['results'], 1):
                    print(f"结果 {i}:")
                    print(f"  相似度: {result['similarity']}")
                    print(f"  内容: {result['content'][:80]}...")
                    print()
            else:
                print(f"❌ 搜索失败: {search_resp2.status_code}")
        else:
            print("⚠️  没有可用的知识库")
    else:
        print(f"❌ 获取知识库列表失败: {kb_resp.status_code}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_search()
