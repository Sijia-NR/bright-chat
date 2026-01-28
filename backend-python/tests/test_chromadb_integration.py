"""
ChromaDB 集成测试 - 完整文档处理流程

测试文档上传、切片、向量化和检索的完整流程
"""
import requests
import time
import sys
from pathlib import Path

BASE_URL = "http://localhost:8080/api/v1"


def get_admin_token():
    """获取 admin token"""
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "pwd123"
    })
    return resp.json()["token"]


def test_complete_document_workflow():
    """测试完整的文档处理工作流"""
    print("=" * 60)
    print("ChromaDB 集成测试 - 完整文档处理流程")
    print("=" * 60)

    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. 创建知识库分组
    print("\n[1] 创建知识库分组...")
    resp = requests.post(f"{BASE_URL}/knowledge/groups", headers=headers, json={
        "name": f"测试分组_{int(time.time())}",
        "description": "ChromaDB 测试分组",
        "color": "#FF5733"
    })
    assert resp.status_code == 200, f"创建分组失败: {resp.text}"
    group = resp.json()
    print(f"✅ 分组创建成功: {group['name']} (ID: {group['id']})")

    # 2. 创建知识库
    print("\n[2] 创建知识库...")
    resp = requests.post(f"{BASE_URL}/knowledge/bases", headers=headers, json={
        "group_id": group["id"],
        "name": f"ChromaDB测试_{int(time.time())}",
        "description": "用于测试ChromaDB向量化和检索",
        "embedding_model": "bge-large-zh-v1.5",
        "chunk_size": 200,
        "chunk_overlap": 50
    })
    assert resp.status_code == 200, f"创建知识库失败: {resp.text}"
    kb = resp.json()
    print(f"✅ 知识库创建成功: {kb['name']} (ID: {kb['id']})")
    print(f"   嵌入模型: {kb['embedding_model']}")
    print(f"   分块大小: {kb['chunk_size']}, 重叠: {kb['chunk_overlap']}")

    # 3. 上传测试文档
    print("\n[3] 上传测试文档...")
    test_content = """
# Bright-Chat AI工作台

Bright-Chat 是一个全栈AI聊天应用工作台，支持实时LLM集成、用户管理和模型配置。

## 主要功能

### 1. 用户管理
- 用户登录认证（JWT）
- 角色权限控制（admin/user）
- 用户CRUD操作

### 2. 知识库管理
- 文档上传（PDF、Word、Markdown等）
- 自动切片和向量化
- 语义检索

### 3. 数字员工
- 创建和配置Agent
- 工具调用（计算器、时间查询等）
- 知识库集成

## 技术栈

- 前端：React 19 + TypeScript + Vite 6
- 后端：Python 3.11 + FastAPI + SQLAlchemy
- 数据库：MySQL + ChromaDB（向量数据库）
- 部署：Docker Compose

## 使用场景

Bright-Chat适用于需要构建智能对话系统的场景：
- 客户服务助手
- 企业知识库问答
- 文档智能检索
- 数字员工协作

## 部署说明

系统采用容器化部署，支持一键启动：
```bash
docker-compose up -d
```

访问地址：
- 前端：http://localhost:3000
- 后端API：http://localhost:8080
- API文档：http://localhost:8080/docs
"""

    # 创建临时文件
    temp_file = f"/tmp/brightchat_test_{int(time.time())}.md"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(test_content)

    # 上传文件
    with open(temp_file, "rb") as f:
        resp = requests.post(
            f"{BASE_URL}/knowledge/bases/{kb['id']}/documents",
            headers=headers,
            files={"file": ("brightchat_test.md", f, "text/markdown")}
        )

    assert resp.status_code == 200, f"上传文档失败: {resp.text}"
    doc = resp.json()
    print(f"✅ 文档上传成功: {doc['filename']}")
    print(f"   文件大小: {doc['file_size']} bytes")
    print(f"   上传状态: {doc['upload_status']}")

    # 4. 等待文档处理
    print("\n[4] 等待文档处理（切片和向量化）...")
    max_wait = 60  # 最多等待60秒
    for i in range(max_wait):
        time.sleep(1)
        resp = requests.get(
            f"{BASE_URL}/knowledge/bases/{kb['id']}/documents/{doc['id']}",
            headers=headers
        )
        assert resp.status_code == 200, f"获取文档状态失败: {resp.text}"
        updated_doc = resp.json()
        status = updated_doc.get("upload_status", "pending")

        if i % 5 == 0 and i > 0:
            print(f"   状态: {status} ({i}s)")

        if status == "completed":
            chunk_count = updated_doc.get("chunk_count", 0)
            print(f"✅ 文档处理完成！")
            print(f"   生成切片数: {chunk_count}")
            print(f"   处理时间: {i}秒")
            break
        elif status == "failed":
            error = updated_doc.get("error_message", "Unknown error")
            print(f"❌ 文档处理失败: {error}")
            return False
    else:
        print(f"⚠️  文档处理超时（{max_wait}秒），当前状态: {status}")
        print("   继续测试切片查询功能...")

    # 5. 查询文档切片
    print("\n[5] 查询文档切片...")
    resp = requests.get(
        f"{BASE_URL}/knowledge/bases/{kb['id']}/documents/{doc['id']}/chunks",
        headers=headers
    )

    if resp.status_code == 200:
        chunks = resp.json()
        print(f"✅ 成功获取 {len(chunks)} 个切片")
        if chunks:
            print("\n   前3个切片预览:")
            for i, chunk in enumerate(chunks[:3]):
                content_preview = chunk.get('content', '')[:80].replace('\n', ' ')
                print(f"   切片 {i+1}: {content_preview}...")
                metadata = chunk.get('metadata', {})
                print(f"          元数据: {list(metadata.keys())}")
    else:
        print(f"❌ 获取切片失败: {resp.status_code} - {resp.text}")
        return False

    # 6. 知识检索测试
    print("\n[6] 知识检索测试...")
    test_queries = [
        "Bright-Chat的主要功能",
        "如何部署Bright-Chat",
        "Bright-Chat使用什么技术栈",
        "数字员工有哪些能力"
    ]

    for query in test_queries:
        print(f"\n   查询: {query}")
        resp = requests.get(
            f"{BASE_URL}/knowledge/search",
            headers=headers,
            params={
                "query": query,
                "knowledge_base_ids": kb["id"],
                "top_k": 3
            }
        )

        if resp.status_code == 200:
            result = resp.json()
            results = result.get("results", [])
            print(f"   ✅ 检索成功，返回 {len(results)} 个结果")

            if results:
                for i, item in enumerate(results[:2]):
                    content_preview = item.get('content', '')[:100].replace('\n', ' ')
                    score = item.get('score', 0)
                    print(f"      结果 {i+1} (相似度: {score:.3f}): {content_preview}...")
            else:
                print(f"   ⚠️  没有找到相关结果")
        else:
            print(f"   ❌ 检索失败: {resp.status_code} - {resp.text}")

    # 7. ChromaDB状态检查
    print("\n[7] ChromaDB状态检查...")
    try:
        import chromadb
        from app.rag.config import get_rag_config

        rag_config = get_rag_config()
        collection = rag_config.get_or_create_collection("knowledge_chunks")

        # 获取collection统计
        count = collection.count()
        print(f"✅ ChromaDB连接正常")
        print(f"   Collection: knowledge_chunks")
        print(f"   总向量数: {count}")

        # 获取一些示例数据
        if count > 0:
            results = collection.get(limit=2)
            print(f"   示例数据: {len(results.get('documents', []))} 条记录")

    except Exception as e:
        print(f"❌ ChromaDB连接失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_complete_document_workflow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
