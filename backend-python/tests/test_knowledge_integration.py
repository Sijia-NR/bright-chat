"""
知识库集成完整测试
测试Agent与知识库的完整集成流程
"""
import requests
import time
import json

BASE_URL = "http://localhost:8080/api/v1"

def get_admin_token():
    """获取admin token"""
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "pwd123"
    })
    return resp.json()["token"]

def test_complete_knowledge_integration():
    """完整的知识库集成测试"""
    print("\n" + "="*80)
    print("知识库集成完整测试")
    print("="*80)

    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 步骤1: 创建知识库分组
    print("\n步骤1: 创建知识库分组")
    resp = requests.post(
        f"{BASE_URL}/knowledge/groups",
        headers=headers,
        json={"name": "测试分组", "description": "Agent测试用"}
    )
    if resp.status_code == 200:
        group_id = resp.json()["id"]
        print(f"✅ 分组创建成功: {group_id}")
    else:
        # 使用现有分组
        resp = requests.get(f"{BASE_URL}/knowledge/groups", headers=headers)
        groups = resp.json() if isinstance(resp.json(), list) else []
        if groups:
            group_id = groups[0]["id"]
            print(f"✅ 使用现有分组: {group_id}")
        else:
            print("❌ 无法获取分组")
            return

    # 步骤2: 创建知识库
    print("\n步骤2: 创建知识库")
    kb_data = {
        "group_id": group_id,
        "name": f"Agent知识库_{int(time.time())}",
        "description": "用于Agent测试的知识库",
        "embedding_model": "bge-large-zh-v1.5",
        "chunk_size": 500,
        "chunk_overlap": 50
    }
    resp = requests.post(
        f"{BASE_URL}/knowledge/bases",
        headers=headers,
        json=kb_data
    )
    if resp.status_code == 200:
        kb = resp.json()
        kb_id = kb["id"]
        print(f"✅ 知识库创建成功: {kb['name']} (ID: {kb_id})")
    else:
        print(f"❌ 知识库创建失败: {resp.status_code} - {resp.text}")
        return

    # 步骤3: 上传测试文档
    print("\n步骤3: 上传测试文档")
    test_content = """
Bright-Chat 项目介绍

Bright-Chat 是一个全栈AI聊天应用工作台，具有以下核心特性：

1. 用户管理
   - 支持管理员和普通用户角色
   - 用户注册、登录、权限管理
   - 基于JWT的身份验证

2. 知识库功能
   - 支持PDF、Word、Markdown等多种文档格式
   - 自动文档切片和向量化
   - 基于BGE模型的语义检索
   - 使用ChromaDB存储向量

3. Agent数字员工
   - 支持自定义Agent配置
   - 工具调用能力（计算器、时间查询等）
   - 知识库集成
   - 流式对话响应

4. 技术架构
   - 前端：React 19 + TypeScript + Vite 6
   - 后端：Python 3.12 + FastAPI + SQLAlchemy
   - 数据库：MySQL (用户数据) + ChromaDB (向量数据)
   - 向量模型：BGE-large-zh-v1.5 (1024维)

5. 部署方式
   - 支持Docker容器化部署
   - 支持本地开发环境
   - 支持生产环境Nginx部署
"""

    # 创建临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_file = f.name

    try:
        with open(temp_file, 'rb') as f:
            resp = requests.post(
                f"{BASE_URL}/knowledge/bases/{kb_id}/documents",
                headers=headers,
                files={"file": ("BrightChat介绍.txt", f, "text/plain")}
            )

        if resp.status_code == 200:
            doc = resp.json()
            doc_id = doc["id"]
            print(f"✅ 文档上传成功: {doc['filename']} (ID: {doc_id})")

            # 等待文档处理
            print("⏳ 等待文档处理...")
            for i in range(30):
                time.sleep(1)
                resp = requests.get(
                    f"{BASE_URL}/knowledge/bases/{kb_id}/documents/{doc_id}",
                    headers=headers
                )
                if resp.status_code == 200:
                    doc_info = resp.json()
                    status = doc_info.get("upload_status", "")
                    if status == "completed":
                        chunk_count = doc_info.get("chunk_count", 0)
                        print(f"✅ 文档处理完成，生成 {chunk_count} 个切片")
                        break
                    elif status == "failed":
                        print(f"❌ 文档处理失败")
                        break
            else:
                print("⚠️  文档处理超时")
        else:
            print(f"❌ 文档上传失败: {resp.status_code} - {resp.text}")
            return
    finally:
        import os
        os.unlink(temp_file)

    # 步骤4: 测试知识检索
    print("\n步骤4: 测试知识检索")
    test_queries = [
        "Bright-Chat有哪些功能？",
        "使用什么技术栈？",
        "支持哪些文档格式？"
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

        print(f"\n查询: {query}")
        if resp.status_code == 200:
            results = resp.json()
            result_count = len(results.get("results", []))
            print(f"  ✅ 找到 {result_count} 个结果")
            if result_count > 0:
                for i, r in enumerate(results["results"][:2], 1):
                    content = r.get("content", "")[:120]
                    print(f"    {i}. {content}...")
        else:
            print(f"  ❌ 检索失败: {resp.status_code}")

    # 步骤5: 创建启用知识库的Agent
    print("\n步骤5: 创建启用知识库的Agent")
    agent_data = {
        "name": f"kb_agent_{int(time.time())}",
        "display_name": "知识库助手",
        "description": "能够检索知识库的Agent",
        "agent_type": "rag",
        "tools": ["knowledge_search"],
        "enable_knowledge": True
    }
    resp = requests.post(
        f"{BASE_URL}/agents/",
        headers=headers,
        json=agent_data
    )

    if resp.status_code == 200:
        agent = resp.json()
        agent_id = agent["id"]
        print(f"✅ Agent创建成功: {agent['display_name']} (ID: {agent_id})")
    else:
        print(f"❌ Agent创建失败: {resp.status_code} - {resp.text}")
        return

    # 步骤6: 测试Agent对话（带知识库）
    print("\n步骤6: 测试Agent对话（带知识库）")
    chat_request = {
        "query": "Bright-Chat支持哪些文档格式？",
        "stream": False,
        "knowledge_base_ids": [kb_id]
    }

    resp = requests.post(
        f"{BASE_URL}/agents/{agent_id}/chat",
        headers=headers,
        json=chat_request,
        stream=True
    )

    print(f"问题: {chat_request['query']}")
    if resp.status_code == 200:
        print("✅ Agent对话成功")
        # 收集完整响应
        full_response = ""
        for line in resp.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data:'):
                    data_str = line_text[5:].strip()
                    if data_str == '[DONE]':
                        break
                    try:
                        event = json.loads(data_str)
                        if event.get('type') == 'complete':
                            output = event.get('output', '')
                            full_response = output
                            print(f"回答: {output[:200]}...")
                    except:
                        pass
    else:
        print(f"❌ Agent对话失败: {resp.status_code}")

    print("\n" + "="*80)
    print("✅ 知识库集成测试完成")
    print("="*80)

if __name__ == "__main__":
    test_complete_knowledge_integration()
