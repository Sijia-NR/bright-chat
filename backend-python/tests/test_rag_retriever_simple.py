"""
RAG 检索器简单测试（不使用 fixture）
Simple RAG Retriever Tests (no fixtures)
"""
import pytest
import os


@pytest.mark.rag
@pytest.mark.unit
class TestRAGRetrieverSimple:
    """RAG检索器简单测试"""

    @pytest.mark.asyncio
    async def test_search_by_query_no_fixture(self):
        """测试搜索（不使用fixture）"""
        from rag.config import get_rag_config, reset_rag_config
        from rag.retriever import RAGRetriever
        import uuid

        # 重置配置
        reset_rag_config()
        os.environ['RAG_USE_MOCK'] = 'true'
        config = get_rag_config()

        # 设置测试数据
        try:
            config.chroma_client.delete_collection("knowledge_chunks")
        except:
            pass

        collection = config.get_or_create_collection("knowledge_chunks")

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

        # 测试搜索（异步方法需要await）
        retriever = RAGRetriever(config)
        results = await retriever.search(
            query="Python",
            knowledge_base_ids=["test-kb-001"],
            user_id="test-user-001",
            top_k=5
        )

        assert results is not None
        assert isinstance(results, list)

        # 清理
        try:
            config.chroma_client.delete_collection("knowledge_chunks")
        except:
            pass
