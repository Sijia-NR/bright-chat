"""
RAG 检索器测试
Test RAG Retriever
"""
import pytest
import os


@pytest.mark.rag
@pytest.mark.unit
class TestRAGRetriever:
    """RAG检索器测试"""

    def test_search_by_query(self, rag_config):
        """测试按查询搜索"""
        from rag.retriever import RAGRetriever
        import uuid

        # 设置测试数据
        try:
            rag_config.chroma_client.delete_collection("knowledge_chunks")
        except:
            pass

        collection = rag_config.get_or_create_collection("knowledge_chunks")

        test_id = str(uuid.uuid4())
        collection.add(
            ids=[test_id],
            embeddings=[[0.1] * 1024],
            documents=["Python是一种编程语言"],
            metadatas=[{
                "document_id": str(uuid.uuid4()),
                "knowledge_base_id": "test-kb-001",
                "user_id": "test-user-001",
                "filename": "python.txt"
            }]
        )

        # 测试搜索
        retriever = RAGRetriever(rag_config)
        results = retriever.search(
            query="Python",
            knowledge_base_ids=["test-kb-001"],
            user_id="test-user-001",
            top_k=5
        )

        assert results is not None
        assert isinstance(results, list)

        # 清理
        try:
            rag_config.chroma_client.delete_collection("knowledge_chunks")
        except:
            pass


@pytest.mark.rag
@pytest.mark.unit
class TestRAGRetrieverEdgeCases:
    """RAG检索器边界情况测试"""

    def test_empty_knowledge_base_list(self, rag_config):
        """测试空知识库列表"""
        from rag.retriever import RAGRetriever
        retriever = RAGRetriever(rag_config)

        results = retriever.search(
            query="test",
            knowledge_base_ids=[],
            user_id="test-user-001",
            top_k=5
        )

        assert results == []
