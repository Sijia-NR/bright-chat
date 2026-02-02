#!/usr/bin/env python3
"""
清理知识库测试数据脚本
Clear Knowledge Base Test Data
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings

def get_db_connection():
    """获取数据库连接"""
    connection_string = settings.DATABASE_URL
    engine = create_engine(connection_string)
    return engine.connect()

def list_test_data():
    """列出所有测试数据"""
    conn = get_db_connection()

    try:
        # 查询知识库分组
        groups = conn.execute(text("""
            SELECT id, name, user_id, created_at
            FROM knowledge_groups
            ORDER BY created_at DESC
        """)).fetchall()

        print(f"\n📁 知识库分组 ({len(groups)} 条):")
        for g in groups:
            print(f"  - {g.id}: {g.name} (用户: {g.user_id})")

        # 查询知识库
        bases = conn.execute(text("""
            SELECT id, name, group_id, created_at
            FROM knowledge_bases
            ORDER BY created_at DESC
        """)).fetchall()

        print(f"\n📚 知识库 ({len(bases)} 条):")
        for b in bases:
            print(f"  - {b.id}: {b.name} (分组: {b.group_id})")

        # 查询文档
        docs = conn.execute(text("""
            SELECT id, filename, knowledge_base_id, upload_status
            FROM documents
            ORDER BY created_at DESC
        """)).fetchall()

        print(f"\n📄 文档 ({len(docs)} 条):")
        for d in docs:
            print(f"  - {d.id}: {d.filename} (知识库: {d.knowledge_base_id}, 状态: {d.upload_status})")

        return {
            'groups': len(groups),
            'bases': len(bases),
            'docs': len(docs)
        }

    finally:
        conn.close()

def clear_test_data(confirm=False):
    """清理测试数据"""

    if not confirm:
        print("\n⚠️  警告：此操作将删除所有知识库数据！")
        print("请先运行脚本查看数据，确认无误后再执行删除。")
        print("\n使用方法：")
        print("  1. 查看数据: python clear_knowledge_test_data.py --list")
        print("  2. 删除数据: python clear_knowledge_test_data.py --clear")
        return

    conn = get_db_connection()
    transaction = conn.begin()

    try:
        print("\n🗑️  开始清理测试数据...")

        # 1. 先删除文档（因为 documents 表有外键指向 knowledge_bases）
        deleted_docs = conn.execute(text("""
            DELETE FROM documents
            WHERE knowledge_base_id IN (
                SELECT id FROM knowledge_bases
                WHERE group_id IN (
                    SELECT id FROM knowledge_groups
                )
            )
        """))
        print(f"  ✅ 删除文档: {deleted_docs.rowcount} 条")

        # 2. 删除知识库
        deleted_bases = conn.execute(text("""
            DELETE FROM knowledge_bases
            WHERE group_id IN (
                SELECT id FROM knowledge_groups
            )
        """))
        print(f"  ✅ 删除知识库: {deleted_bases.rowcount} 条")

        # 3. 删除知识库分组
        deleted_groups = conn.execute(text("DELETE FROM knowledge_groups"))
        print(f"  ✅ 删除知识库分组: {deleted_groups.rowcount} 条")

        # 4. 清理 ChromaDB 中的向量数据（如果需要）
        print("\n💡 提示：ChromaDB 向量数据未清理，如需清理请重启 ChromaDB 或手动删除 collection")

        transaction.commit()
        print("\n✅ 清理完成！")

    except Exception as e:
        transaction.rollback()
        print(f"\n❌ 清理失败: {e}")
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='清理知识库测试数据')
    parser.add_argument('--list', action='store_true', help='列出所有测试数据')
    parser.add_argument('--clear', action='store_true', help='删除所有测试数据')

    args = parser.parse_args()

    if args.list:
        print("=" * 60)
        print("知识库测试数据清单")
        print("=" * 60)
        list_test_data()

    elif args.clear:
        print("=" * 60)
        print("清理知识库测试数据")
        print("=" * 60)

        # 先显示数据
        counts = list_test_data()

        # 确认删除
        print(f"\n⚠️  即将删除:")
        print(f"  - {counts['groups']} 个知识库分组")
        print(f"  - {counts['bases']} 个知识库")
        print(f"  - {counts['docs']} 个文档")

        confirm = input("\n确认删除？(yes/no): ")
        if confirm.lower() in ['yes', 'y']:
            clear_test_data(confirm=True)
        else:
            print("\n❌ 已取消删除")

    else:
        print(__doc__)
        print("\n使用 --list 查看数据，使用 --clear 删除数据")
