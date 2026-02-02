#!/usr/bin/env python3
"""运行数据库迁移脚本 - 使用 SQLAlchemy"""
import sys
from sqlalchemy import create_engine, text, Column, String, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

# 使用与 minimal_api.py 相同的数据库配置
DATABASE_URL = "mysql+pymysql://root:123456@47.116.218.206:13306/bright_chat"

def run_migration():
    """执行迁移 SQL"""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # 开始事务
        trans = conn.begin()

        try:
            print("开始执行数据库迁移...")

            # 1. 创建 llm_providers 表
            print("\n[1/4] 创建 llm_providers 表...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS llm_providers (
                    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
                    name VARCHAR(100) UNIQUE NOT NULL COMMENT 'e.g., openai-provider',
                    display_name VARCHAR(100) NOT NULL COMMENT 'e.g., OpenAI Provider',
                    base_url VARCHAR(500) NOT NULL COMMENT 'e.g., https://api.openai.com',
                    description TEXT COMMENT 'Optional description',
                    is_active BOOLEAN DEFAULT TRUE COMMENT 'Enable/disable provider',
                    auth_type VARCHAR(50) DEFAULT 'bearer' COMMENT 'bearer, api_key, none',
                    default_api_key TEXT COMMENT 'Default API key for models',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    created_by VARCHAR(36) COMMENT 'Creator user ID',
                    INDEX idx_name (name),
                    INDEX idx_is_active (is_active),
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                COMMENT='LLM 提供商配置表'
            """))
            print("  ✓ llm_providers 表创建成功")

            # 2. 检查并添加 provider_id 列
            print("\n[2/4] 添加 provider_id 列到 llm_models...")
            try:
                conn.execute(text("ALTER TABLE llm_models ADD COLUMN provider_id VARCHAR(36) NULL AFTER id"))
                conn.execute(text("ALTER TABLE llm_models ADD INDEX idx_provider_id (provider_id)"))
                conn.execute(text("ALTER TABLE llm_models ADD FOREIGN KEY (provider_id) REFERENCES llm_providers(id) ON DELETE SET NULL"))
                print("  ✓ provider_id 列添加成功")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("  - provider_id 列已存在，跳过")
                else:
                    raise

            # 3. 添加上架状态和同步追踪字段
            print("\n[3/4] 添加上架状态和同步追踪字段...")
            fields_to_add = [
                ("is_listed", "BOOLEAN DEFAULT FALSE COMMENT '是否上架到前端（只有上架的模型对用户可见）'", "idx_is_listed"),
                ("synced_from_provider", "BOOLEAN DEFAULT FALSE COMMENT 'Auto-discovered flag'", None),
                ("last_synced_at", "DATETIME NULL COMMENT 'Last sync timestamp'", None),
                ("external_model_id", "VARCHAR(200) NULL COMMENT 'Model ID in provider system'", None)
            ]

            for field_name, field_def, index_name in fields_to_add:
                try:
                    conn.execute(text(f"ALTER TABLE llm_models ADD COLUMN {field_name} {field_def}"))
                    print(f"  ✓ {field_name} 列添加成功")
                    if index_name:
                        conn.execute(text(f"ALTER TABLE llm_models ADD INDEX {index_name} ({field_name})"))
                        print(f"    索引 {index_name} 创建成功")
                except Exception as e:
                    if "Duplicate column name" in str(e):
                        print(f"  - {field_name} 列已存在，跳过")
                    else:
                        raise

            # 4. 修改 api_url 为可空
            print("\n[4/4] 修改 api_url 为可空...")
            try:
                conn.execute(text("ALTER TABLE llm_models MODIFY api_url VARCHAR(500) NULL"))
                print("  ✓ api_url 已修改为可空")
            except Exception as e:
                print(f"  ! 修改 api_url 时出错（可能已经修改过）: {e}")

            # 提交事务
            trans.commit()
            print("\n✓ 所有迁移执行成功！")

            # 验证表结构
            print("\n" + "="*60)
            print("验证表结构:")
            print("="*60)

            result = conn.execute(text("DESCRIBE llm_providers"))
            print("\nllm_providers 表结构:")
            for row in result:
                print(f"  {row[0]:<20} {row[1]:<35} {row[2]:<10}")

            result = conn.execute(text("""
                SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'bright_chat'
                AND TABLE_NAME = 'llm_models'
                AND COLUMN_NAME IN ('provider_id', 'is_listed', 'synced_from_provider', 'last_synced_at', 'external_model_id', 'api_url')
            """))
            print("\nllm_models 新增/修改字段:")
            for row in result:
                nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                print(f"  {row[0]:<25} {row[1]:<30} {nullable:<10} {row[4] or ''}")

        except Exception as e:
            trans.rollback()
            print(f"\n✗ 迁移失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    run_migration()
