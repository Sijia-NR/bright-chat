"""
文档处理器测试
Test Document Processor
"""
import pytest
import os
import asyncio
from pathlib import Path
from tests.test_utils import TestDocumentCreator, MockEmbeddingModel


@pytest.mark.rag
@pytest.mark.unit
class TestDocumentProcessor:
    """文档处理器测试"""

    def test_file_type_detection(self):
        """测试文件类型检测"""
        try:
            from rag.document_processor import DocumentProcessor
            processor = DocumentProcessor()

            # 测试各种文件类型
            assert processor.get_file_type("test.pdf") == "pdf"
            assert processor.get_file_type("test.docx") == "word"
            assert processor.get_file_type("test.txt") == "text"
            assert processor.get_file_type("test.md") == "text"
            assert processor.get_file_type("test.html") == "html"
            assert processor.get_file_type("test.xls") == "excel"
            assert processor.get_file_type("test.xlsx") == "excel"
            assert processor.get_file_type("test.pptx") == "powerpoint"
            assert processor.get_file_type("test.unknown") is None

        except ImportError:
            pytest.skip("RAG模块未安装")

    @pytest.mark.asyncio
    async def test_load_text_document(self):
        """测试加载文本文档"""
        try:
            from rag.document_processor import DocumentProcessor
            processor = DocumentProcessor()

            # 创建测试文件
            content = "这是一个测试文档。\n包含两行文本。"
            file_path = TestDocumentCreator.create_text_file(content)

            # 加载文档（异步方法）
            documents = await processor.load_document(file_path, "text")

            assert documents is not None
            assert len(documents) > 0

        except ImportError:
            pytest.skip("RAG模块未安装")

    def test_split_documents(self):
        """测试文档分割"""
        try:
            from rag.document_processor import DocumentProcessor
            from langchain.schema import Document as LangDocument

            processor = DocumentProcessor()

            # 创建测试文档
            docs = [
                LangDocument(page_content="第一段内容。" * 100),
                LangDocument(page_content="第二段内容。" * 100)
            ]

            # 分割文档
            chunks = processor.split_documents(docs, chunk_size=200, chunk_overlap=50)

            assert chunks is not None
            assert len(chunks) > len(docs)  # 分割后应该有更多块

        except ImportError:
            pytest.skip("RAG模块未安装")

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_embed_documents(self):
        """测试文档向量化"""
        try:
            from rag.document_processor import DocumentProcessor
            processor = DocumentProcessor()

            # 准备测试文本
            texts = ["测试文本一", "测试文本二", "测试文本三"]

            # 向量化（使用真实的Embedding模型，可能较慢）
            embeddings = await processor.embed_documents(texts)

            assert embeddings is not None
            assert len(embeddings) == len(texts)
            assert len(embeddings[0]) > 0  # 向量维度应该大于0

        except ImportError:
            pytest.skip("RAG模块未安装")

    @pytest.mark.asyncio
    async def test_process_document_full_workflow(self):
        """测试完整文档处理流程"""
        try:
            from rag.document_processor import DocumentProcessor
            processor = DocumentProcessor()

            # 创建测试文档
            content = """
            BrightChat是一个AI聊天应用。

            它支持多种功能：
            1. 实时聊天
            2. 用户管理
            3. 模型配置

            这是测试文档的内容。
            """

            file_path = TestDocumentCreator.create_text_file(content, "brightchat_test.txt")

            # 处理文档（异步方法）
            result = await processor.process_document(
                file_path=file_path,
                knowledge_base_id="test-kb-001",
                user_id="test-user-001",
                filename="brightchat_test.txt",
                chunk_size=100,
                chunk_overlap=20
            )

            # 验证结果
            assert result is not None
            assert "document_id" in result
            assert "status" in result

            # 清理向量数据
            if result["status"] == "completed":
                from tests.test_utils import cleanup_test_chroma
                cleanup_test_chroma()

        except ImportError:
            pytest.skip("RAG模块未安装")


@pytest.mark.rag
@pytest.mark.unit
class TestDocumentProcessorErrorHandling:
    """文档处理器错误处理测试"""

    @pytest.mark.asyncio
    async def test_unsupported_file_type(self):
        """测试不支持的文件类型"""
        try:
            from rag.document_processor import DocumentProcessor
            processor = DocumentProcessor()

            # 创建不支持的文件
            file_path = TestDocumentCreator.create_text_file("content", "test.xyz")

            # 尝试加载应该失败
            with pytest.raises(ValueError):
                await processor.load_document(file_path, "unsupported")

        except ImportError:
            pytest.skip("RAG模块未安装")

    @pytest.mark.asyncio
    async def test_empty_document(self):
        """测试空文档处理"""
        try:
            from rag.document_processor import DocumentProcessor
            processor = DocumentProcessor()

            # 创建空文件
            file_path = TestDocumentCreator.create_text_file("", "empty.txt")

            # 加载文档（异步方法）
            documents = await processor.load_document(file_path, "text")

            # 空文档应该至少返回一个Document对象（可能内容为空）
            assert documents is not None

        except ImportError:
            pytest.skip("RAG模块未安装")
