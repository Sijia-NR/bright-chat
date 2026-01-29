"""
RAG 配置模块
RAG Configuration Module

配置 ChromaDB 客户端和 BGE Embedding 模型
Configure ChromaDB client and BGE Embedding model
"""
import os
import sys
import threading
import time
from typing import Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import logging

# 配置日志输出到 stdout，确保 docker logs 能捕获
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)

logger = logging.getLogger(__name__)


class RAGConfig:
    """RAG 配置类"""

    def __init__(
        self,
        chromadb_host: Optional[str] = None,
        chromadb_port: Optional[int] = None,
        embedding_model_name: str = "bge-large-zh-v1.5",
        device: str = "cpu",
        use_mock: bool = False,  # 新增：是否使用Mock模型
        model_path: Optional[str] = None,  # 新增：本地模型路径
        use_chromadb_embedding: bool = False  # 新增：使用 ChromaDB 自带向量模型
    ):
        """
        初始化 RAG 配置

        Args:
            chromadb_host: ChromaDB 服务器地址 (默认从环境变量读取)
            chromadb_port: ChromaDB 服务器端口 (默认从环境变量读取)
            embedding_model_name: Embedding 模型名称
            device: 运行设备 ("cpu" 或 "cuda")
            use_mock: 是否使用Mock模型（测试/离线环境）
            model_path: 本地模型路径（优先级高于模型名称）
            use_chromadb_embedding: 是否使用ChromaDB自带向量模型（推荐）
        """
        # ChromaDB 配置（仅使用容器模式）
        self.chromadb_host = chromadb_host or os.getenv("CHROMADB_HOST", "chromadb")
        self.chromadb_port = chromadb_port or int(os.getenv("CHROMADB_PORT", "8000"))

        # 连接到 ChromaDB 容器（强制使用 HttpClient，带重试机制）
        max_retries = 3
        retry_delay = 2

        # 设置环境变量禁用 telemetry
        os.environ["ANONYMIZED_TELEMETRY"] = "False"

        for attempt in range(max_retries):
            try:
                self.chroma_client = chromadb.HttpClient(
                    host=self.chromadb_host,
                    port=self.chromadb_port,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                # 测试连接
                self.chroma_client.heartbeat()
                logger.info(f"✅ ChromaDB 连接成功: {self.chromadb_host}:{self.chromadb_port}")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ ChromaDB 连接失败（尝试 {attempt + 1}/{max_retries}），{retry_delay}秒后重试...")
                    logger.debug(f"错误详情: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    logger.error(f"❌ ChromaDB 连接失败（已达最大重试次数 {max_retries}）")
                    logger.error(f"最后错误: {e}")
                    logger.error("请确保 ChromaDB 容器已启动: docker-compose up -d chromadb")
                    raise

        # Embedding 模型配置
        self.embedding_model_name = embedding_model_name
        self.device = device
        self.use_mock = use_mock
        self.model_path = model_path or os.getenv("BGE_MODEL_PATH")  # 优先使用环境变量
        self.use_chromadb_embedding = use_chromadb_embedding or os.getenv("RAG_USE_CHROMADB_EMBEDDING", "false").lower() == "true"  # 优先使用 ChromaDB 自带模型
        self._embedding_model = None
        self._model_lock = threading.Lock()  # 线程锁，保护模型懒加载

        # 默认检索配置
        self.default_top_k = 5
        self.default_score_threshold = 0.5

    @property
    def embedding_model(self) -> SentenceTransformer:
        """
        获取 Embedding 模型（线程安全的懒加载）

        使用双重检查锁（Double-Checked Locking）确保线程安全
        """
        if self._embedding_model is None:
            with self._model_lock:  # 加锁
                # 双重检查：其他线程可能已经初始化了
                if self._embedding_model is None:
                    # 检查是否使用Mock模式（用于测试或离线环境）
                    if self.use_mock or os.getenv("RAG_USE_MOCK", "false").lower() == "true":
                        logger.info(f"使用 Mock Embedding 模型 (测试/离线模式)")
                        try:
                            from tests.mocks import MockEmbeddingModel
                            self._embedding_model = MockEmbeddingModel()
                        except ImportError:
                            # 如果tests不可用，创建内联的Mock模型
                            logger.warning("tests.mocks 不可用，使用内联Mock模型")
                            import numpy as np
                            class _MockEmbeddingModel:
                                def __init__(self):
                                    self.dimension = 1024
                                    self.call_count = 0
                                def encode(self, texts):
                                    self.call_count += 1
                                    # 使用确定性伪随机向量
                                    embeddings = []
                                    for text in texts:
                                        text_hash = hash(text) % (2**31)
                                        np.random.seed(text_hash)
                                        vector = np.random.rand(1024)
                                        vector = vector / np.linalg.norm(vector)
                                        embeddings.append(vector.tolist())
                                    return embeddings
                                def get_sentence_embedding_dimension(self):
                                    return self.dimension
                            self._embedding_model = _MockEmbeddingModel()
                    else:
                        # 检查是否有本地模型路径
                        if self.model_path and os.path.exists(self.model_path):
                            logger.info(f"从本地路径加载 Embedding 模型: {self.model_path} (设备: {self.device})")
                            self._embedding_model = SentenceTransformer(
                                self.model_path,
                                device=self.device
                            )
                            logger.info(f"本地 Embedding 模型加载成功 (维度: {self._embedding_model.get_sentence_embedding_dimension()})")
                        else:
                            logger.info(f"加载在线 Embedding 模型: {self.embedding_model_name} (设备: {self.device})")
                            self._embedding_model = SentenceTransformer(
                                self.embedding_model_name,
                                device=self.device
                            )
                            logger.info(f"Embedding 模型加载成功 (维度: {self._embedding_model.get_sentence_embedding_dimension()})")
        return self._embedding_model

    def get_or_create_collection(self, name: str, metadata: Optional[dict] = None, use_embedding: bool = True):
        """
        获取或创建 ChromaDB Collection（兼容性增强版本）

        Args:
            name: Collection 名称
            metadata: 元数据（已废弃，保留参数兼容性）
            use_embedding: 是否使用 ChromaDB 自带向量模型（已废弃）

        Returns:
            ChromaDB Collection 对象
        """
        try:
            # 方案 1: 先尝试 get_collection（大多数情况下应该成功）
            try:
                collection = self.chroma_client.get_collection(name)
                logger.info(f"✅ 成功获取现有 Collection: {name}")
                return collection
            except KeyError as key_err:
                if "_type" in str(key_err):
                    # _type 错误：尝试删除并重新创建
                    logger.warning(f"Collection {name} 数据损坏（_type 错误），尝试删除并重新创建...")
                    try:
                        self.chroma_client.delete_collection(name)
                        logger.info(f"✅ 已删除损坏的 Collection: {name}")
                    except:
                        pass
                else:
                    raise
            except Exception as get_err:
                # Collection 不存在或其他错误
                if "does not exist" not in str(get_err).lower():
                    logger.debug(f"获取 Collection 失败: {get_err}")

            # 方案 2: 创建新的 collection
            try:
                collection = self.chroma_client.create_collection(name=name)
                logger.info(f"✅ Collection 创建成功: {name}")
                return collection
            except KeyError as key_err:
                if "_type" in str(key_err):
                    # _type 错误：使用服务器 API 直接创建
                    logger.warning(f"create_collection 返回 _type 错误，使用备用方案...")
                    # 直接使用 HTTP 客户端创建 collection
                    import requests
                    url = f"http://{self.chromadb_host}:{self.chromadb_port}/api/v1/tenants/default_tenant/databases/default_database/collections"
                    response = requests.post(url, json={"name": name})
                    if response.status_code in [200, 201]:
                        logger.info(f"✅ 通过 HTTP API 创建 Collection 成功: {name}")
                        # 返回一个简单的 collection 包装器
                        return self._create_collection_wrapper(name)
                    else:
                        raise Exception(f"创建 Collection 失败: {response.text}")
                else:
                    raise

        except Exception as e:
            logger.error(f"获取/创建 Collection 失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _create_collection_wrapper(self, name: str):
        """创建一个简单的 Collection 包装器（用于兼容性问题）"""
        from chromadb.api.models import Collection
        # 创建一个最小的 collection 对象
        return Collection(
            client=self.chroma_client,
            id=name,
            name=name,
            metadata={}
        )

    def reset_collection(self, name: str):
        """
        重置（删除）Collection

        Args:
            name: Collection 名称
        """
        try:
            self.chroma_client.delete_collection(name)
            logger.info(f"删除 Collection: {name}")
        except Exception as e:
            logger.error(f"删除 Collection 失败: {e}")
            raise

    def list_collections(self):
        """列出所有 Collections"""
        return self.chroma_client.list_collections()

    def health_check(self) -> bool:
        """
        检查 ChromaDB 连接状态

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            # 尝试列出 collections
            self.chroma_client.list_collections()
            return True
        except Exception as e:
            logger.error(f"ChromaDB 健康检查失败: {e}")
            return False


# 全局配置实例
_rag_config: Optional[RAGConfig] = None


def get_rag_config() -> RAGConfig:
    """
    获取全局 RAG 配置实例（单例模式）

    Returns:
        RAGConfig 实例
    """
    global _rag_config
    if _rag_config is None:
        # 检查是否使用Mock模式（从环境变量读取）
        use_mock = os.getenv("RAG_USE_MOCK", "false").lower() == "true"
        # 检查是否使用 ChromaDB 自带向量模型（从环境变量读取，默认 false）
        use_chromadb_embedding = os.getenv("RAG_USE_CHROMADB_EMBEDDING", "false").lower() == "true"
        _rag_config = RAGConfig(
            use_mock=use_mock,
            use_chromadb_embedding=use_chromadb_embedding
        )
    return _rag_config


def reset_rag_config():
    """重置全局 RAG 配置（主要用于测试）"""
    global _rag_config
    _rag_config = None


# 预定义的 Collection 名称
KNOWLEDGE_COLLECTION = "knowledge_chunks"

# 文档类型支持
SUPPORTED_FILE_TYPES = {
    "pdf": [".pdf"],
    "word": [".doc", ".docx"],
    "text": [".txt", ".md", ".markdown"],
    "html": [".html", ".htm"],
    "excel": [".xls", ".xlsx"],
    "powerpoint": [".ppt", ".pptx"],
}

# 统一的文件扩展名白名单（用于安全验证）
ALLOWED_FILE_EXTENSIONS = set()
for extensions in SUPPORTED_FILE_TYPES.values():
    ALLOWED_FILE_EXTENSIONS.update(extensions)

# 文件魔术字节（用于深度验证）
MAGIC_BYTES = {
    ".pdf": b"%PDF",
    ".doc": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
    ".docx": b"PK\x03\x04",  # ZIP format
    ".xls": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
    ".xlsx": b"PK\x03\x04",  # ZIP format
    ".ppt": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
    ".pptx": b"PK\x03\x04",  # ZIP format
}

# Embedding 模型列表
EMBEDDING_MODELS = {
    "bge-large-zh-v1.5": {
        "name": "BAAI/bge-large-zh-v1.5",
        "dimension": 1024,
        "language": "zh",
        "description": "中文大型 Embedding 模型，适合中文场景"
    },
    "bge-small-zh-v1.5": {
        "name": "BAAI/bge-small-zh-v1.5",
        "dimension": 512,
        "language": "zh",
        "description": "中文小型 Embedding 模型，速度更快"
    },
    "paraphrase-multilingual-MiniLM-L12-v2": {
        "name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "dimension": 384,
        "language": "multilingual",
        "description": "多语言轻量级模型"
    },
}
