#!/usr/bin/env python3
"""
测试文档切片分页 API
验证是否正确返回 total_count 和分页数据
"""

import requests
import json

API_BASE = "http://localhost:18080/api/v1"
# 替换为实际的 knowledge_base_id 和 document_id
KB_ID = "042240fe-1f48-4b3a-b8f6-5b85754837b7"
DOC_ID = "bc34ecda-354a-4cfc-808a-b349f1348d01"

# 需要先登录获取 token
LOGIN_URL = f"{API_BASE}/auth/login"

def test_chunks_api():
    print("=" * 60)
    print("测试文档切片分页 API")
    print("=" * 60)

    # 1. 登录
    print("\n1. 登录...")
    login_resp = requests.post(LOGIN_URL, json={
        "username": "admin",
        "password": "pwd123"
    })

    if login_resp.status_code != 200:
        print(f"❌ 登录失败: {login_resp.status_code}")
        print(login_resp.text)
        return

    token = login_resp.json().get("access_token")
    print(f"✅ 登录成功, token: {token[:20]}...")

    headers = {"Authorization": f"Bearer {token}"}

    # 2. 获取文档信息
    print(f"\n2. 获取文档信息 (doc_id: {DOC_ID})...")
    doc_url = f"{API_BASE}/knowledge/bases/{KB_ID}/documents/{DOC_ID}"
    doc_resp = requests.get(doc_url, headers=headers)

    if doc_resp.status_code == 200:
        doc_data = doc_resp.json()
        print(f"✅ 文档信息:")
        print(f"   - 文件名: {doc_data.get('filename')}")
        print(f"   - 切片数: {doc_data.get('chunk_count')}")
        print(f"   - 状态: {doc_data.get('upload_status')}")
    else:
        print(f"❌ 获取文档失败: {doc_resp.status_code}")
        print(doc_resp.text)
        return

    # 3. 测试分页 - 第一页
    print(f"\n3. 测试分页 API (第一页, offset=0, limit=10)...")
    chunks_url = f"{API_BASE}/knowledge/bases/{KB_ID}/documents/{DOC_ID}/chunks?offset=0&limit=10"
    print(f"   URL: {chunks_url}")

    chunks_resp = requests.get(chunks_url, headers=headers)

    if chunks_resp.status_code != 200:
        print(f"❌ 请求失败: {chunks_resp.status_code}")
        print(chunks_resp.text)
        return

    chunks_data = chunks_resp.json()
    print(f"\n✅ API 响应:")
    print(json.dumps(chunks_data, indent=2, ensure_ascii=False))

    print(f"\n📊 分页信息:")
    print(f"   - document_id: {chunks_data.get('document_id')}")
    print(f"   - filename: {chunks_data.get('filename')}")
    print(f"   - total_count: {chunks_data.get('total_count')}")
    print(f"   - returned_count: {chunks_data.get('returned_count')}")
    print(f"   - offset: {chunks_data.get('offset')}")
    print(f"   - limit: {chunks_data.get('limit')}")

    chunks_list = chunks_data.get('chunks', [])
    print(f"\n📦 返回的切片数量: {len(chunks_list)}")
    if chunks_list:
        print(f"   第一个切片索引: {chunks_list[0].get('chunk_index')}")
        print(f"   最后一个切片索引: {chunks_list[-1].get('chunk_index')}")

    # 4. 测试第二页
    print(f"\n4. 测试分页 API (第二页, offset=10, limit=10)...")
    chunks_url2 = f"{API_BASE}/knowledge/bases/{KB_ID}/documents/{DOC_ID}/chunks?offset=10&limit=10"
    chunks_resp2 = requests.get(chunks_url2, headers=headers)

    if chunks_resp2.status_code == 200:
        chunks_data2 = chunks_resp2.json()
        print(f"✅ 第二页响应:")
        print(f"   - total_count: {chunks_data2.get('total_count')}")
        print(f"   - returned_count: {chunks_data2.get('returned_count')}")
        print(f"   - 切片数量: {len(chunks_data2.get('chunks', []))}")

        if chunks_data2.get('chunks'):
            print(f"   第一个切片索引: {chunks_data2['chunks'][0].get('chunk_index')}")
    else:
        print(f"❌ 第二页请求失败: {chunks_resp2.status_code}")

    # 5. 验证
    print(f"\n5. 验证结果:")
    total_count = chunks_data.get('total_count', 0)
    returned_count = chunks_data.get('returned_count', 0)
    doc_chunk_count = doc_data.get('chunk_count', 0)

    print(f"   文档表中的 chunk_count: {doc_chunk_count}")
    print(f"   API 返回的 total_count: {total_count}")
    print(f"   第一页返回的切片数: {returned_count}")

    if total_count == 0:
        print(f"\n❌ 问题: total_count 为 0!")
        print(f"   这就是为什么分页组件没有显示的原因。")
    elif total_count != doc_chunk_count:
        print(f"\n⚠️  警告: total_count ({total_count}) 与文档表的 chunk_count ({doc_chunk_count}) 不一致")
    else:
        print(f"\n✅ 数据一致!")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_chunks_api()
