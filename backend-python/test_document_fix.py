#!/usr/bin/env python3
"""
测试文档处理修复效果
"""
import requests
import json
import time
import io
from pathlib import Path

BASE_URL = "http://localhost:8080/api/v1"

def test_fixes():
    """测试所有修复"""

    print("="*60)
    print("测试文档处理修复")
    print("="*60)

    # 1. 登录
    print("\n1. 登录...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "pwd123"
    })

    if resp.status_code != 200:
        print(f"❌ 登录失败: {resp.status_code}")
        return False

    token = resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 登录成功")

    # 2. 创建测试知识库
    print("\n2. 创建测试知识库...")
    resp = requests.post(f"{BASE_URL}/knowledge/groups", headers=headers, json={
        "name": f"TestGroup_{int(time.time())}"
    })

    if resp.status_code != 200:
        print(f"❌ 创建分组失败: {resp.status_code}")
        return False

    group = resp.json()

    resp = requests.post(f"{BASE_URL}/knowledge/bases", headers=headers, json={
        "name": f"TestKB_{int(time.time())}",
        "group_id": group["id"]
    })

    if resp.status_code != 200:
        print(f"❌ 创建知识库失败: {resp.status_code}")
        return False

    kb = resp.json()
    kb_id = kb["id"]
    print(f"✅ 知识库创建成功: {kb['name']} (ID: {kb_id})")

    # 3. 测试同步处理（新功能）
    print("\n3. 测试同步文档处理...")
    test_content = '''
Bright-Chat 是一个 AI 聊天应用，支持以下功能：

1. 用户管理和权限控制
   - 支持多用户登录
   - 管理员权限管理
   - 用户CRUD操作

2. 知识库管理
   - 支持多种文档格式上传
   - 自动分块和向量化
   - 语义检索功能

3. Agent 数字员工
   - 支持自定义Agent
   - 工具调用能力
   - 知识库集成

技术栈：React 19, Python FastAPI, MySQL, ChromaDB
'''

    # 创建临时文件
    temp_file = Path("/tmp/test_sync_doc.txt")
    temp_file.write_text(test_content, encoding="utf-8")

    with open(temp_file, "rb") as f:
        files = {"file": ("test.txt", f, "text/plain")}
        params = {
            "sync": "true",  # 使用同步处理
            "chunk_size": 200,
            "chunk_overlap": 50
        }

        resp = requests.post(
            f"{BASE_URL}/knowledge/bases/{kb_id}/documents",
            headers=headers,
            files=files,
            params=params
        )

    if resp.status_code != 200:
        print(f"❌ 文档上传失败: {resp.status_code}")
        print(resp.text)
        return False

    doc = resp.json()
    doc_id = doc["id"]
    print(f"✅ 文档上传成功: {doc['filename']}")
    print(f"   状态: {doc['upload_status']}")
    print(f"   Chunks: {doc.get('chunk_count', 'N/A')}")

    # 4. 验证向量化结果
    print("\n4. 验证向量化结果...")

    if doc['upload_status'] == 'completed':
        print(f"✅ 文档已成功向量化: {doc['chunk_count']} 个chunks")

        # 测试知识检索
        print("\n5. 测试知识检索...")
        test_queries = [
            "Bright-Chat有哪些功能？",
            "使用什么技术栈？",
            "支持数据库吗？"
        ]

        for query in test_queries:
            resp = requests.get(
                f"{BASE_URL}/knowledge/search",
                headers=headers,
                params={
                    "query": query,
                    "knowledge_base_ids": [kb_id],
                    "top_k": 2
                }
            )

            if resp.status_code == 200:
                results = resp.json().get("results", [])
                print(f"\n查询: {query}")
                print(f"✅ 返回 {len(results)} 个结果")

                if results:
                    for i, r in enumerate(results[:1], 1):
                        content = r.get("content", "")[:100]
                        score = r.get("score", 0)
                        print(f"   结果{i} (相似度:{score:.3f}): {content}...")
            else:
                print(f"\n查询: {query}")
                print(f"❌ 检索失败: {resp.status_code}")

    elif doc['upload_status'] == 'error':
        print(f"❌ 文档处理失败: {doc.get('error_message', 'Unknown error')}")
        return False
    else:
        print(f"⚠️  文档状态: {doc['upload_status']}")

    # 6. 测试系统健康检查
    print("\n6. 测试系统健康检查...")
    resp = requests.get(f"{BASE_URL}/system/health", headers=headers)

    if resp.status_code == 200:
        health = resp.json()
        print(f"✅ 系统状态: {health['status']}")
        print(f"\n组件状态:")
        for component, status in health['components'].items():
            comp_status = status.get('status', 'unknown')
            print(f"  - {component}: {comp_status}")
            if comp_status == 'healthy':
                if 'vector_count' in status:
                    print(f"    向量数: {status['vector_count']}")
                if 'dimension' in status:
                    print(f"    模型维度: {status['dimension']}")
    else:
        print(f"❌ 健康检查失败: {resp.status_code}")

    print("\n" + "="*60)
    print("✅ 所有测试完成！")
    print("="*60)

    # 清理测试数据
    print("\n清理测试数据...")
    requests.delete(f"{BASE_URL}/knowledge/bases/{kb_id}", headers=headers)
    print("✅ 测试知识库已删除")

    return True

if __name__ == "__main__":
    try:
        success = test_fixes()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
