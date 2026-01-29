#!/usr/bin/env python3
"""
诊断文档切片数量不一致问题
对比数据库中的 chunk_count 和 ChromaDB 中的实际切片数量
"""

import sys
sys.path.insert(0, '/data1/allresearchProject/Bright-Chat/backend-python')

from app.core.database import DB, get_db
from app.models.knowledge_base import Document, KnowledgeBase
from app.rag.config import get_rag_config

def diagnose_chunks():
    print("=" * 80)
    print("诊断文档切片数量")
    print("=" * 80)

    db = next(get_db())

    # 查找有切片的文档
    docs = db.query(Document).filter(
        Document.chunk_count > 0
    ).order_by(Document.created_at.desc()).limit(10).all()

    print(f"\n找到 {len(docs)} 个有切片的文档\n")

    rag_config = get_rag_config()
    collection = rag_config.get_or_create_collection("knowledge_chunks")

    for doc in docs:
        print(f"文档: {doc.filename}")
        print(f"  ID: {doc.id}")
        print(f"  知识库 ID: {doc.knowledge_base_id}")
        print(f"  数据库中的 chunk_count: {doc.chunk_count}")
        print(f"  上传状态: {doc.upload_status}")

        # 从 ChromaDB 查询实际切片数量
        results = collection.get(
            where={"document_id": doc.id}
        )

        chromadb_count = len(results.get('documents', []))
        print(f"  ChromaDB 中的实际切片数: {chromadb_count}")

        # 显示前3个切片的索引
        if chromadb_count > 0:
            metadatas = results.get('metadatas', [])
            chunk_indices = [m.get('chunk_index', '?') for m in metadatas[:3]]
            print(f"  前3个切片索引: {chunk_indices}")

            if chromadb_count > 3:
                last_index = metadatas[-1].get('chunk_index', '?')
                print(f"  最后一个切片索引: {last_index}")

        # 检查是否一致
        if doc.chunk_count != chromadb_count:
            print(f"  ❌ 不一致! 数据库记录 {doc.chunk_count} 个，实际有 {chromadb_count} 个")

            # 可能的原因
            if chromadb_count == 0:
                print(f"  原因: ChromaDB 中没有找到该文档的切片")
                print(f"  可能: 文档处理失败或 ChromaDB 连接问题")
            elif chromadb_count < doc.chunk_count:
                print(f"  原因: 实际切片数少于记录数")
                print(f"  可能: 文档处理中断，只处理了部分切片")
            else:
                print(f"  原因: 实际切片数多于记录数")
                print(f"  可能: 数据库记录未更新或重复处理")
        else:
            print(f"  ✅ 一致")

        print("-" * 80)

    # 特别检查用户提到的文档
    target_doc_id = "bc34ecda-354a-4cfc-808a-b349f1348d01"
    target_doc = db.query(Document).filter(Document.id == target_doc_id).first()

    if target_doc:
        print(f"\n🔍 特别检查目标文档:")
        print(f"  文件名: {target_doc.filename}")
        print(f"  数据库 chunk_count: {target_doc.chunk_count}")

        results = collection.get(
            where={"document_id": target_doc_id}
        )
        actual_count = len(results.get('documents', []))
        print(f"  ChromaDB 实际数量: {actual_count}")

        if actual_count == 0:
            print(f"\n  ❌ 问题确认: ChromaDB 中没有该文档的切片!")
            print(f"  这就是为什么前端只显示 10 个切片且没有下一页的原因。")
            print(f"  因为 total_count = 0，所以分页组件不会显示。")
        elif actual_count != target_doc.chunk_count:
            print(f"\n  ❌ 数据不一致: 记录 {target_doc.chunk_count} 个，实际 {actual_count} 个")

            # 尝试获取切片看看
            if actual_count > 0:
                print(f"\n  尝试获取切片数据...")
                for i, (doc_text, metadata) in enumerate(zip(results['documents'][:3], results['metadatas'][:3])):
                    print(f"    切片 {i}:")
                    print(f"      chunk_index: {metadata.get('chunk_index')}")
                    print(f"      内容预览: {doc_text[:50]}...")
        else:
            print(f"\n  ✅ 数据一致，问题可能在其他地方")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    diagnose_chunks()
