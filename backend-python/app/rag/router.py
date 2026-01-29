"""
RAG API 路由
RAG API Router

提供知识库管理、文档上传、RAG 聊天等 API 端点
Provides API endpoints for knowledge base management, document upload, RAG chat
"""
import os
import uuid
import shutil
import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.knowledge_base import (
    KnowledgeGroup,
    KnowledgeGroupCreate,
    KnowledgeGroupResponse,
    KnowledgeBase,
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    Document,
    DocumentResponse,
    DocumentUploadResponse,
    RAGChatRequest,
)
from .config import get_rag_config
from .document_processor import DocumentProcessor
from .retriever import RAGRetriever

router = APIRouter()
logger = logging.getLogger(__name__)

# 常量定义
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB - 最大文件上传大小
TEMP_UPLOAD_DIR = "/tmp/bright_chat_uploads"  # 临时文件上传目录

# 全局处理器实例
document_processor: Optional[DocumentProcessor] = None
rag_retriever: Optional[RAGRetriever] = None


def get_document_processor():
    """获取文档处理器实例"""
    global document_processor
    if document_processor is None:
        document_processor = DocumentProcessor()
    return document_processor


def get_rag_retriever():
    """获取RAG检索器实例"""
    global rag_retriever
    if rag_retriever is None:
        rag_retriever = RAGRetriever()
    return rag_retriever


def cleanup_temp_files(document_id: str, filename: str):
    """
    清理文档相关的临时文件

    Args:
        document_id: 文档 ID
        filename: 原始文件名（用于获取扩展名）
    """
    try:
        # 清理所有匹配的临时文件
        if os.path.exists(TEMP_UPLOAD_DIR):
            for file in os.listdir(TEMP_UPLOAD_DIR):
                if file.startswith(document_id) or file.endswith(f"_{document_id}"):
                    file_path = os.path.join(TEMP_UPLOAD_DIR, file)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            logger.info(f"已删除临时文件: {file_path}")
                    except Exception as e:
                        logger.warning(f"删除临时文件失败 {file_path}: {e}")
    except Exception as e:
        logger.error(f"清理临时文件失败: {e}")


# ==================== 知识库分组 API ====================

