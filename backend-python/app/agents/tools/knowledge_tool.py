"""
知识库检索工具
Knowledge Base Search Tool

允许 Agent 搜索和检索知识库中的信息
Allows Agent to search and retrieve information from knowledge bases
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# 常量定义
DEFAULT_TOP_K = 5
SIMILARITY_DECIMAL_PLACES = 3
DEFAULT_FILENAME = "Unknown"
DEFAULT_CHUNK_INDEX = 0


def format_search_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """格式化单个搜索结果"""
    return {
        "content": result["content"],
        "filename": result["metadata"].get("filename", DEFAULT_FILENAME),
        "similarity": round(result["similarity"], SIMILARITY_DECIMAL_PLACES),
        "chunk_index": result["metadata"].get("chunk_index", DEFAULT_CHUNK_INDEX)
    }


def create_error_response(error: Union[Exception, str], query: str) -> Dict[str, Any]:
    """创建错误响应"""
    error_msg = str(error) if isinstance(error, Exception) else error
    return {
        "error": error_msg,
        "query": query,
        "total_results": 0,
        "results": [],
        "context": "",
        "sources": [],
        "retrieval_time": datetime.now().isoformat()
    }


def create_success_response(
    query: str,
    results: List[Dict[str, Any]],
    formatted_results: List[Dict[str, Any]],
    context: str,
    sources: List[str]
) -> Dict[str, Any]:
    """创建成功响应"""
    return {
        "query": query,
        "total_results": len(results),
        "context": context,
        "sources": sources,
        "results": formatted_results,
        "retrieval_time": datetime.now().isoformat()
    }


async def knowledge_search_tool(
    query: str,
    knowledge_base_ids: List[str],
    top_k: int = DEFAULT_TOP_K,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    知识库检索工具

    Args:
        query: 搜索查询
        knowledge_base_ids: 知识库 ID 列表
        top_k: 返回结果数量
        user_id: 用户 ID（用于权限验证）

    Returns:
        检索结果，包含以下字段:
        - query: 原始查询
        - total_results: 结果总数
        - context: 格式化的上下文文本
        - sources: 来源列表
        - results: 详细结果列表
        - retrieval_time: 检索时间
    """
    # ✅ 检查用户是否选择了知识库
    if not knowledge_base_ids or len(knowledge_base_ids) == 0:
        logger.warning(f"⚠️ [知识库检索] 用户未选择知识库，拒绝搜索请求")
        return create_error_response(
            error="用户未选择知识库，无法进行检索。请先选择一个或多个知识库。",
            query=query
        )

    try:
        from ...rag.retriever import RAGRetriever
        from ...rag.config import get_rag_config

        # 创建检索器并执行搜索
        config = get_rag_config()
        retriever = RAGRetriever(config)

        results = await retriever.search(
            query=query,
            knowledge_base_ids=knowledge_base_ids,
            user_id=user_id or "",
            top_k=top_k
        )

        # 格式化结果
        formatted_results = [format_search_result(result) for result in results]

        # 构建上下文和来源
        context, sources = retriever.format_retrieval_context(results)

        return create_success_response(
            query=query,
            results=results,
            formatted_results=formatted_results,
            context=context,
            sources=sources
        )

    except Exception as e:
        logger.error(f"知识库检索失败: {e}")
        return create_error_response(e, query)
