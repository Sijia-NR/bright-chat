"""
手动处理文档 - 跳过后台任务直接处理

用于测试文档处理、切片和向量化功能
"""
import sys
import asyncio
from pathlib import Path
from pathlib import Path as PathlibPath

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.rag.document_processor import DocumentProcessor
from app.models.knowledge_base import Document, KnowledgeBase
from app.rag.config import get_rag_config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_pending_document():
    """处理第一个pending状态的文档"""
    print("=" * 60)
    print("手动处理文档 - 切片和向量化")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 查找pending状态的文档
        doc = db.query(Document).filter(
            Document.upload_status == "pending"
        ).first()

        if not doc:
            print("❌ 没有找到pending状态的文档")
            return False

        print(f"\n[1] 找到文档: {doc.filename}")
        print(f"   文档ID: {doc.id}")
        print(f"   知识库ID: {doc.knowledge_base_id}")
        print(f"   文件大小: {doc.file_size} bytes")

        # 获取知识库信息
        kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == doc.knowledge_base_id
        ).first()

        if not kb:
            print("❌ 知识库不存在")
            return False

        print(f"\n[2] 知识库信息:")
        print(f"   名称: {kb.name}")
        print(f"   嵌入模型: {kb.embedding_model}")
        print(f"   分块大小: {kb.chunk_size}, 重叠: {kb.chunk_overlap}")

        # 查找文件
        uploads_dir = PathlibPath("uploads/documents")

        # 首先尝试精确匹配
        file_path = None
        for f in uploads_dir.glob(f"*{doc.id}*"):
            file_path = f
            break

        # 如果没找到，尝试匹配文件名
        if not file_path:
            for f in uploads_dir.glob("*"):
                if doc.filename in f.name or f.suffix in ['.txt', '.md', '.pdf', '.docx']:
                    # 尝试匹配最近修改的文件
                    file_path = f
                    break

        if not file_path or not file_path.exists():
            print(f"❌ 文件不存在")
            # 列出uploads目录下的所有文件
            if uploads_dir.exists():
                files = list(uploads_dir.glob("*"))
                print(f"\nuploads/documents目录下的文件:")
                for f in files[:10]:
                    stat = f.stat()
                    print(f"  - {f.name} ({stat.st_size} bytes)")
            return False

        print(f"\n[3] 文件路径: {file_path}")
        print(f"   文件存在: {file_path.exists()}")
        print(f"   文件大小: {file_path.stat().st_size} bytes")

        # 更新状态为processing
        print(f"\n[4] 更新文档状态为 processing...")
        doc.upload_status = "processing"
        db.commit()

        # 处理文档
        print(f"\n[5] 开始处理文档...")
        processor = DocumentProcessor()

        try:
            # 处理文档（async方法）
            import asyncio

            async def process_async():
                return await processor.process_document(
                    file_path=str(file_path),
                    knowledge_base_id=kb.id,
                    user_id=kb.user_id,
                    filename=doc.filename,
                    chunk_size=kb.chunk_size,
                    chunk_overlap=kb.chunk_overlap,
                    document_id=doc.id
                )

            result = asyncio.run(process_async())
            chunk_count = result.get('chunk_count', 0)
            chunks = result.get('chunks', [])

            print(f"✅ 文档处理成功！")
            print(f"   生成切片数: {len(chunks)}")

            # 更新状态为completed
            doc.upload_status = "completed"
            doc.chunk_count = len(chunks)
            db.commit()

            # 验证ChromaDB中的数据
            print(f"\n[6] 验证ChromaDB中的数据...")
            rag_config = get_rag_config()
            collection = rag_config.get_or_create_collection("knowledge_chunks")

            # 查询该文档的切片
            results = collection.get(
                where={"document_id": doc.id}
            )

            vector_count = len(results.get('ids', []))
            print(f"✅ ChromaDB中找到 {vector_count} 个向量")

            if vector_count > 0:
                print(f"\n   前3个切片预览:")
                for i in range(min(3, len(results.get('documents', [])))):
                    content = results['documents'][i][:100].replace('\n', ' ')
                    metadata = results['metadatas'][i] if results.get('metadatas') else {}
                    print(f"   切片 {i+1}: {content}...")
                    print(f"          元数据: knowledge_base_id={metadata.get('knowledge_base_id')}, "
                          f"chunk_index={metadata.get('chunk_index')}")

            return True

        except Exception as e:
            logger.error(f"文档处理失败: {e}", exc_info=True)
            doc.upload_status = "failed"
            doc.error_message = str(e)
            db.commit()
            print(f"❌ 文档处理失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    finally:
        db.close()


if __name__ == "__main__":
    try:
        success = process_pending_document()
        if success:
            print("\n" + "=" * 60)
            print("✅ 文档处理完成！")
            print("=" * 60)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 处理异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
