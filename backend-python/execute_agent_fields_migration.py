#!/usr/bin/env python3
"""
Agent 字段迁移脚本 - 添加 order 和 enable_knowledge 字段
执行方式: python execute_agent_fields_migration.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

def check_column_exists(column_name: str) -> bool:
    """检查字段是否已存在"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = 'bright_chat'
            AND TABLE_NAME = 'agents'
            AND COLUMN_NAME = :column_name
        """), {"column_name": column_name})
        return result.scalar() > 0

def execute_migration():
    """执行迁移"""
    try:
        print("连接数据库...")
        print()

        # 检查字段是否已存在
        enable_knowledge_exists = check_column_exists("enable_knowledge")
        order_exists = check_column_exists("order")

        if enable_knowledge_exists and order_exists:
            print("✓ order 和 enable_knowledge 字段已存在，无需迁移")
            print()
            # 验证字段属性
            with engine.connect() as conn:
                result = conn.execute(text("DESCRIBE agents"))
                columns = {row[0]: row for row in result}
                for col_name in ["order", "enable_knowledge"]:
                    if col_name in columns:
                        print(f"  - {col_name}: {columns[col_name][1]} ✓")
            return True

        print("开始迁移...")
        print()

        with engine.begin() as conn:
            # 1. 添加 enable_knowledge 字段
            if not enable_knowledge_exists:
                print("1. 添加 enable_knowledge 字段...")
                conn.execute(text("""
                    ALTER TABLE `agents`
                    ADD COLUMN `enable_knowledge` BOOLEAN NULL DEFAULT TRUE
                    COMMENT '是否启用知识库功能'
                    AFTER `llm_model_id`
                """))
                print("  ✓ enable_knowledge 字段添加成功")
            else:
                print("  ✓ enable_knowledge 字段已存在")

            # 2. 添加 order 字段
            if not order_exists:
                print("2. 添加 order 字段...")
                conn.execute(text("""
                    ALTER TABLE `agents`
                    ADD COLUMN `order` INT NULL DEFAULT 0
                    COMMENT 'Agent 显示顺序（数字越小越靠前）'
                    AFTER `enable_knowledge`
                """))
                print("  ✓ order 字段添加成功")
            else:
                print("  ✓ order 字段已存在")

            # 3. 更新现有数据的默认值
            print("3. 更新现有数据的默认值...")
            conn.execute(text("UPDATE `agents` SET `order` = 0 WHERE `order` IS NULL"))
            conn.execute(text("UPDATE `agents` SET `enable_knowledge` = TRUE WHERE `enable_knowledge` IS NULL"))
            print("  ✓ 默认值更新完成")

            # 4. 添加索引
            print("4. 添加索引...")
            try:
                conn.execute(text("CREATE INDEX `idx_agents_order` ON `agents`(`order`)"))
                print("  ✓ idx_agents_order 索引创建成功")
            except Exception as e:
                if "Duplicate key name" in str(e):
                    print("  ✓ idx_agents_order 索引已存在")
                else:
                    raise

            try:
                conn.execute(text("CREATE INDEX `idx_agents_enable_knowledge` ON `agents`(`enable_knowledge`)"))
                print("  ✓ idx_agents_enable_knowledge 索引创建成功")
            except Exception as e:
                if "Duplicate key name" in str(e):
                    print("  ✓ idx_agents_enable_knowledge 索引已存在")
                else:
                    raise

            # 5. 设置字段为 NOT NULL（在更新完默认值后）
            print("5. 设置字段为 NOT NULL...")
            conn.execute(text("""
                ALTER TABLE `agents`
                MODIFY COLUMN `order` INT NOT NULL DEFAULT 0,
                MODIFY COLUMN `enable_knowledge` BOOLEAN NOT NULL DEFAULT TRUE
            """))
            print("  ✓ 字段属性更新完成")

        print()
        print("✓ 迁移成功完成！")
        print()

        # 验证
        print("验证迁移结果...")
        with engine.connect() as conn:
            result = conn.execute(text("DESCRIBE agents"))
            columns = {row[0]: row for row in result}
            for col_name in ["order", "enable_knowledge"]:
                if col_name in columns:
                    col_info = columns[col_name]
                    print(f"  - {col_name}: {col_info[1]} DEFAULT {col_info[3]} ✓")

        return True

    except Exception as e:
        print(f"\n✗ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Agent 字段迁移脚本")
    print("添加: order, enable_knowledge")
    print("=" * 60)
    print()

    success = execute_migration()

    if success:
        print("\n请重启后端服务以使更改生效")
        sys.exit(0)
    else:
        print("\n迁移失败，请检查错误信息")
        sys.exit(1)
