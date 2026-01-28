#!/usr/bin/env python3
"""
ChromaDB 快速重置工具（使用v2 API）
"""
import requests
import json

CHROMADB_URL = "http://localhost:8002"

def reset_chromadb():
    """重置ChromaDB的所有collections"""

    print("="*60)
    print("ChromaDB 快速重置")
    print("="*60)

    # 1. 列出所有collections
    print("\n1. 获取Collections列表...")
    list_url = f"{CHROMADB_URL}/api/v2/collections"
    resp = requests.get(list_url)

    if resp.status_code != 200:
        print(f"❌ 获取失败: {resp.status_code}")
        print(resp.text)
        return False

    data = resp.json()
    collections = data.get('collections', [])

    print(f"   发现 {len(collections)} 个collections")

    if len(collections) == 0:
        print("   ✅ 没有需要删除的collections")
        return True

    # 2. 删除所有collections
    print("\n2. 删除所有collections...")
    for col in collections:
        col_id = col.get('id')
        col_name = col.get('name', 'unknown')

        print(f"   删除: {col_name} (ID: {col_id})")

        delete_url = f"{CHROMADB_URL}/api/v2/collections/{col_id}"
        resp = requests.delete(delete_url)

        if resp.status_code in [200, 204]:
            print(f"      ✅ 成功")
        else:
            print(f"      ❌ 失败: {resp.status_code}")

    # 3. 验证
    print("\n3. 验证清理结果...")
    resp = requests.get(list_url)

    if resp.status_code == 200:
        data = resp.json()
        remaining = data.get('collections', [])
        if len(remaining) == 0:
            print("   ✅ 所有collections已清空")
        else:
            print(f"   ⚠️  还剩 {len(remaining)} 个collections")
    else:
        print("   ❌ 验证失败")

    print("\n" + "="*60)
    print("✅ ChromaDB重置完成！")
    print("="*60)
    print("\n下一步:")
    print("1. 重启后端服务（会自动创建新collection）")
    print("2. 重新上传知识库文档")
    print("3. 测试知识检索功能")

    return True

if __name__ == "__main__":
    reset_chromadb()
