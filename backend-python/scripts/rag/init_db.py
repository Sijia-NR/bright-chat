#!/usr/bin/env python3
"""
数据库初始化脚本 - 知识库和Agent功能
Database Initialization Script - Knowledge Base and Agent Feature

用法 / Usage:
    python scripts/rag/init_db.py

说明 / Description:
    此脚本会自动创建知识库和Agent功能所需的数据表
    This script automatically creates tables required for knowledge base and agent features
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.database import Base, engine, check_db_connection
from app.models.knowledge_base import KnowledgeGroup, KnowledgeBase, Document
from app.models.agent import Agent, AgentExecution
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_knowledge_tables():
    """创建知识库和Agent相关的数据表"""
    logger.info("开始创建知识库和Agent功能数据表...")

    try:
        # 检查数据库连接
        if not check_db_connection():
            logger.error("数据库连接失败，请检查配置")
            return False

        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("✓ 数据表创建成功")

        # 验证表是否创建成功
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT TABLE_NAME
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME IN (
                        'knowledge_groups',
                        'knowledge_bases',
                        'documents',
                        'agents',
                        'agent_executions'
                    )
                ORDER BY TABLE_NAME
            """))
            tables = [row[0] for row in result]
            logger.info(f"✓ 已创建的数据表: {', '.join(tables)}")

        # 插入默认 Agent 模板（可选）
        insert_default_agents()

        logger.info("=" * 50)
        logger.info("✓ 知识库和Agent功能数据库初始化完成!")
        logger.info("=" * 50)
        return True

    except Exception as e:
        logger.error(f"✗ 数据库初始化失败: {e}")
        return False


def insert_default_agents():
    """插入默认Agent模板"""
    try:
        from app.models.user import User
        from app.models.agent import Agent, PREDEFINED_TOOLS
        from app.core.database import SessionLocal

        with SessionLocal() as db:
            # 查找admin用户
            admin_user = db.query(User).filter(User.username == 'admin').first()

            if not admin_user:
                logger.warning("未找到admin用户，跳过默认Agent创建")
                return

            # 检查是否已经存在默认Agent
            existing_agent = db.query(Agent).filter(Agent.name == 'general_assistant').first()
            if existing_agent:
                logger.info("默认Agent已存在，跳过创建")
                return

            # 创建通用助手Agent
            general_agent = Agent(
                name='general_assistant',
                display_name='通用助手',
                description='能够回答各种问题、执行计算、搜索信息的通用AI助手',
                agent_type='tool',
                system_prompt='你是一个有用的AI助手。你可以使用各种工具来帮助用户解决问题。在回答问题时，要简洁、准确、友好。',
                knowledge_base_ids=None,
                tools=['calculator', 'datetime', 'knowledge_search'],
                config={
                    'temperature': 0.7,
                    'max_steps': 10,
                    'timeout': 300
                },
                is_active=True,
                created_by=admin_user.id
            )

            db.add(general_agent)
            db.commit()

            logger.info("✓ 默认Agent模板创建成功")

    except Exception as e:
        logger.warning(f"创建默认Agent时出错: {e}")


def main():
    """主函数"""
    print("\n" + "=" * 50)
    print("BrightChat - 知识库和Agent功能数据库初始化")
    print("=" * 50 + "\n")

    success = create_knowledge_tables()

    if success:
        print("\n✓ 初始化成功完成!")
        print("\n下一步:")
        print("1. 启动 ChromaDB 服务 (Docker): docker-compose up -d chromadb")
        print("2. 启动后端服务: python backend-python/run.py")
        print("3. 访问前端开始使用知识库和Agent功能\n")
    else:
        print("\n✗ 初始化失败，请检查错误日志\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
