"""
RAG 功能集成代码 - 添加到 minimal_api.py
RAG Feature Integration Code - Add to minimal_api.py

将此代码块插入到 minimal_api.py 的第 1592 行（在 @app.get("/health") 之前）
Insert this code block at line 1592 in minimal_api.py (before @app.get("/health"))
"""

# ============================================================================
# RAG 相关导入
# ============================================================================
import os
import uuid
import shutil
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

rag_logger = logging.getLogger(__name__)

# ============================================================================
# RAG 相关数据库模型
# ============================================================================

class KnowledgeGroup(Base):
    """知识库分组表"""
    __tablename__ = "knowledge_groups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    color = Column(String(20), default="#3B82F6")
    created_at = Column(DateTime, nullable=False, default=func.now())


class KnowledgeBase(Base):
    """知识库表"""
    __tablename__ = "knowledge_bases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(String(36), ForeignKey("knowledge_groups.id", ondelete="SET NULL"), nullable=True)
    embedding_model = Column(String(100), default="bge-large-zh-v1.5")
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=50)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


class Document(Base):
    """知识库文档表"""
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_base_id = Column(String(36), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=True)
    file_size = Column(Integer, nullable=True)
    chunk_count = Column(Integer, default=0)
    upload_status = Column(String(50), default="processing")
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, nullable=False, default=func.now())
    processed_at = Column(DateTime, nullable=True)


# ============================================================================
# RAG Pydantic 模型
# ============================================================================

class KnowledgeGroupCreate(BaseModel):
    """创建知识库分组请求"""
    name: str
    description: Optional[str] = None
    color: str = "#3B82F6"


class KnowledgeGroupResponse(BaseModel):
    """知识库分组响应"""
    id: str
    name: str
    description: Optional[str] = None
    user_id: str
    color: str
    created_at: datetime


class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""
    name: str
    description: Optional[str] = None
    group_id: Optional[str] = None
    embedding_model: str = "bge-large-zh-v1.5"
    chunk_size: int = 500
    chunk_overlap: int = 50


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    group_id: Optional[str] = None
    is_active: Optional[bool] = None


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: str
    name: str
    description: Optional[str] = None
    user_id: str
    group_id: Optional[str] = None
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    document_count: int = 0


class DocumentResponse(BaseModel):
    """文档响应"""
    id: str
    knowledge_base_id: str
    filename: str
    file_type: Optional[str]
    file_size: Optional[int]
    chunk_count: int
    upload_status: str
    error_message: Optional[str]
    uploaded_at: datetime
    processed_at: Optional[datetime]


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    document_id: str
    filename: str
    status: str
    message: str


class RAGChatRequest(BaseModel):
    """RAG 聊天请求"""
    query: str
    knowledge_base_ids: List[str]
    retrieval_config: Optional[Dict[str, Any]] = None


# ============================================================================
# RAG API 路由
# ============================================================================

# ==================== 知识库分组 API ====================

