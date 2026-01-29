#!/usr/bin/env python3
"""
在 Docker MySQL 数据库中创建缺失的表
"""

import pymysql

# Docker MySQL 连接配置（通过暴露的端口）
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 13306,
    'user': 'bright_chat',
    'password': 'BrightChat2024!@#',
    'database': 'bright_chat',
    'charset': 'utf8mb4'
}

print("="*80)
print("在 Docker MySQL 数据库中创建缺失的表")
print("="*80)
print(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
print(f"Database: {DB_CONFIG['database']}")
print()

try:
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 检查现有表
    cursor.execute('SHOW TABLES')
    existing_tables = [t[0] for t in cursor.fetchall()]

    print(f"现有表 ({len(existing_tables)}):")
    for table in sorted(existing_tables):
        print(f"  - {table}")
    print()

    # 定义需要创建的表
    tables_to_create = {}

    # knowledge_groups 表
    if 'knowledge_groups' not in existing_tables:
        tables_to_create['knowledge_groups'] = """
        CREATE TABLE knowledge_groups (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            user_id VARCHAR(36) NOT NULL,
            color VARCHAR(20) DEFAULT '#3B82F6',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

    # knowledge_bases 表
    if 'knowledge_bases' not in existing_tables:
        tables_to_create['knowledge_bases'] = """
        CREATE TABLE knowledge_bases (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            user_id VARCHAR(36) NOT NULL,
            group_id VARCHAR(36),
            embedding_model VARCHAR(100) DEFAULT 'bge-large-zh-v1.5',
            chunk_size INT DEFAULT 500,
            chunk_overlap INT DEFAULT 50,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_group_id (group_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

    # documents 表
    if 'documents' not in existing_tables:
        tables_to_create['documents'] = """
        CREATE TABLE documents (
            id VARCHAR(36) PRIMARY KEY,
            knowledge_base_id VARCHAR(36) NOT NULL,
            filename VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),
            file_size INT,
            chunk_count INT DEFAULT 0,
            upload_status VARCHAR(50) DEFAULT 'processing',
            error_message TEXT,
            uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            processed_at DATETIME,
            INDEX idx_kb_id (knowledge_base_id),
            FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

    # agents 表
    if 'agents' not in existing_tables:
        tables_to_create['agents'] = """
        CREATE TABLE agents (
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
            INDEX idx_created_by (created_by),
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

    # agent_executions 表
    if 'agent_executions' not in existing_tables:
        tables_to_create['agent_executions'] = """
        CREATE TABLE agent_executions (
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
            INDEX idx_user_id (user_id),
            FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

    if tables_to_create:
        print(f"需要创建 {len(tables_to_create)} 个表:")
        for table_name in tables_to_create.keys():
            print(f"  - {table_name}")
        print()

        # 创建表
        for table_name, create_sql in tables_to_create.items():
            print(f"创建表: {table_name}...")
            try:
                cursor.execute(create_sql)
                conn.commit()
                print(f"  ✓ {table_name} 创建成功")
            except Exception as e:
                print(f"  ✗ {table_name} 创建失败: {e}")
                conn.rollback()
    else:
        print("✓ 所有表都已存在，无需创建")

    print()
    print("="*80)
    print("验证")
    print("="*80)

    # 重新检查
    cursor.execute('SHOW TABLES')
    final_tables = [t[0] for t in cursor.fetchall()]

    print(f"\n最终表数量: {len(final_tables)}")
    all_tables = ['users', 'sessions', 'messages', 'message_favorites',
                  'llm_models', 'llm_providers',
                  'knowledge_groups', 'knowledge_bases', 'documents',
                  'agents', 'agent_executions']

    for table in all_tables:
        if table in final_tables:
            print(f"  ✓ {table}")
        else:
            print(f"  ✗ {table} (缺失)")

    cursor.close()
    conn.close()

    print()
    print("="*80)
    print("完成！")
    print("="*80)
    print("\n现在可以运行集成测试了:")
    print("  cd /data1/allresearchProject/Bright-Chat/backend-python")
    print("  python3 integration_test_full.py")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
