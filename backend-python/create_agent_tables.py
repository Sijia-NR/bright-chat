#!/usr/bin/env python3
"""
在 Docker MySQL 数据库中创建 agents 相关表（无外键约束版本）
"""

import pymysql

# Docker MySQL 连接配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 13306,
    'user': 'bright_chat',
    'password': 'BrightChat2024!@#',
    'database': 'bright_chat',
    'charset': 'utf8mb4'
}

print("="*80)
print("创建 agents 相关表")
print("="*80)

try:
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # agents 表（不使用外键约束）
    print("\n创建表: agents...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agents (
        id VARCHAR(36) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        display_name VARCHAR(255),
        description TEXT,
        agent_type VARCHAR(50) NOT NULL,
        system_prompt TEXT,
        knowledge_base_ids JSON,
        tools JSON,
        config JSON,
        is_active BOOLEAN DEFAULT TRUE,
        created_by VARCHAR(36),
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_created_by (created_by)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    conn.commit()
    print("  ✓ agents 创建成功")

    # agent_executions 表（不使用外键约束）
    print("\n创建表: agent_executions...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_executions (
        id VARCHAR(36) PRIMARY KEY,
        agent_id VARCHAR(36) NOT NULL,
        user_id VARCHAR(36) NOT NULL,
        session_id VARCHAR(36),
        input_prompt TEXT NOT NULL,
        status VARCHAR(50) DEFAULT 'running',
        steps INT DEFAULT 0,
        result TEXT,
        error_message TEXT,
        started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME,
        INDEX idx_agent_id (agent_id),
        INDEX idx_user_id (user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    conn.commit()
    print("  ✓ agent_executions 创建成功")

    print()
    print("="*80)
    print("验证")
    print("="*80)

    cursor.execute('SHOW TABLES')
    tables = [t[0] for t in cursor.fetchall()]

    all_tables = ['users', 'sessions', 'messages', 'message_favorites',
                  'llm_models', 'llm_providers',
                  'knowledge_groups', 'knowledge_bases', 'documents',
                  'agents', 'agent_executions']

    print(f"\n最终表数量: {len(tables)}")
    for table in all_tables:
        if table in tables:
            print(f"  ✓ {table}")
        else:
            print(f"  ✗ {table} (缺失)")

    cursor.close()
    conn.close()

    print()
    print("="*80)
    print("完成！所有表已创建")
    print("="*80)
    print("\n现在可以运行集成测试了:")
    print("  cd /data1/allresearchProject/Bright-Chat/backend-python")
    print("  python3 integration_test_full.py")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