@router.post("/groups", response_model=KnowledgeGroupResponse)
async def create_knowledge_group(
    group_data: KnowledgeGroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建知识库分组"""
    try:
        group = KnowledgeGroup(
            name=group_data.name,
            description=group_data.description,
            user_id=current_user.id,
            color=group_data.color
        )
        db.add(group)
        db.commit()
        db.refresh(group)
        return group
    except Exception as e:
        logger.error(f"创建知识库分组失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups", response_model=List[KnowledgeGroupResponse])
async def list_knowledge_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出当前用户的知识库分组"""
    try:
        groups = db.query(KnowledgeGroup).filter(
            KnowledgeGroup.user_id == current_user.id
        ).all()
        return groups
    except Exception as e:
        logger.error(f"获取知识库分组列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/groups/{group_id}")
async def delete_knowledge_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除知识库分组"""
    try:
        group = db.query(KnowledgeGroup).filter(
            KnowledgeGroup.id == group_id,
            KnowledgeGroup.user_id == current_user.id
        ).first()

        if not group:
            raise HTTPException(status_code=404, detail="分组不存在")

        db.delete(group)
        db.commit()
        return {"message": "分组删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除知识库分组失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 知识库 API ====================

@router.post("/bases", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建知识库"""
    try:
        kb = KnowledgeBase(
            name=kb_data.name,
            description=kb_data.description,
            user_id=current_user.id,
            group_id=kb_data.group_id,
            embedding_model=kb_data.embedding_model,
            chunk_size=kb_data.chunk_size,
            chunk_overlap=kb_data.chunk_overlap
        )
        db.add(kb)
        db.commit()
        db.refresh(kb)

        # 添加文档计数
        kb.document_count = 0
        return kb
    except Exception as e:
        logger.error(f"创建知识库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bases", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出当前用户的知识库"""
    try:
        kbs = db.query(KnowledgeBase).filter(
            KnowledgeBase.user_id == current_user.id
        ).all()

        # 添加文档计数
        result = []
        for kb in kbs:
            doc_count = db.query(Document).filter(
                Document.knowledge_base_id == kb.id,
                Document.upload_status == "completed"
            ).count()
            kb_dict = KnowledgeBaseResponse.model_validate(kb).model_dump()
            kb_dict['document_count'] = doc_count
            result.append(KnowledgeBaseResponse(**kb_dict))

        return result
    except Exception as e:
        logger.error(f"获取知识库列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bases/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取知识库详情"""
    try:
        kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id
        ).first()

        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 添加文档计数
        doc_count = db.query(Document).filter(
            Document.knowledge_base_id == kb.id,
            Document.upload_status == "completed"
        ).count()
        kb_dict = KnowledgeBaseResponse.model_validate(kb).model_dump()
        kb_dict['document_count'] = doc_count

        return KnowledgeBaseResponse(**kb_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识库详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/bases/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: str,
    kb_data: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新知识库"""
    try:
        kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id
        ).first()

        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 更新字段
        if kb_data.name is not None:
            kb.name = kb_data.name
        if kb_data.description is not None:
            kb.description = kb_data.description
        if kb_data.group_id is not None:
            kb.group_id = kb_data.group_id
        if kb_data.is_active is not None:
            kb.is_active = kb_data.is_active

        db.commit()
        db.refresh(kb)

        # 添加文档计数
        doc_count = db.query(Document).filter(
            Document.knowledge_base_id == kb.id,
            Document.upload_status == "completed"
        ).count()
        kb_dict = KnowledgeBaseResponse.model_validate(kb).model_dump()
        kb_dict['document_count'] = doc_count

        return KnowledgeBaseResponse(**kb_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新知识库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/bases/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除知识库"""
    try:
        kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id
        ).first()

        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 删除向量数据库中的数据
        processor = get_document_processor()
        await processor.delete_knowledge_base(kb_id)

        # 删除数据库记录（级联删除文档）
        db.delete(kb)
        db.commit()

        return {"message": "知识库删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除知识库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 文档上传 API ====================

@router.post("/bases/{kb_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """上传文档到知识库"""
    try:
        # 验证知识库
        kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id
        ).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 检查文件类型
        processor = get_document_processor()
        file_type = processor.get_file_type(file.filename)
        if not file_type:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。支持的类型: {list(processor.SUPPORTED_FILE_TYPES.keys())}"
            )

        # ✅ 先检查 Content-Length 头，防止大文件攻击
        content_length = file.file._headers.get('content-length')
        if content_length:
            try:
                file_size = int(content_length)
                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"文件大小超过限制 ({MAX_FILE_SIZE / 1024 / 1024:.0f}MB)"
                    )
            except ValueError:
                pass  # 如果 Content-Length 无效，继续读取文件内容检查

        # 验证文件大小（双重检查）
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"文件大小超过限制 ({MAX_FILE_SIZE / 1024 / 1024:.0f}MB)"
            )
        # 重置文件指针供后续使用
        await file.seek(0)

        # 创建文档记录
        doc_id = str(uuid.uuid4())
        document = Document(
            id=doc_id,
            knowledge_base_id=kb_id,
            filename=file.filename,
            file_type=file_type,
            upload_status="processing"
        )
        db.add(document)
        db.commit()

        # 保存文件到临时目录（使用安全的文件名）
        temp_dir = "/tmp/bright_chat_uploads"
        os.makedirs(temp_dir, exist_ok=True)

        # 安全处理文件名：防止路径遍历攻击
        from pathlib import Path
        file_ext = Path(file.filename).suffix
        safe_filename = f"{doc_id}_{uuid.uuid4().hex}{file_ext}"
        temp_file_path = os.path.join(temp_dir, safe_filename)

        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 后台处理文档
        if background_tasks:
            background_tasks.add_task(
                process_document_background,
                temp_file_path,
                kb_id,
                doc_id,
                file.filename,
                kb.chunk_size,
                kb.chunk_overlap,
                db,
                current_user.id  # ✅ 传递 user_id
            )

        return DocumentUploadResponse(
            document_id=doc_id,
            filename=file.filename,
            status="processing",
            message="文档上传成功，正在后台处理中..."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_document_background(
    file_path: str,
    kb_id: str,
    doc_id: str,
    filename: str,
    chunk_size: int,
    chunk_overlap: int,
    db: Session,
    user_id: str  # ✅ 添加 user_id 参数
):
    """后台处理文档"""
    from ..core.database import SessionLocal
    db = SessionLocal()

    try:
        processor = get_document_processor()

        # 处理文档
        result = await processor.process_document(
            file_path=file_path,
            knowledge_base_id=kb_id,
            user_id=user_id,  # ✅ 使用传入的 user_id
            filename=filename,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # 更新文档状态
        document = db.query(Document).filter(Document.id == doc_id).first()
        if document:
            document.upload_status = result.get("status", "failed")
            document.chunk_count = result.get("chunk_count", 0)
            document.error_message = result.get("error")
            document.processed_at = datetime.now()
            db.commit()

        # 删除临时文件
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        logger.error(f"后台处理文档失败: {e}")
        # 更新文档状态为失败
        try:
            document = db.query(Document).filter(Document.id == doc_id).first()
            if document:
                document.upload_status = "failed"
                document.error_message = str(e)
                document.processed_at = datetime.now()
                db.commit()
        except Exception as update_error:
            logger.error(f"更新文档状态失败: {update_error}")
    finally:
        # 确保数据库连接关闭
        try:
            db.close()
        except:
            pass


@router.get("/bases/{kb_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出知识库的文档"""
    try:
        # 验证知识库
        kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id
        ).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        documents = db.query(Document).filter(
            Document.knowledge_base_id == kb_id
        ).order_by(Document.uploaded_at.desc()).all()

        return documents
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除文档"""
    try:
        document = db.query(Document).filter(
            Document.id == doc_id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 验证权限（通过知识库）
        kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == document.knowledge_base_id,
            KnowledgeBase.user_id == current_user.id
        ).first()
        if not kb:
            raise HTTPException(status_code=403, detail="无权限删除此文档")

        # ✅ 删除向量数据（带错误处理）
        processor = get_document_processor()
        try:
            await processor.delete_document(doc_id)
        except Exception as e:
            logger.error(f"删除向量数据失败: {e}")
            # 向量删除失败不影响数据库记录的删除，但记录错误日志

        # 清理临时文件
        cleanup_temp_files(doc_id, document.filename)

        # 删除数据库记录
        db.delete(document)
        db.commit()

        return {"message": "文档删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{doc_id}/chunks")
async def get_document_chunks(
    doc_id: str,
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    offset: int = 0,
    limit: Optional[int] = None
):
    """获取文档的切片列表"""
    try:
        # 验证文档和权限
        document = db.query(Document).filter(
            Document.id == doc_id,
            Document.knowledge_base_id == kb_id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 验证知识库权限
        kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id
        ).first()
        if not kb:
            raise HTTPException(status_code=403, detail="无权限访问此文档")

        # 获取切片数据
        processor = get_document_processor()
        chunks_data = await processor.get_document_chunks(
            document_id=doc_id,
            knowledge_base_id=kb_id,
            user_id=current_user.id,
            include_embeddings=False,
            offset=offset,
            limit=limit
        )

        return {
            "document_id": doc_id,
            "filename": document.filename,
            "chunks": chunks_data["chunks"],
            "total_count": chunks_data["total_count"],
            "returned_count": chunks_data["returned_count"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档切片失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== RAG 聊天 API ====================

@router.post("/chat")
async def rag_chat(
    request: RAGChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """RAG 聊天（流式输出）"""
    try:
        # 验证知识库权限
        kb_count = db.query(KnowledgeBase).filter(
            KnowledgeBase.id.in_(request.knowledge_base_ids),
            KnowledgeBase.user_id == current_user.id
        ).count()

        if kb_count != len(request.knowledge_base_ids):
            raise HTTPException(status_code=403, detail="无权限访问部分知识库")

        # 获取配置
        config = request.retrieval_config or {}
        top_k = config.get("top_k", 5)
        score_threshold = config.get("score_threshold", None)

        # 执行检索
        retriever = get_rag_retriever()
        retrieval_result = await retriever.retrieve_and_format(
            query=request.query,
            knowledge_base_ids=request.knowledge_base_ids,
            user_id=current_user.id,
            top_k=top_k,
            score_threshold=score_threshold
        )

        # 构建增强提示词
        system_prompt = f"""你是一个专业的AI助手。请根据以下参考文档回答用户的问题。

参考文档:
{retrieval_result['context']}

要求:
1. 答案必须基于参考文档，不要编造信息
2. 如果参考文档中没有相关信息，请明确告知
3. 在答案中引用具体的来源
4. 保持简洁、准确、友好

用户问题: {request.query}
"""

        # 流式输出
        async def generate():
            # TODO: 调用 LLM 生成回答（这里需要集成现有的 LLM 服务）
            # 暂时返回检索结果
            import json
            yield f"data: {json.dumps({'type': 'sources', 'data': retrieval_result['sources']})}\n\n"
            yield f"data: {json.dumps({'type': 'context', 'content': retrieval_result['context']})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG 聊天失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        config = get_rag_config()
        is_healthy = config.health_check()

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "chromadb": "connected" if is_healthy else "disconnected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# 导入 logging
import logging
