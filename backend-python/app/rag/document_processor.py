"""
文档处理模块
Document Processing Module

负责文档上传、解析、分块和向量化
Responsible for document upload, parsing, chunking, and vectorization
"""
import os
import uuid
import asyncio
import sys
from typing import List, Dict, Any, Optional, AsyncGenerator
from pathlib import Path
import logging
from datetime import datetime

# 配置日志输出到 stdout，确保 docker logs 能捕获
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True  # 强制重新配置，即使已经配置过
)

# LangChain 文档加载器
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    TextLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangDocument

from .config import RAGConfig, SUPPORTED_FILE_TYPES, KNOWLEDGE_COLLECTION

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """文档处理器"""

    def __init__(self, config: Optional[RAGConfig] = None):
        """
        初始化文档处理器

        Args:
            config: RAG 配置
        """
        self.config = config or get_rag_config()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
        )

    def get_file_type(self, filename: str) -> Optional[str]:
        """
        根据文件扩展名获取文件类型

        Args:
            filename: 文件名

        Returns:
            文件类型 (pdf/word/text/html/excel/powerpoint) 或 None
        """
        ext = Path(filename).suffix.lower()
        for file_type, extensions in SUPPORTED_FILE_TYPES.items():
            if ext in extensions:
                return file_type
        return None

    async def load_document(self, file_path: str, file_type: str) -> List[LangDocument]:
        """
        加载文档内容

        Args:
            file_path: 文件路径
            file_type: 文件类型

        Returns:
            LangChain Document 列表
        """
        try:
            # 根据文件类型选择加载器
            if file_type == "pdf":
                loader = PyPDFLoader(file_path)
                documents = loader.load()
            elif file_type == "word":
                # 判断是 .docx (新版) 还是 .doc (旧版)
                if file_path.lower().endswith('.docx'):
                    # .docx 格式：使用 Docx2txtLoader
                    loader = Docx2txtLoader(file_path)
                    documents = loader.load()
                    logger.info(f"使用 Docx2txtLoader 加载 .docx 文件")
                else:
                    # .doc 格式（旧版）：使用 antiword 命令行工具
                    import subprocess
                    try:
                        result = subprocess.run(
                            ['antiword', file_path],
                            capture_output=True,
                            text=True,
                            check=True,
                            encoding='utf-8'
                        )
                        text = result.stdout
                        documents = [LangDocument(page_content=text, metadata={'source': file_path})]
                        logger.info(f"使用 antiword 加载 .doc 文件")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"antiword 处理 .doc 文件失败: {e}")
                        raise ValueError(f"无法处理 .doc 文件，请转换为 .docx 格式: {e}")
            elif file_type == "text":
                # 判断是 Markdown 还是纯文本
                if file_path.endswith(('.md', '.markdown')):
                    loader = UnstructuredMarkdownLoader(file_path)
                else:
                    loader = TextLoader(file_path, encoding='utf-8')
                documents = loader.load()
            elif file_type == "html":
                loader = UnstructuredHTMLLoader(file_path)
                documents = loader.load()
            elif file_type == "excel":
                # 使用 pandas 直接读取 Excel，避免 UnstructuredExcelLoader 的依赖问题
                documents = await self._load_excel_with_pandas(file_path)
            elif file_type == "powerpoint":
                loader = UnstructuredPowerPointLoader(file_path)
                documents = loader.load()
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")

            logger.info(f"成功加载文档: {file_path} (页数/段落数: {len(documents)})")
            return documents

        except Exception as e:
            logger.error(f"加载文档失败 {file_path}: {e}")
            raise

    async def _load_excel_with_pandas(self, file_path: str) -> List[LangDocument]:
        """
        使用 pandas 加载 Excel 文件

        Args:
            file_path: Excel 文件路径

        Returns:
            LangChain Document 列表
        """
        try:
            import pandas as pd

            # 根据文件扩展名选择引擎
            if file_path.endswith('.xls'):
                # 旧版 Excel 格式
                df = pd.read_excel(file_path, engine='xlrd')
            else:
                # 新版 Excel 格式
                df = pd.read_excel(file_path, engine='openpyxl')

            # 将 DataFrame 转换为文本
            text_content = df.to_string(index=False)

            # 创建 LangChain Document
            document = LangDocument(
                page_content=text_content,
                metadata={'source': file_path}
            )

            logger.info(f"使用 pandas 成功加载 Excel: {file_path} ({len(df)} 行, {len(df.columns)} 列)")
            return [document]

        except Exception as e:
            logger.error(f"pandas 加载 Excel 失败: {e}")
            # 尝试使用原始的 UnstructuredExcelLoader 作为后备
            try:
                loader = UnstructuredExcelLoader(file_path)
                return loader.load()
            except:
                raise

    def split_documents(
        self,
        documents: List[LangDocument],
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> List[LangDocument]:
        """
        分割文档为小块

        Args:
            documents: LangChain Document 列表
            chunk_size: 块大小
            chunk_overlap: 块重叠大小

        Returns:
            分割后的 Document 列表
        """
        # 更新分割器配置
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
        )

        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"文档分割完成: {len(documents)} 个文档 -> {len(chunks)} 个块")
        return chunks

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        将文本转换为向量

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        try:
            # 使用 Sentence Transformers 生成向量
            embeddings = self.config.embedding_model.encode(
                texts,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            # 兼容 numpy array 和 list 类型
            if hasattr(embeddings, 'tolist'):
                return embeddings.tolist()
            return embeddings if isinstance(embeddings, list) else list(embeddings)
        except Exception as e:
            logger.error(f"向量化失败: {e}")
            raise

    async def process_document(
        self,
        file_path: str,
        knowledge_base_id: str,
        user_id: str,
        filename: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理文档：加载 -> 分割 -> 向量化 -> 存储

        Args:
            file_path: 文件路径
            knowledge_base_id: 知识库 ID
            user_id: 用户 ID
            filename: 文件名
            chunk_size: 块大小
            chunk_overlap: 块重叠
            document_id: 文档 ID (可选,如果不提供则自动生成)

        Returns:
            处理结果字典
        """
        document_id = document_id or str(uuid.uuid4())
        start_time = datetime.now()

        try:
            logger.info(f"开始处理文档: {filename}")

            # 1. 验证并加载文档
            file_type, documents = await self._validate_and_load_document(filename, file_path)

            # 2. 分割文档
            chunks = self.split_documents(documents, chunk_size, chunk_overlap)

            # 3. 准备 ChromaDB 数据
            chunk_ids, chunk_documents, chunk_metadatas = self._prepare_chunk_data(
                document_id, knowledge_base_id, user_id, filename, file_type, chunks
            )

            # 4. 存储到 ChromaDB
            await self._store_to_chromadb(chunk_ids, chunk_documents, chunk_metadatas, len(chunks))

            # 5. 生成结果
            return self._generate_result(document_id, filename, file_type, len(chunks), start_time)

        except Exception as e:
            logger.error(f"文档处理失败 {filename}: {e}")
            return self._generate_error_result(document_id, filename, str(e))

    async def _validate_and_load_document(self, filename: str, file_path: str) -> tuple:
        """验证文件类型并加载文档"""
        file_type = self.get_file_type(filename)
        if not file_type:
            raise ValueError(f"不支持的文件类型: {filename}")

        documents = await self.load_document(file_path, file_type)
        return file_type, documents

    def _prepare_chunk_data(
        self,
        document_id: str,
        knowledge_base_id: str,
        user_id: str,
        filename: str,
        file_type: str,
        chunks: list
    ) -> tuple:
        """准备 ChromaDB 所需的数据"""
        chunk_ids = []
        chunk_documents = []
        chunk_metadatas = []

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{idx}"
            chunk_ids.append(chunk_id)
            chunk_documents.append(chunk.page_content)
            chunk_metadatas.append({
                "document_id": document_id,
                "knowledge_base_id": knowledge_base_id,
                "user_id": user_id,
                "chunk_index": idx,
                "filename": filename,
                "file_type": file_type,
                "source": filename
            })

        return chunk_ids, chunk_documents, chunk_metadatas

    async def _store_to_chromadb(
        self,
        chunk_ids: list,
        chunk_documents: list,
        chunk_metadatas: list,
        chunk_count: int
    ):
        """存储数据到 ChromaDB"""
        if self.config.use_chromadb_embedding:
            logger.info(f"准备存储 {chunk_count} 个块到 ChromaDB (使用自带向量模型)...")
            collection = self.config.get_or_create_collection(
                KNOWLEDGE_COLLECTION,
                use_embedding=True
            )
            logger.info("Collection 已获取，开始添加数据...")
            collection.add(
                ids=chunk_ids,
                documents=chunk_documents,
                metadatas=chunk_metadatas
            )
            logger.info(f"✅ 使用 ChromaDB 自带向量模型成功处理 {chunk_count} 个块")
        else:
            logger.info("使用本地 embedding 模型生成向量")
            texts = chunk_documents
            embeddings = await self.embed_documents(texts)

            collection = self.config.get_or_create_collection(KNOWLEDGE_COLLECTION)
            collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=chunk_documents,
                metadatas=chunk_metadatas
            )

    def _generate_result(
        self,
        document_id: str,
        filename: str,
        file_type: str,
        chunk_count: int,
        start_time: datetime
    ) -> Dict[str, Any]:
        """生成处理成功结果"""
        processing_time = (datetime.now() - start_time).total_seconds()

        result = {
            "document_id": document_id,
            "filename": filename,
            "file_type": file_type,
            "chunk_count": chunk_count,
            "status": "completed",
            "processing_time": processing_time,
            "message": f"文档处理成功，共 {chunk_count} 个块"
        }

        logger.info(f"文档处理完成: {filename} ({chunk_count} 块, {processing_time:.2f}秒)")
        return result

    def _generate_error_result(
        self,
        document_id: str,
        filename: str,
        error_message: str
    ) -> Dict[str, Any]:
        """生成处理失败结果"""
        return {
            "document_id": document_id,
            "filename": filename,
            "status": "failed",
            "error": error_message,
            "message": f"文档处理失败: {error_message}"
        }

    async def delete_document(self, document_id: str) -> bool:
        """
        从向量数据库中删除文档

        Args:
            document_id: 文档 ID

        Returns:
            是否删除成功
        """
        try:
            collection = self.config.get_or_create_collection(KNOWLEDGE_COLLECTION)
            # 删除所有以 document_id 开头的 chunks
            collection.delete(
                where={"document_id": document_id}
            )
            logger.info(f"删除文档向量: {document_id}")
            return True
        except Exception as e:
            logger.error(f"删除文档向量失败 {document_id}: {e}")
            return False

    async def get_document_chunks(
        self,
        document_id: str,
        knowledge_base_id: str,
        user_id: str,
        include_embeddings: bool = False,
        offset: int = 0,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取文档的所有切片

        Args:
            document_id: 文档 ID
            knowledge_base_id: 知识库 ID
            user_id: 用户 ID（权限验证）
            include_embeddings: 是否包含向量
            offset: 分页偏移量
            limit: 分页限制（None = 返回全部）

        Returns:
            切片信息字典
        """
        try:
            collection = self.config.get_or_create_collection(KNOWLEDGE_COLLECTION)

            # 构建权限验证的过滤条件
            where_clause = {
                "$and": [
                    {"document_id": document_id},
                    {"knowledge_base_id": knowledge_base_id},
                    {"user_id": user_id}
                ]
            }

            # 查询切片（ChromaDB 的 count() 不支持 where 参数，先查询再计数）
            include_fields = ["documents", "metadatas", "embeddings"] if include_embeddings else ["documents", "metadatas"]
            results = collection.get(
                where=where_clause,
                include=include_fields
            )

            # 获取总数
            total_count = len(results['ids'])

            if total_count == 0:
                return {
                    "chunks": [],
                    "total_count": 0,
                    "returned_count": 0
                }

            # 组合并排序
            chunks_data = []
            for idx, chunk_id in enumerate(results['ids']):
                metadata = results['metadatas'][idx]
                chunk_index = metadata.get('chunk_index', 0)

                chunks_data.append({
                    'id': chunk_id,
                    'chunk_index': chunk_index,
                    'content': results['documents'][idx],
                    'metadata': metadata,
                    'embedding': results['embeddings'][idx] if include_embeddings and results.get('embeddings') else None
                })

            # 按 chunk_index 排序
            chunks_data.sort(key=lambda x: x['chunk_index'])

            # 应用分页
            if limit is not None:
                paginated_data = chunks_data[offset:offset + limit]
            else:
                paginated_data = chunks_data[offset:] if offset > 0 else chunks_data

            return {
                "chunks": paginated_data,
                "total_count": total_count,
                "returned_count": len(paginated_data)
            }

        except Exception as e:
            logger.error(f"获取文档切片失败 {document_id}: {e}")
            raise

    async def delete_knowledge_base(self, knowledge_base_id: str) -> bool:
        """
        从向量数据库中删除知识库的所有文档

        Args:
            knowledge_base_id: 知识库 ID

        Returns:
            是否删除成功
        """
        try:
            collection = self.config.get_or_create_collection(KNOWLEDGE_COLLECTION)
            collection.delete(
                where={"knowledge_base_id": knowledge_base_id}
            )
            logger.info(f"删除知识库向量: {knowledge_base_id}")
            return True
        except Exception as e:
            logger.error(f"删除知识库向量失败 {knowledge_base_id}: {e}")
            return False

    async def get_document_chunks_count(
        self,
        knowledge_base_id: str,
        document_id: Optional[str] = None
    ) -> int:
        """
        获取文档的块数量

        Args:
            knowledge_base_id: 知识库 ID
            document_id: 文档 ID（可选）

        Returns:
            块数量
        """
        try:
            collection = self.config.get_or_create_collection(KNOWLEDGE_COLLECTION)
            where_clause = {"knowledge_base_id": knowledge_base_id}
            if document_id:
                where_clause["document_id"] = document_id

            result = collection.count(where=where_clause)
            return result
        except Exception as e:
            logger.error(f"获取块数量失败: {e}")
            return 0


# 导入配置函数
from .config import get_rag_config
