#!/usr/bin/env python3
"""
诊断文档上传问题：检查为什么只有10个切片被插入到ChromaDB
"""

import sys
sys.path.insert(0, '/data1/allresearchProject/Bright-Chat/backend-python')

from app.core.database import get_db
from app.models.knowledge_base import Document
from app.rag.config import get_rag_config

def diagnose_document_upload():
    """诊断文档上传问题"""
    print("=" * 80)
    print("诊断文档切片上传问题")
    print("=" * 80)

    db = next(get_db())

    # 查找目标文档
    doc_id = "bc34ecda-354a-4cfc-808a-b349f1348d01"
    doc = db.query(Document).filter(Document.id == doc_id).first()

    if not doc:
        print(f"\n❌ 未找到文档: {doc_id}")
        return

    print(f"\n📄 文档信息:")
    print(f"  文件名: {doc.filename}")
    print(f"  数据库 chunk_count: {doc.chunk_count}")
    print(f"  上传状态: {doc.upload_status}")
    print(f"  文件大小: {doc.file_size} 字节")
    print(f"  处理时间: {doc.processed_at}")

    # 检查 ChromaDB
    print(f"\n🔍 检查 ChromaDB 数据...")
    try:
        rag_config = get_rag_config()
        collection = rag_config.get_or_create_collection("knowledge_chunks")

        # 查询该文档的所有切片
        results = collection.get(
            where={"document_id": doc_id}
        )

        actual_count = len(results.get('documents', []))
        print(f"  ChromaDB 中的实际切片数: {actual_count}")

        if actual_count == 0:
            print(f"\n❌ 问题确认: ChromaDB 中完全没有该文档的切片!")
            print(f"\n可能原因:")
            print(f"  1. 文档上传时处理失败，但没有正确记录错误")
            print(f"  2. ChromaDB 插入时抛出异常，但被上层捕获")
            print(f"  3. collection.add() 调用失败，但没有抛出异常")
        elif actual_count < doc.chunk_count:
            print(f"\n❌ 数据不完整: 缺少 {doc.chunk_count - actual_count} 个切片")

            # 检查切片索引
            metadatas = results.get('metadatas', [])
            chunk_indices = [m.get('chunk_index') for m in metadatas]

            print(f"\n  已插入的切片索引: {chunk_indices}")

            # 检查是否有连续的索引
            if len(chunk_indices) <= 10:
                print(f"\n  ⚠️  只有前10个切片被插入!")
                print(f"\n  可能原因:")
                print(f"  1. ChromaDB collection.add() 有默认的批次大小限制")
                print(f"  2. 插入过程中出现错误，但只插入了前10个")
                print(f"  3. embed_documents 只处理了前10个文本")

                # 检查 ChromaDB 配置
                print(f"\n🔍 检查 ChromaDB 配置...")
                print(f"  Collection 名称: {collection.name}")
                print(f"  Collection ID: {collection.id}")

                # 尝试获取 collection 的配置
                try:
                    metadata = collection.metadata
                    print(f"  Collection metadata: {metadata}")
                except:
                    print(f"  无法获取 Collection metadata")

        else:
            print(f"\n✅ 数据完整!")

        # 显示第一个和最后一个切片的内容预览
        if actual_count > 0:
            documents = results.get('documents', [])
            print(f"\n📝 第一个切片预览:")
            print(f"  {documents[0][:100]}...")

            if actual_count > 1:
                print(f"\n📝 最后一个切片预览:")
                print(f"  {documents[-1][:100]}...")

    except Exception as e:
        print(f"\n❌ 检查 ChromaDB 失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("建议修复方案:")
    print("=" * 80)
    print("\n1. 重新上传文档")
    print("   - 删除当前文档")
    print("   - 重新上传文件")
    print("   - 等待处理完成（确保状态为 'completed'）")

    print("\n2. 检查文档处理代码")
    print("   - 查看 _store_to_chromadb 方法")
    print("   - 检查是否有批次大小限制")
    print("   - 添加详细的日志记录")

    print("\n3. 检查 ChromaDB 配置")
    print("   - 确认 ChromaDB 版本兼容")
    print("   - 检查 collection.add() 的限制")
    print("   - 考虑分批插入，每批不超过一定数量")

if __name__ == "__main__":
    diagnose_document_upload()
