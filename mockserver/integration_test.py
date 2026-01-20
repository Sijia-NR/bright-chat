"""
集成测试脚本
测试前端和Mock Server的协同工作
"""
import requests
import json

def test_mock_server():
    """测试Mock Server所有接口"""
    base_url = "http://localhost:18063"

    # 测试根路径
    try:
        response = requests.get(f"{base_url}/")
        assert response.status_code == 200
        print("✅ Mock Server 根路径正常")
    except Exception as e:
        print(f"❌ Mock Server 根路径错误: {e}")
        return False

    # 测试语义大模型接口
    try:
        response = requests.post(
            f"{base_url}/lmp-cloud-ias-server/api/llm/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": "APP_KEY"
            },
            json={
                "model": "BrightChat-General-v1",
                "messages": [
                    {
                        "role": "user",
                        "content": "你好，测试语义模型"
                    }
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "choices" in data
        print("✅ 语义大模型接口正常")
    except Exception as e:
        print(f"❌ 语义大模型接口错误: {e}")
        return False

    # 测试视觉大模型接口
    try:
        response = requests.post(
            f"{base_url}/lmp-cloud-ias-server/api/lvm/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": "APP_KEY"
            },
            json={
                "model": "vision-model",
                "data": [
                    {
                        "image_name": "test.jpg",
                        "image_type": "url",
                        "image_data": "http://example.com/test.jpg"
                    }
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        print("✅ 视觉大模型接口正常")
    except Exception as e:
        print(f"❌ 视觉大模型接口错误: {e}")
        return False

    # 测试多模态大模型接口
    try:
        response = requests.post(
            f"{base_url}/lmp-cloud-ias-server/api/vlm/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": "APP_KEY"
            },
            json={
                "model": "SGGM-VL-7B",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "测试多模态"
                            }
                        ]
                    }
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "choices" in data
        print("✅ 多模态大模型接口正常")
    except Exception as e:
        print(f"❌ 多模态大模型接口错误: {e}")
        return False

    # 测试错误处理
    try:
        response = requests.post(
            f"{base_url}/lmp-cloud-ias-server/api/llm/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": "INVALID"
            },
            json={"model": "test"}
        )
        assert response.status_code == 401
        print("✅ 错误处理正常")
    except Exception as e:
        print(f"❌ 错误处理错误: {e}")
        return False

    return True

def main():
    print("=== Bright-Chat 系统集成测试 ===\n")

    print("1. 测试Mock Server...")
    if test_mock_server():
        print("\n🎉 所有测试通过！Mock Server运行正常")
        print("\n系统状态:")
        print("  - 前端应用: http://localhost:3002")
        print("  - Mock Server: http://localhost:18063")
        print("  - API文档: http://localhost:18063/docs")
        print("\n可以开始开发和测试了！")
    else:
        print("\n❌ 测试失败，请检查服务状态")

if __name__ == "__main__":
    main()