"""
测试工具类和辅助函数
Test utilities and helper functions
"""
import os
import sys
import tempfile
import pytest
from typing import List, Dict, Any, Optional
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDocumentCreator:
    """测试文档创建器"""

    @staticmethod
    def create_text_file(content: str, filename: str = "test.txt") -> str:
        """创建文本文件"""
        temp_dir = tempfile.mkdtemp(prefix='test_txt_')
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    @staticmethod
    def create_markdown_file(content: str, filename: str = "test.md") -> str:
        """创建Markdown文件"""
        return TestDocumentCreator.create_text_file(content, filename)

    @staticmethod
    def create_html_file(content: str, filename: str = "test.html") -> str:
        """创建HTML文件"""
        return TestDocumentCreator.create_text_file(content, filename)


class TestAssertions:
    """自定义断言"""

    @staticmethod
    def assert_valid_uuid(id_str: str):
        """验证UUID格式"""
        import uuid
        try:
            uuid.UUID(id_str)
        except ValueError:
            pytest.fail(f"Invalid UUID: {id_str}")

    @staticmethod
    def assert_knowledge_base_response(data: Dict[str, Any], expected_name: str = None):
        """验证知识库响应"""
        assert "id" in data, "Missing 'id' field"
        assert "name" in data, "Missing 'name' field"
        assert "user_id" in data, "Missing 'user_id' field"

        TestAssertions.assert_valid_uuid(data["id"])

        if expected_name:
            assert data["name"] == expected_name, f"Expected name '{expected_name}', got '{data['name']}'"

    @staticmethod
    def assert_document_response(data: Dict[str, Any]):
        """验证文档响应"""
        assert "id" in data, "Missing 'id' field"
        assert "knowledge_base_id" in data, "Missing 'knowledge_base_id' field"
        assert "filename" in data, "Missing 'filename' field"
        assert "upload_status" in data, "Missing 'upload_status' field"

        TestAssertions.assert_valid_uuid(data["id"])

    @staticmethod
    def assert_agent_response(data: Dict[str, Any]):
        """验证Agent响应"""
        assert "id" in data, "Missing 'id' field"
        assert "name" in data, "Missing 'name' field"
        assert "agent_type" in data, "Missing 'agent_type' field"

        TestAssertions.assert_valid_uuid(data["id"])


class MockEmbeddingModel:
    """模拟Embedding模型（用于测试）"""

    def __init__(self):
        self.dimension = 1024
        self.call_count = 0

    def encode(self, texts: List[str], **kwargs):
        """模拟编码，返回固定向量"""
        self.call_count += 1
        import numpy as np
        return np.random.rand(len(texts), self.dimension).tolist()


class TestKnowledgeBaseBuilder:
    """测试知识库构建器"""

    @staticmethod
    def build(
        name: str = "测试知识库",
        user_id: str = "test-user-001",
        description: str = None,
        embedding_model: str = "bge-large-zh-v1.5"
    ) -> Dict[str, Any]:
        """构建知识库数据"""
        import uuid
        return {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "user_id": user_id,
            "embedding_model": embedding_model,
            "chunk_size": 500,
            "chunk_overlap": 50,
            "is_active": True
        }


class TestAgentBuilder:
    """测试Agent构建器"""

    @staticmethod
    def build(
        name: str = "test_assistant",
        display_name: str = "测试助手",
        agent_type: str = "tool",
        tools: List[str] = None,
        user_id: str = "test-user-001"
    ) -> Dict[str, Any]:
        """构建Agent数据"""
        import uuid
        return {
            "id": str(uuid.uuid4()),
            "name": name,
            "display_name": display_name,
            "description": f"{display_name}的描述",
            "agent_type": agent_type,
            "system_prompt": "你是一个测试助手",
            "knowledge_base_ids": [],
            "tools": tools or ["calculator"],
            "config": {"temperature": 0.7, "max_steps": 10},
            "is_active": True,
            "created_by": user_id
        }


class DatabaseTestHelper:
    """数据库测试辅助类"""

    @staticmethod
    def cleanup_test_data(session, model_class, user_id: str = None):
        """清理测试数据"""
        from sqlalchemy import delete
        from app.models.knowledge_base import KnowledgeBase
        from app.models.agent import Agent

        if user_id:
            # 删除特定用户的测试数据
            session.execute(delete(KnowledgeBase).where(KnowledgeBase.user_id == user_id))
            session.execute(delete(Agent).where(Agent.created_by == user_id))
            session.commit()

    @staticmethod
    def create_test_user(session, username: str = "test_user"):
        """创建测试用户"""
        from app.models.user import User, UserRole
        import uuid
        from datetime import datetime

        user = User(
            id=str(uuid.uuid4()),
            username=username,
            password_hash="test_hash",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.now()
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


class ChromaDBTestHelper:
    """ChromaDB测试辅助类"""

    @staticmethod
    def cleanup_test_collections(config, prefix: str = "test_"):
        """清理测试集合"""
        try:
            collections = config.chroma_client.list_collections()
            for collection in collections:
                if collection.name.startswith(prefix):
                    config.chroma_client.delete_collection(collection.name)
        except Exception as e:
            # 忽略清理错误
            pass

    @staticmethod
    def verify_collection_exists(config, collection_name: str) -> bool:
        """验证集合是否存在"""
        try:
            collections = config.chroma_client.list_collections()
            return any(c.name == collection_name for c in collections)
        except:
            return False
