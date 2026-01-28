"""
Mock Embedding 模型用于测试
Mock Embedding Model for Testing

避免下载真实模型，加快测试速度
"""
import numpy as np
from typing import List


class MockEmbeddingModel:
    """Mock Embedding 模型"""

    def __init__(self, dimension: int = 1024):
        """
        初始化Mock模型

        Args:
            dimension: 向量维度（默认1024，与BGE-large-zh-v1.5一致）
        """
        self.dimension = dimension
        self.call_count = 0
        np.random.seed(42)  # 固定随机种子以便测试

    def encode(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        编码文本为向量（返回固定但确定的伪随机向量）

        Args:
            texts: 待编码的文本列表
            **kwargs: 其他参数（batch_size, show_progress_bar等）

        Returns:
            向量列表
        """
        self.call_count += 1

        # 使用文本的哈希值作为种子，确保相同文本得到相同向量
        embeddings = []
        for text in texts:
            # 简单的哈希函数
            text_hash = hash(text) % (2**31)
            np.random.seed(text_hash)

            # 生成归一化的向量
            vector = np.random.rand(self.dimension)
            vector = vector / np.linalg.norm(vector)  # L2 归一化

            embeddings.append(vector.tolist())

        return embeddings

    def get_sentence_embedding_dimension(self) -> int:
        """获取向量维度"""
        return self.dimension


class MockRAGConfig:
    """Mock RAG 配置"""

    def __init__(self):
        """初始化Mock配置"""
        from tests.test_utils import cleanup_test_chroma

        self.embedding_model_name = "mock-bge-large-zh-v1.5"
        self.chromadb_host = "localhost"
        self.chromadb_port = 8001
        self.device = "cpu"

        # 创建Mock Embedding模型
        self._embedding_model = MockEmbeddingModel()

        # 初始化ChromaDB客户端（使用真实客户端）
        try:
            from rag.config import get_rag_config
            self.chroma_client = get_rag_config().chroma_client
        except:
            # 如果无法导入，使用本地持久化模式
            import chromadb
            from chromadb.config import Settings
            import tempfile
            import os

            temp_dir = tempfile.mkdtemp(prefix='chroma_test_')
            self.chroma_client = chromadb.PersistentClient(
                path=temp_dir,
                settings=Settings(anonymized_telemetry=False, allow_reset=True)
            )

    @property
    def embedding_model(self):
        """获取Mock Embedding模型"""
        return self._embedding_model

    def get_or_create_collection(self, name: str, metadata: dict = None):
        """获取或创建Collection"""
        return self.chroma_client.get_or_create_collection(name, metadata)

    def reset_collection(self, name: str):
        """重置Collection"""
        try:
            self.chroma_client.delete_collection(name)
        except:
            pass

    def health_check(self) -> bool:
        """健康检查"""
        try:
            self.chroma_client.heartbeat()
            return True
        except:
            return False
