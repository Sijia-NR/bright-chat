"""
RAG 检索模块
RAG Retrieval Module

负责语义搜索、检索增强生成
Responsible for semantic search and retrieval-augmented generation
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .config import RAGConfig, KNOWLEDGE_COLLECTION

logger = logging.getLogger(__name__)


class RAGRetriever:
    """RAG 检索器"""

    def __init__(self, config: Optional[RAGConfig] = None):
        """
        初始化 RAG 检索器

        Args:
            config: RAG 配置
        """
        self.config = config or get_rag_config()

    async def embed_query(self, query: str) -> List[float]:
        """
        将查询转换为向量

        Args:
            query: 查询文本

        Returns:
            查询向量
        """
        try:
            embedding = self.config.embedding_model.encode(
                [query],
                show_progress_bar=False,
                normalize_embeddings=True
            )
            # 兼容 numpy array 和 list 类型
            result = embedding[0]
            if hasattr(result, 'tolist'):
                return result.tolist()
            return result if isinstance(result, list) else list(result)
        except Exception as e:
            logger.error(f"查询向量化失败: {e}")
            raise

    async def search(
        self,
        query: str,
        knowledge_base_ids: List[str],
        user_id: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        语义搜索

        Args:
            query: 查询文本
            knowledge_base_ids: 知识库 ID 列表
            user_id: 用户 ID（用于数据隔离）
            top_k: 返回结果数量
            score_threshold: 相似度阈值（可选）

        Returns:
            检索结果列表
        """
        try:
            # 1. 查询向量化
            query_embedding = await self.embed_query(query)

            # 2. 构建过滤条件
            # 注意：ChromaDB 的 where 语法只支持精确匹配，不支持 $in 操作符
            # 所以我们需要分别查询每个知识库，然后合并结果
            all_results = []

            for kb_id in knowledge_base_ids:
                collection = self.config.get_or_create_collection(KNOWLEDGE_COLLECTION)

                # 查询（使用正确的 ChromaDB where 语法）
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where={
                        "$and": [
                            {"user_id": user_id},
                            {"knowledge_base_id": kb_id}
                        ]
                    }
                )

                # 处理结果
                if results['ids'] and results['ids'][0]:
                    for idx, doc_id in enumerate(results['ids'][0]):
                        distance = results['distances'][0][idx]
                        # 转换距离为相似度（Cosine 距离 -> 相似度）
                        similarity = 1 - distance

                        # 应用阈值过滤
                        if score_threshold and similarity < score_threshold:
                            continue

                        all_results.append({
                            "id": doc_id,
                            "content": results['documents'][0][idx],
                            "metadata": results['metadatas'][0][idx],
                            "similarity": similarity,
                            "distance": distance
                        })

            # 3. 按相似度排序并返回 top_k
            all_results.sort(key=lambda x: x['similarity'], reverse=True)
            return all_results[:top_k]

        except Exception as e:
            logger.error(f"检索失败: {e}")
            raise

    async def search_with_rerank(
        self,
        query: str,
        knowledge_base_ids: List[str],
        user_id: str,
        top_k: int = 10,
        rerank_top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        两阶段检索：先检索更多结果，再重排序

        Args:
            query: 查询文本
            knowledge_base_ids: 知识库 ID 列表
            user_id: 用户 ID
            top_k: 第一阶段检索数量
            rerank_top_k: 重排序后返回数量

        Returns:
            检索结果列表
        """
        # 第一阶段：检索更多结果
        results = await self.search(
            query=query,
            knowledge_base_ids=knowledge_base_ids,
            user_id=user_id,
            top_k=top_k,
            score_threshold=None
        )

        # TODO: 这里可以添加重排序逻辑（如使用 Cohere Rerank API）
        # 当前实现：直接按相似度排序返回前 rerank_top_k 个
        return results[:rerank_top_k]

    def format_retrieval_context(
        self,
        results: List[Dict[str, Any]],
        max_context_length: int = 4000
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        格式化检索结果为上下文

        Args:
            results: 检索结果列表
            max_context_length: 最大上下文长度

        Returns:
            (格式化后的上下文, 引用来源列表)
        """
        sources = []
        context_parts = []

        for idx, result in enumerate(results):
            content = result['content']
            metadata = result['metadata']

            # 添加来源信息
            source = {
                "index": idx + 1,
                "filename": metadata.get('filename', 'Unknown'),
                "chunk_index": metadata.get('chunk_index', 0),
                "similarity": round(result['similarity'], 3)
            }
            sources.append(source)

            # 添加上下文（带来源标注）
            context_part = f"[来源 {idx + 1}: {metadata.get('filename', 'Unknown')}]\n{content}"
            context_parts.append(context_part)

        # 合并上下文
        context = "\n\n".join(context_parts)

        # 截断过长的上下文
        if len(context) > max_context_length:
            context = context[:max_context_length] + "\n...(上下文已截断)"

        return context, sources

    async def retrieve_and_format(
        self,
        query: str,
        knowledge_base_ids: List[str],
        user_id: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        检索并格式化结果（一站式接口）

        Args:
            query: 查询文本
            knowledge_base_ids: 知识库 ID 列表
            user_id: 用户 ID
            top_k: 返回结果数量
            score_threshold: 相似度阈值

        Returns:
            格式化的检索结果
        """
        # 执行检索
        results = await self.search(
            query=query,
            knowledge_base_ids=knowledge_base_ids,
            user_id=user_id,
            top_k=top_k,
            score_threshold=score_threshold
        )

        # 格式化上下文
        context, sources = self.format_retrieval_context(results)

        return {
            "context": context,
            "sources": sources,
            "raw_results": results,
            "total_results": len(results),
            "query": query,
            "retrieval_time": datetime.now().isoformat()
        }

    async def hybrid_search(
        self,
        query: str,
        knowledge_base_ids: List[str],
        user_id: str,
        top_k: int = 5,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        混合检索：语义搜索 + 关键词搜索（BM25）

        Args:
            query: 查询文本
            knowledge_base_ids: 知识库 ID 列表
            user_id: 用户 ID
            top_k: 返回结果数量
            alpha: 语义和关键词的权重比例（0-1，1表示纯语义）

        Returns:
            检索结果列表
        """
        # 当前实现：仅语义搜索
        # TODO: 可以添加 BM25 关键词搜索，然后融合结果
        results = await self.search(
            query=query,
            knowledge_base_ids=knowledge_base_ids,
            user_id=user_id,
            top_k=top_k
        )
        return results


# 导入配置函数
from .config import get_rag_config
