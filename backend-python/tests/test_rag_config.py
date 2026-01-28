"""
RAG 配置测试
Test RAG Configuration
"""
import pytest
import os
import tempfile
from pathlib import Path


@pytest.mark.rag
@pytest.mark.unit
class TestRAGConfig:
    """RAG配置测试"""

    def test_config_initialization(self):
        """测试配置初始化"""
        # 这里需要能够正常导入模块
        try:
            from rag.config import RAGConfig
            config = RAGConfig()
            assert config is not None
        except ImportError:
            pytest.skip("RAG模块未安装")

    def test_chromadb_client_creation(self):
        """测试ChromaDB客户端创建"""
        try:
            from rag.config import RAGConfig
            config = RAGConfig()
            assert config.chroma_client is not None
        except ImportError:
            pytest.skip("RAG模块未安装")

    def test_get_or_create_collection(self):
        """测试获取或创建Collection"""
        try:
            from rag.config import RAGConfig
            config = RAGConfig()

            # 创建测试集合
            collection = config.get_or_create_collection(
                name="test_collection",
                metadata={"hnsw:space": "cosine"}
            )

            assert collection is not None
            assert collection.name == "test_collection"

            # 清理
            config.reset_collection("test_collection")

        except ImportError:
            pytest.skip("RAG模块未安装")

    def test_health_check(self):
        """测试健康检查"""
        try:
            from rag.config import RAGConfig
            config = RAGConfig()
            is_healthy = config.health_check()

            # 应该返回布尔值
            assert isinstance(is_healthy, bool)

        except ImportError:
            pytest.skip("RAG模块未安装")


@pytest.mark.rag
@pytest.mark.unit
class TestEmbeddingModel:
    """Embedding模型测试"""

    def test_embedding_model_loading(self):
        """测试Embedding模型加载"""
        try:
            from rag.config import RAGConfig
            config = RAGConfig()

            # 第一次访问时加载模型
            model = config.embedding_model
            assert model is not None
            assert hasattr(model, 'encode')

            # 测试编码功能
            import numpy as np
            embeddings = model.encode(["测试文本"])
            assert embeddings is not None
            assert len(embeddings) == 1
            assert len(embeddings[0]) > 0

        except ImportError:
            pytest.skip("RAG模块未安装")

    def test_embedding_dimension(self):
        """测试Embedding维度"""
        try:
            from rag.config import RAGConfig
            config = RAGConfig()

            model = config.embedding_model
            embeddings = model.encode(["测试"])
            dimension = len(embeddings[0])

            # BGE-large-zh-v1.5 的维度应该是 1024
            assert dimension == 1024, f"Expected dimension 1024, got {dimension}"

        except ImportError:
            pytest.skip("RAG模块未安装")


@pytest.mark.rag
@pytest.mark.unit
class TestRAGConfigConstants:
    """RAG配置常量测试"""

    def test_supported_file_types(self):
        """测试支持的文件类型"""
        try:
            from rag.config import SUPPORTED_FILE_TYPES

            # 验证文件类型配置
            assert 'pdf' in SUPPORTED_FILE_TYPES
            assert 'word' in SUPPORTED_FILE_TYPES
            assert 'text' in SUPPORTED_FILE_TYPES
            assert 'html' in SUPPORTED_FILE_TYPES

        except ImportError:
            pytest.skip("RAG模块未安装")

    def test_embedding_models_config(self):
        """测试Embedding模型配置"""
        try:
            from rag.config import EMBEDDING_MODELS

            # 验证模型配置
            assert 'bge-large-zh-v1.5' in EMBEDDING_MODELS
            assert EMBEDDING_MODELS['bge-large-zh-v1.5']['dimension'] == 1024

        except ImportError:
            pytest.skip("RAG模块未安装")

    def test_collection_name(self):
        """测试Collection名称"""
        try:
            from rag.config import KNOWLEDGE_COLLECTION

            assert KNOWLEDGE_COLLECTION == "knowledge_chunks"

        except ImportError:
            pytest.skip("RAG模块未安装")
