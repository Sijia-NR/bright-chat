#!/usr/bin/env python3
"""
临时迁移脚本 - 添加 api_format 字段到 llm_models 表
执行方式: python execute_migration.py
"""
import pymysql
import sys

# 数据库连接配置
DB_CONFIG = {
    'host': '47.116.218.206',
    'port': 13306,
    'user': 'root',
    'password': '123456',
    'database': 'bright_chat',
    'charset': 'utf8mb4'
}

def check_column_exists(cursor):
    """检查 api_format 字段是否已存在"""
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = 'bright_chat'
        AND TABLE_NAME = 'llm_models'
        AND COLUMN_NAME = 'api_format'
    """)
    return cursor.fetchone()[0] > 0

def execute_migration():
    """执行迁移"""
    connection = None
    try:
        print("连接数据库...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # 检查字段是否已存在
        if check_column_exists(cursor):
            print("✓ api_format 字段已存在，无需迁移")
            return True

        print("开始迁移...")

        # 1. 备份表（可选，如果数据很重要）
        print("1. 创建备份表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_models_backup_20260125
            AS SELECT * FROM llm_models
        """)
        print("✓ 备份完成")

        # 2. 添加 api_format 字段
        print("2. 添加 api_format 字段...")
        cursor.execute("""
            ALTER TABLE llm_models
            ADD COLUMN api_format ENUM('openai', 'ias')
            NOT NULL
            DEFAULT 'openai'
            COMMENT 'API format: openai standard or ias custom'
            AFTER model_type
        """)
        print("✓ 字段添加成功")

        # 3. 创建索引
        print("3. 创建索引...")
        cursor.execute("""
            CREATE INDEX idx_api_format ON llm_models(api_format)
        """)
        print("✓ 索引创建成功")

        # 提交事务
        connection.commit()
        print("\n✓ 迁移成功完成！")

        # 验证
        print("\n验证迁移结果...")
        cursor.execute("DESCRIBE llm_models")
        columns = cursor.fetchall()
        for col in columns:
            if col[0] == 'api_format':
                print(f"  - {col[0]}: {col[1]} ✓")

        return True

    except pymysql.Error as e:
        print(f"\n✗ 迁移失败: {e}")
        if connection:
            connection.rollback()
        return False

    except Exception as e:
        print(f"\n✗ 未知错误: {e}")
        if connection:
            connection.rollback()
        return False

    finally:
        if connection:
            connection.close()
            print("\n数据库连接已关闭")

if __name__ == "__main__":
    print("=" * 60)
    print("LLM Models API Format 迁移脚本")
    print("=" * 60)
    print()

    success = execute_migration()

    if success:
        print("\n请重启后端服务以使更改生效")
        sys.exit(0)
    else:
        print("\n迁移失败，请检查错误信息")
        sys.exit(1)
