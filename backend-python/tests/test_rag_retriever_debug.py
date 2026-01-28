"""
RAG 检索器调试测试
Debug RAG Retriever Tests
"""
import pytest
import os


@pytest.mark.rag
@pytest.mark.unit
class TestRAGRetrieverDebug:
    """RAG检索器调试测试"""

    def test_simple_import(self):
        """测试简单导入"""
        try:
            from rag.retriever import RAGRetriever
            print("RAGRetriever imported successfully")
            assert True
        except ImportError as e:
            print(f"Import failed: {e}")
            pytest.skip("RAG模块未安装")

    def test_create_retriever(self, rag_config):
        """测试创建检索器"""
        try:
            from rag.retriever import RAGRetriever
            print(f"rag_config type: {type(rag_config)}")
            retriever = RAGRetriever(rag_config)
            print(f"RAGRetriever created: {type(retriever)}")
            assert retriever is not None
        except ImportError as e:
            print(f"Import failed: {e}")
            pytest.skip("RAG模块未安装")
