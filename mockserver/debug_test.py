"""
调试测试脚本
"""
import requests
import json

# 测试语义大模型接口
url = "http://localhost:18063/lmp-cloud-ias-server/api/llm/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": "APP_KEY"
}

data = {
    "model": "BrightChat-General-v1",
    "messages": [
        {
            "role": "user",
            "content": "你好"
        }
    ],
    "stream": False
}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Content: {response.text}")

    if response.status_code == 200:
        print("✅ 接口调用成功")
    else:
        print("❌ 接口调用失败")

except Exception as e:
    print(f"❌ 请求异常: {e}")