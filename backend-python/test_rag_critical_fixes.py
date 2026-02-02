#!/usr/bin/env python3
"""
RAG 模块关键修复验证测试
RAG Critical Fixes Verification Test

验证以下 4 个关键修复:
1. RAG-CRITICAL-001: 删除知识库时清理 ChromaDB 向量
2. RAG-CRITICAL-002: 删除文档时清理 ChromaDB 向量
3. RAG-CRITICAL-003: 搜索多知识库时的 $in 操作符问题
4. RAG-CRITICAL-004: BGE 模型线程安全
"""
import asyncio
import sys
import os
import threading
import time
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.rag.config import get_rag_config, KNOWLEDGE_COLLECTION
from app.rag.document_processor import DocumentProcessor
from app.rag.retriever import RAGRetriever


class RAGCriticalFixesTest:
    """RAG 关键修复测试"""

    def __init__(self):
        """初始化测试"""
        self.engine = create_engine(settings.DATABASE_URL, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.rag_config = get_rag_config()
        self.test_user_id = None
        self.test_kb_ids = []
        self.test_doc_ids = []

    def setup_test_data(self):
        """创建测试数据"""
        print("\n=== 设置测试数据 ===")
        db: Session = self.SessionLocal()

        try:
            # 创建测试用户
            test_user = db.query(User).filter(User.username == "rag_test_user").first()
            if not test_user:
                test_user = User(
                    username="rag_test_user",
                    password_hash="test_hash",
                    role="user"
                )
                db.add(test_user)
                db.commit()
                db.refresh(test_user)
            self.test_user_id = test_user.id
            print(f"✓ 测试用户: {test_user.username} (ID: {test_user.id})")

            # 创建两个测试知识库
            for i in range(1, 3):
                kb = db.query(KnowledgeBase).filter(
                    KnowledgeBase.name == f"test_kb_{i}",
                    KnowledgeBase.user_id == self.test_user_id
                ).first()

                if not kb:
                    kb = KnowledgeBase(
                        name=f"test_kb_{i}",
                        description=f"测试知识库 {i}",
                        user_id=self.test_user_id,
                        embedding_model="bge-large-zh-v1.5",
                        chunk_size=500,
                        chunk_overlap=50,
                        is_active=True
                    )
                    db.add(kb)
                    db.commit()
                    db.refresh(kb)

                self.test_kb_ids.append(kb.id)
                print(f"✓ 测试知识库 {i}: {kb.name} (ID: {kb.id})")

        finally:
            db.close()

    async def test_delete_knowledge_base_cleanup(self):
        """测试 1: 删除知识库时清理 ChromaDB 向量 (RAG-CRITICAL-001)"""
        print("\n" + "="*60)
        print("测试 1: 删除知识库时清理 ChromaDB 向量")
        print("="*60)

        db: Session = self.SessionLocal()

        try:
            # 创建测试知识库
            kb = KnowledgeBase(
                name="test_delete_kb",
                description="测试删除知识库",
                user_id=self.test_user_id,
                embedding_model="bge-large-zh-v1.5",
                is_active=True
            )
            db.add(kb)
            db.commit()
            db.refresh(kb)
            kb_id = kb.id
            print(f"✓ 创建测试知识库: {kb_id}")

            # 上传测试文档（创建一些向量）
            processor = DocumentProcessor(self.rag_config)

            # 创建测试文件
            test_file = "/tmp/test_delete_kb.txt"
            with open(test_file, 'w') as f:
                f.write("这是测试文档内容。" * 100)

            # 处理文档
            result = await processor.process_document(
                file_path=test_file,
                knowledge_base_id=kb_id,
                user_id=self.test_user_id,
                filename="test_delete.txt"
            )
            print(f"✓ 处理测试文档: {result['document_id']}")

            # 验证向量存在
            collection = self.rag_config.get_or_create_collection(KNOWLEDGE_COLLECTION)
            count_before = collection.count(where={"knowledge_base_id": kb_id})
            print(f"✓ 删除前向量数量: {count_before}")

            assert count_before > 0, "应该有向量数据"

            # 使用 DocumentProcessor 删除知识库向量
            success = await processor.delete_knowledge_base(kb_id)
            assert success, "删除应该成功"
            print(f"✓ 调用 delete_knowledge_base({kb_id})")

            # 验证向量已删除
            count_after = collection.count(where={"knowledge_base_id": kb_id})
            print(f"✓ 删除后向量数量: {count_after}")

            assert count_after == 0, "向量应该被完全删除"

            # 清理 MySQL 记录
            db.delete(kb)
            db.commit()
            print(f"✓ 清理 MySQL 记录")

            # 清理测试文件
            if os.path.exists(test_file):
                os.remove(test_file)

            print("✅ 测试 1 通过: 删除知识库时正确清理了 ChromaDB 向量")
            return True

        except Exception as e:
            print(f"❌ 测试 1 失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.close()

    async def test_delete_document_cleanup(self):
        """测试 2: 删除文档时清理 ChromaDB 向量 (RAG-CRITICAL-002)"""
        print("\n" + "="*60)
        print("测试 2: 删除文档时清理 ChromaDB 向量")
        print("="*60)

        db: Session = self.SessionLocal()

        try:
            # 使用第一个测试知识库
            kb_id = self.test_kb_ids[0]

            # 上传测试文档
            processor = DocumentProcessor(self.rag_config)

            test_file = "/tmp/test_delete_doc.txt"
            with open(test_file, 'w') as f:
                f.write("这是测试删除文档的内容。" * 100)

            result = await processor.process_document(
                file_path=test_file,
                knowledge_base_id=kb_id,
                user_id=self.test_user_id,
                filename="test_delete_doc.txt"
            )
            doc_id = result['document_id']
            print(f"✓ 创建测试文档: {doc_id}")

            # 验证向量存在
            collection = self.rag_config.get_or_create_collection(KNOWLEDGE_COLLECTION)
            count_before = collection.count(where={"document_id": doc_id})
            print(f"✓ 删除前向量数量: {count_before}")
            assert count_before > 0, "应该有向量数据"

            # 使用 DocumentProcessor 删除文档向量
            success = await processor.delete_document(doc_id)
            assert success, "删除应该成功"
            print(f"✓ 调用 delete_document({doc_id})")

            # 验证向量已删除
            count_after = collection.count(where={"document_id": doc_id})
            print(f"✓ 删除后向量数量: {count_after}")
            assert count_after == 0, "向量应该被完全删除"

            # 清理测试文件
            if os.path.exists(test_file):
                os.remove(test_file)

            print("✅ 测试 2 通过: 删除文档时正确清理了 ChromaDB 向量")
            return True

        except Exception as e:
            print(f"❌ 测试 2 失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.close()

    async def test_multi_kb_search(self):
        """测试 3: 搜索多知识库功能 (RAG-CRITICAL-003)"""
        print("\n" + "="*60)
        print("测试 3: 搜索多知识库（不使用 $in 操作符）")
        print("="*60)

        db: Session = self.SessionLocal()

        try:
            processor = DocumentProcessor(self.rag_config)
            retriever = RAGRetriever(self.rag_config)

            # 为两个知识库上传不同的测试文档
            for idx, kb_id in enumerate(self.test_kb_ids):
                test_file = f"/tmp/test_search_kb_{idx + 1}.txt"
                content = f"知识库 {idx + 1} 的独特内容。关键词{idx + 1}。" * 50

                with open(test_file, 'w') as f:
                    f.write(content)

                result = await processor.process_document(
                    file_path=test_file,
                    knowledge_base_id=kb_id,
                    user_id=self.test_user_id,
                    filename=f"test_search_{idx + 1}.txt"
                )
                print(f"✓ 知识库 {idx + 1} 上传文档: {result['document_id']}")

                self.test_doc_ids.append(result['document_id'])

            # 等待向量索引完成
            await asyncio.sleep(1)

            # 测试搜索单个知识库
            print("\n--- 测试搜索单个知识库 ---")
            results = await retriever.search(
                query="关键词1",
                knowledge_base_ids=[self.test_kb_ids[0]],
                user_id=self.test_user_id,
                top_k=5
            )
            print(f"✓ 搜索单个知识库结果数: {len(results)}")
            assert len(results) > 0, "应该找到结果"

            # 验证结果都来自正确的知识库
            for result in results:
                assert result['metadata']['knowledge_base_id'] == self.test_kb_ids[0], \
                    f"结果应来自知识库 {self.test_kb_ids[0]}"
            print(f"✓ 所有结果都来自正确的知识库")

            # 测试搜索多个知识库（不使用 $in）
            print("\n--- 测试搜索多个知识库 ---")
            results = await retriever.search(
                query="关键词",
                knowledge_base_ids=self.test_kb_ids,
                user_id=self.test_user_id,
                top_k=10
            )
            print(f"✓ 搜索多个知识库结果数: {len(results)}")
            assert len(results) > 0, "应该找到结果"

            # 验证结果来自不同的知识库
            kb_ids_in_results = set(r['metadata']['knowledge_base_id'] for r in results)
            print(f"✓ 结果来自知识库: {kb_ids_in_results}")
            assert len(kb_ids_in_results) > 1, "应该有多个知识库的结果"

            # 清理测试文件
            for idx in range(2):
                test_file = f"/tmp/test_search_kb_{idx + 1}.txt"
                if os.path.exists(test_file):
                    os.remove(test_file)

            print("✅ 测试 3 通过: 多知识库搜索正确工作（不依赖 $in 操作符）")
            return True

        except Exception as e:
            print(f"❌ 测试 3 失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.close()

    def test_thread_safety(self):
        """测试 4: BGE 模型线程安全 (RAG-CRITICAL-004)"""
        print("\n" + "="*60)
        print("测试 4: BGE 模型线程安全的懒加载")
        print("="*60)

        try:
            # 重置 RAG 配置以确保从零开始
            from app.rag.config import reset_rag_config
            reset_rag_config()

            # 获取新的配置实例
            config = get_rag_config()

            # 验证初始状态
            assert config._embedding_model is None, "初始状态模型应该是 None"
            assert hasattr(config, '_model_lock'), "应该有线程锁"
            print("✓ 初始状态正确: 模型未加载，锁已存在")

            # 并发加载测试
            results = []
            errors = []

            def load_model(thread_id):
                """线程函数：加载模型"""
                try:
                    # 访问 embedding_model 属性触发懒加载
                    model = config.embedding_model
                    results.append((thread_id, id(model)))
                    print(f"  线程 {thread_id}: 加载成功，模型 ID: {id(model)}")
                except Exception as e:
                    errors.append((thread_id, str(e)))
                    print(f"  线程 {thread_id}: 加载失败 - {e}")

            # 创建多个线程同时访问模型
            print("\n--- 并发加载测试（10 个线程） ---")
            threads = []
            for i in range(10):
                thread = threading.Thread(target=load_model, args=(i,))
                threads.append(thread)

            # 启动所有线程
            start_time = time.time()
            for thread in threads:
                thread.start()

            # 等待所有线程完成
            for thread in threads:
                thread.join()
            elapsed = time.time() - start_time

            print(f"\n✓ 所有线程完成，耗时: {elapsed:.2f}秒")

            # 验证结果
            assert len(errors) == 0, f"应该没有错误，但遇到: {errors}"
            assert len(results) == 10, "应该有 10 个成功结果"

            # 验证所有线程使用的是同一个模型实例
            model_ids = [model_id for _, model_id in results]
            assert len(set(model_ids)) == 1, "所有线程应该使用同一个模型实例"
            print(f"✓ 所有线程使用同一个模型实例 (ID: {model_ids[0]})")

            # 验证模型确实被加载了
            assert config._embedding_model is not None, "模型应该被加载"
            print("✓ 模型已正确加载")

            # 测试双重检查锁
            print("\n--- 测试双重检查锁 ---")
            model_1 = config.embedding_model
            model_2 = config.embedding_model
            assert id(model_1) == id(model_2), "多次访问应该返回同一个实例"
            print(f"✓ 双重检查锁工作正常")

            print("✅ 测试 4 通过: BGE 模型线程安全的懒加载正确实现")
            return True

        except Exception as e:
            print(f"❌ 测试 4 失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def cleanup_test_data(self):
        """清理测试数据"""
        print("\n=== 清理测试数据 ===")
        db: Session = self.SessionLocal()

        try:
            # 删除测试文档向量
            processor = DocumentProcessor(self.rag_config)
            for doc_id in self.test_doc_ids:
                try:
                    await processor.delete_document(doc_id)
                    print(f"✓ 删除测试文档向量: {doc_id}")
                except:
                    pass

            # 删除测试知识库
            for kb_id in self.test_kb_ids:
                try:
                    await processor.delete_knowledge_base(kb_id)
                    print(f"✓ 删除测试知识库向量: {kb_id}")
                except:
                    pass

            # 删除数据库记录
            db.query(KnowledgeBase).filter(
                KnowledgeBase.user_id == self.test_user_id,
                KnowledgeBase.name.in_([f"test_kb_{i}" for i in range(1, 3)])
            ).delete(synchronize_session=False)

            db.query(KnowledgeBase).filter(
                KnowledgeBase.user_id == self.test_user_id,
                KnowledgeBase.name == "test_delete_kb"
            ).delete(synchronize_session=False)

            db.commit()
            print("✓ 清理数据库记录")

        finally:
            db.close()

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("RAG 模块关键修复验证测试")
        print("="*60)

        # 设置测试数据
        self.setup_test_data()

        # 运行测试
        test_results = []

        # 测试 1: 删除知识库清理向量
        test_results.append(await self.test_delete_knowledge_base_cleanup())

        # 测试 2: 删除文档清理向量
        test_results.append(await self.test_delete_document_cleanup())

        # 测试 3: 多知识库搜索
        test_results.append(await self.test_multi_kb_search())

        # 测试 4: 线程安全
        test_results.append(self.test_thread_safety())

        # 清理测试数据
        await self.cleanup_test_data()

        # 输出总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        print(f"总测试数: {len(test_results)}")
        print(f"通过: {sum(test_results)}")
        print(f"失败: {len(test_results) - sum(test_results)}")

        test_names = [
            "删除知识库清理向量",
            "删除文档清理向量",
            "多知识库搜索",
            "BGE 模型线程安全"
        ]

        for i, (name, result) in enumerate(zip(test_names, test_results), 1):
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {i}. {name}: {status}")

        if all(test_results):
            print("\n🎉 所有测试通过！")
            return 0
        else:
            print("\n⚠️  部分测试失败")
            return 1


async def main():
    """主函数"""
    test = RAGCriticalFixesTest()
    return await test.run_all_tests()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
