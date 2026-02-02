#!/usr/bin/env python3
"""
验证文档切片 API 返回格式的诊断脚本
"""
import requests
import json
import sys

# 配置
API_BASE = "http://localhost:18080/api/v1"
# 替换为实际的 token
TOKEN = "your-token-here"
KB_ID = "042240fe-1f48-4b3a-b8f6-5b85754837b7"
DOC_ID = "688f6b87-1a33-4728-8b93-486043875ede"

def test_chunks_api():
    """测试文档切片接口"""
    url = f"{API_BASE}/knowledge/bases/{KB_ID}/documents/{DOC_ID}/chunks?offset=0"

    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }

    print("=" * 80)
    print("🔍 测试文档切片 API")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print()

    try:
        response = requests.get(url, headers=headers)
        print(f"📡 响应状态码: {response.status_code}")
        print(f"📡 响应头: {dict(response.headers)}")
        print()

        if response.status_code == 200:
            data = response.json()
            print("✅ 请求成功")
            print()
            print("📦 返回数据类型:", type(data))
            print("📦 是否为数组:", isinstance(data, list))
            print("📦 是否为字典:", isinstance(data, dict))
            print()

            if isinstance(data, dict):
                print("✅ 正确! 返回的是对象")
                print("📦 对象键:", list(data.keys()))
                print()
                if 'chunks' in data:
                    print(f"✅ 有 chunks 字段")
                    print(f"📦 chunks 类型: {type(data['chunks'])}")
                    print(f"📦 chunks 长度: {len(data['chunks'])}")
                    print()
                    if len(data['chunks']) > 0:
                        print("📦 第一个切片:", json.dumps(data['chunks'][0], indent=2, ensure_ascii=False))
                else:
                    print("❌ 错误! 没有 chunks 字段")
                    print("📦 完整数据:", json.dumps(data, indent=2, ensure_ascii=False))
            elif isinstance(data, list):
                print("❌ 错误! 返回的是数组而不是对象")
                print(f"📦 数组长度: {len(data)}")
                print()
                if len(data) > 0:
                    print("📦 第一个元素:", json.dumps(data[0], indent=2, ensure_ascii=False))
                print()
                print("⚠️  这说明后端代码未生效,需要重启后端服务!")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print("📦 错误信息:", response.text)

    except Exception as e:
        print(f"❌ 请求异常: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)

if __name__ == "__main__":
    if TOKEN == "your-token-here":
        print("❌ 请先修改脚本中的 TOKEN")
        sys.exit(1)

    test_chunks_api()
