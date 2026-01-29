#!/usr/bin/env python3
"""创建 RAG 相关数据库表"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# 数据库连接配置
DB_HOST = os.getenv("DB_HOST", "mysql")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USERNAME = os.getenv("DB_USERNAME", "bright_chat")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "BrightChat2024!@#")
DB_DATABASE = os.getenv("DB_DATABASE", "bright_chat")

# URL 编码密码
DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD)
DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"

print(f"连接到数据库: {DB_HOST}:{DB_PORT}/{DB_DATABASE}")
print(f"数据库URL: {DATABASE_URL}")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

try:
    with engine.connect() as conn:
        # 1. 创建知识库分组表
        print("\n创建 knowledge_groups 表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS knowledge_groups (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                user_id VARCHAR(36) NOT NULL,
                color VARCHAR(20) DEFAULT '#3B82F6',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))
        print("✓ knowledge_groups 表创建成功")

        # 2. 创建知识库表
        print("\n创建 knowledge_bases 表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS knowledge_bases (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                user_id VARCHAR(36) NOT NULL,
                group_id VARCHAR(36),
                embedding_model VARCHAR(100) DEFAULT 'voyage-3-large',
                chunk_size INT DEFAULT 500,
                chunk_overlap INT DEFAULT 50,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (group_id) REFERENCES knowledge_groups(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))
        print("✓ knowledge_bases 表创建成功")

        # 3. 创建文档表
        print("\n创建 documents 表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id VARCHAR(36) PRIMARY KEY,
                knowledge_base_id VARCHAR(36) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                file_type VARCHAR(50),
                file_size INT,
                chunk_count INT DEFAULT 0,
                upload_status VARCHAR(50) DEFAULT 'processing',
                error_message TEXT,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed_at DATETIME,
                FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))
        print("✓ documents 表创建成功")

        # 提交事务
        conn.commit()

        # 验证表创建
        print("\n验证表创建...")
        result = conn.execute(text("""
            SELECT TABLE_NAME
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = 'bright_chat'
            AND TABLE_NAME IN ('knowledge_groups', 'knowledge_bases', 'documents')
        """))
        tables = [row[0] for row in result]
        print(f"✓ 已创建的 RAG 表: {', '.join(tables)}")

        print("\n✅ 所有 RAG 数据库表创建成功!")

except Exception as e:
    print(f"\n❌ 创建表失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
