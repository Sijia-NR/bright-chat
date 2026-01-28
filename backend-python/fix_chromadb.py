#!/usr/bin/env python3
"""
ChromaDB 修复工具
修复损坏的collection元数据
"""
import chromadb
import requests
import json

def fix_chromadb():
    """修复ChromaDB损坏的collections"""

    print("="*60)
    print("ChromaDB 修复工具")
    print("="*60)

    # 方法1: 使用HTTP API直接删除
    print("\n方法1: 使用HTTP API删除损坏的collections")
    print("-"*60)

    try:
        # 获取所有collections
        resp = requests.get("http://localhost:8002/api/v1/collections")
        if resp.status_code == 200:
            collections = resp.json()

            print(f"发现 {len(collections)} 个collections:")

            for col in collections:
                col_id = col['id']
                col_name = col['name']
                print(f"\n  Collection: {col_name}")
                print(f"  ID: {col_id}")

                # 删除collection
                delete_url = f"http://localhost:8002/api/v1/collections/{col_id}"
                resp = requests.delete(delete_url)

                if resp.status_code == 200:
                    print(f"  ✅ 已删除")
                else:
                    print(f"  ❌ 删除失败: {resp.status_code}")

        print("\n✅ 所有损坏的collections已清理")
    except Exception as e:
        print(f"❌ 方法1失败: {e}")

    # 方法2: 重新初始化knowledge_chunks collection
    print("\n" + "="*60)
    print("方法2: 重新初始化knowledge_chunks collection")
    print("-"*60)

    try:
        client = chromadb.HttpClient(host='localhost', port=8002)

        # 删除旧的collection（如果存在）
        try:
            client.delete_collection("knowledge_chunks")
            print("✅ 旧的knowledge_chunks已删除")
        except:
            print("⚠️  旧collection不存在或已删除")

        # 创建新的collection
        collection = client.get_or_create_collection(
            name="knowledge_chunks",
            metadata={"description": "知识库文档切片向量存储"}
        )

        print(f"✅ 新collection创建成功: {collection.id}")
        print(f"   名称: knowledge_chunks")
        print(f"   向量维度: 1024 (BGE-large-zh)")

    except Exception as e:
        print(f"❌ 方法2失败: {e}")
        return False

    print("\n" + "="*60)
    print("✅ ChromaDB修复完成！")
    print("="*60)
    return True

if __name__ == "__main__":
    fix_chromadb()