@app.post(f"{API_PREFIX}/knowledge/groups", response_model=KnowledgeGroupResponse)
async def create_knowledge_group(
    group_data: KnowledgeGroupCreate,
    current_user: User = Depends(require_user),
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
        rag_logger.error(f"创建知识库分组失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(f"{API_PREFIX}/knowledge/groups", response_model=List[KnowledgeGroupResponse])
async def list_knowledge_groups(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """列出当前用户的知识库分组"""
    try:
        groups = db.query(KnowledgeGroup).filter(
            KnowledgeGroup.user_id == current_user.id
        ).all()
        return groups
    except Exception as e:
        rag_logger.error(f"获取知识库分组列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete(f"{API_PREFIX}/knowledge/groups/{{group_id}}")
async def delete_knowledge_group(
    group_id: str,
    current_user: User = Depends(require_user),
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
        rag_logger.error(f"删除知识库分组失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 知识库 API ====================

@app.post(f"{API_PREFIX}/knowledge/bases", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    current_user: User = Depends(require_user),
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
        kb_dict = KnowledgeBaseResponse.model_validate(kb).model_dump()
        kb_dict['document_count'] = 0
        return KnowledgeBaseResponse(**kb_dict)
    except Exception as e:
        rag_logger.error(f"创建知识库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(f"{API_PREFIX}/knowledge/bases", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    current_user: User = Depends(require_user),
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
        rag_logger.error(f"获取知识库列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(f"{API_PREFIX}/knowledge/bases/{{kb_id}}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: str,
    current_user: User = Depends(require_user),
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
        rag_logger.error(f"获取知识库详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put(f"{API_PREFIX}/knowledge/bases/{{kb_id}}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: str,
    kb_data: KnowledgeBaseUpdate,
    current_user: User = Depends(require_user),
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
        rag_logger.error(f"更新知识库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete(f"{API_PREFIX}/knowledge/bases/{{kb_id}}")
async def delete_knowledge_base(
    kb_id: str,
    current_user: User = Depends(require_user),
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

        # TODO: 删除向量数据库中的数据（需要导入 RAG 模块）

        # 删除数据库记录（级联删除文档）
        db.delete(kb)
        db.commit()

        return {"message": "知识库删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        rag_logger.error(f"删除知识库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 文档 API ====================

@app.get(f"{API_PREFIX}/knowledge/bases/{{kb_id}}/documents", response_model=List[DocumentResponse])
async def list_documents(
    kb_id: str,
    current_user: User = Depends(require_user),
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
        rag_logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete(f"{API_PREFIX}/knowledge/documents/{{doc_id}}")
async def delete_document(
    doc_id: str,
    current_user: User = Depends(require_user),
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

        # TODO: 删除向量数据（需要导入 RAG 模块）

        # 删除数据库记录
        db.delete(document)
        db.commit()

        return {"message": "文档删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        rag_logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== RAG 聊天 API ====================

@app.post(f"{API_PREFIX}/knowledge/rag/chat")
async def rag_chat(
    request: RAGChatRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """RAG 聊天（简化版本）"""
    try:
        # 验证知识库权限
        kb_count = db.query(KnowledgeBase).filter(
            KnowledgeBase.id.in_(request.knowledge_base_ids),
            KnowledgeBase.user_id == current_user.id
        ).count()

        if kb_count != len(request.knowledge_base_ids):
            raise HTTPException(status_code=403, detail="无权限访问部分知识库")

        # TODO: 完整的 RAG 检索和生成流程
        # 当前返回模拟响应
        return {
            "query": request.query,
            "knowledge_base_ids": request.knowledge_base_ids,
            "message": "RAG 聊天功能已集成，但需要配置 ChromaDB 和 Embedding 模型",
            "status": "configured_but_inactive",
            "hint": "请确保 RAG 模块已正确配置"
        }

    except HTTPException:
        raise
    except Exception as e:
        rag_logger.error(f"RAG 聊天失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== RAG 健康检查 ====================

@app.get(f"{API_PREFIX}/knowledge/health")
async def rag_health_check():
    """RAG 模块健康检查"""
    try:
        # 检查数据库表是否存在
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        has_rag_tables = all(tab in tables for tab in ["knowledge_groups", "knowledge_bases", "documents"])

        return {
            "status": "healthy" if has_rag_tables else "database_tables_missing",
            "database_tables": "created" if has_rag_tables else "missing",
            "chromadb": "not_configured",
            "embedding_model": "not_loaded",
            "message": "RAG API 已集成，但需要配置 ChromaDB 和 Embedding 模型才能使用完整功能",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# 集成说明
# ============================================================================
"""
集成步骤 Integration Steps:

1. 创建数据库表（如果不存在）:
   CREATE TABLE knowledge_groups (...);
   CREATE TABLE knowledge_bases (...);
   CREATE TABLE documents (...);

2. 运行此脚本后，RAG API 将在以下路径可用:
   POST   /api/v1/knowledge/groups          - 创建知识库分组
   GET    /api/v1/knowledge/groups          - 列出分组
   DELETE /api/v1/knowledge/groups/{id}     - 删除分组
   POST   /api/v1/knowledge/bases           - 创建知识库
   GET    /api/v1/knowledge/bases           - 列出知识库
   GET    /api/v1/knowledge/bases/{id}      - 获取知识库详情
   PUT    /api/v1/knowledge/bases/{id}      - 更新知识库
   DELETE /api/v1/knowledge/bases/{id}      - 删除知识库
   GET    /api/v1/knowledge/bases/{id}/documents - 列出文档
   DELETE /api/v1/knowledge/documents/{id} - 删除文档
   POST   /api/v1/knowledge/rag/chat       - RAG 聊天
   GET    /api/v1/knowledge/health         - 健康检查

3. 完整功能需要:
   - 安装 RAG 依赖: pip install -r requirements-rag.txt
   - 配置 ChromaDB (本地或 Docker)
   - 下载 BGE Embedding 模型

4. 当前状态:
   - ✅ API 端点已集成
   - ✅ 数据库模型已定义
   - ⚠️ 文档上传功能需要额外的导入配置
   - ⚠️ RAG 检索和生成需要完整的 RAG 模块
"""
