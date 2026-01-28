#!/usr/bin/env python3
"""
Bright-Chat 数据库完整初始化脚本
Database Complete Initialization Script for Bright-Chat

功能：
1. 创建所有必要的数据库表
2. 插入默认用户数据
3. 插入LLM模型和提供商示例数据
4. 初始化知识库和Agent相关表

Usage:
    python init_database.py [--reset]
"""

import os
import sys
import uuid
import bcrypt
import pymysql
from typing import List, Dict, Any
from datetime import datetime

# 数据库配置
DB_HOST = "AIWorkbench-mysql"
DB_PORT = 3306
DB_USERNAME = "root"
DB_PASSWORD = "root_password_change_me"
DB_DATABASE = "bright_chat"

print("=" * 80)
print("Bright-Chat 数据库初始化脚本")
print("Bright-Chat Database Initialization Script")
print("=" * 80)
print(f"数据库: {DB_USERNAME}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}")
print()


def get_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USERNAME,
        password=DB_PASSWORD,
        database=DB_DATABASE,
        charset='utf8mb4'
    )


def hash_password(password: str) -> str:
    """生成bcrypt密码哈希"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_tables():
    """创建数据库表"""
    print("\n" + "=" * 80)
    print("步骤 1: 创建数据库表")
    print("Step 1: Creating Database Tables")
    print("=" * 80)

    conn = get_connection()
    cursor = conn.cursor()

    # 1. 用户表
    print("\n创建用户表 (users)...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `users` (
            `id` VARCHAR(36) PRIMARY KEY,
            `username` VARCHAR(50) UNIQUE NOT NULL,
            `password_hash` VARCHAR(255) NOT NULL,
            `role` ENUM('ADMIN', 'USER') NOT NULL DEFAULT 'USER',
            `is_active` BOOLEAN DEFAULT TRUE,
            `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX `idx_username` (`username`),
            INDEX `idx_role` (`role`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # 2. 会话表
    print("创建会话表 (sessions)...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `sessions` (
            `id` VARCHAR(36) PRIMARY KEY,
            `user_id` VARCHAR(36) NOT NULL,
            `title` VARCHAR(255),
            `model` VARCHAR(100),
            `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
            INDEX `idx_user_sessions` (`user_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # 3. 消息表
    print("创建消息表 (messages)...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `messages` (
            `id` VARCHAR(36) PRIMARY KEY,
            `session_id` VARCHAR(36) NOT NULL,
            `role` ENUM('user', 'assistant', 'system') NOT NULL,
            `content` TEXT NOT NULL,
            `tokens_used` INT DEFAULT 0,
            `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (`session_id`) REFERENCES `sessions`(`id`) ON DELETE CASCADE,
            INDEX `idx_session_messages` (`session_id`),
            INDEX `idx_created_at` (`created_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # 4. 消息收藏表
    print("创建消息收藏表 (message_favorites)...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `message_favorites` (
            `id` VARCHAR(36) PRIMARY KEY,
            `user_id` VARCHAR(36) NOT NULL,
            `message_id` VARCHAR(36) NOT NULL,
            `session_id` VARCHAR(36) NOT NULL,
            `note` VARCHAR(500),
            `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
            FOREIGN KEY (`message_id`) REFERENCES `messages`(`id`) ON DELETE CASCADE,
            FOREIGN KEY (`session_id`) REFERENCES `sessions`(`id`) ON DELETE CASCADE,
            UNIQUE KEY `uq_user_message` (`user_id`, `message_id`),
            INDEX `idx_user_favorites` (`user_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # 5. LLM提供商表
    print("创建LLM提供商表 (llm_providers)...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `llm_providers` (
            `id` VARCHAR(36) PRIMARY KEY,
            `name` VARCHAR(100) UNIQUE NOT NULL,
            `display_name` VARCHAR(100) NOT NULL,
            `description` TEXT,
            `base_url` VARCHAR(500) NOT NULL,
            `api_format` ENUM('openai', 'ias') NOT NULL DEFAULT 'openai',
            `is_active` BOOLEAN DEFAULT TRUE,
            `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX `idx_provider_name` (`name`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # 6. LLM模型表
    print("创建LLM模型表 (llm_models)...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `llm_models` (
            `id` VARCHAR(36) PRIMARY KEY,
            `name` VARCHAR(100) UNIQUE NOT NULL,
            `display_name` VARCHAR(100) NOT NULL,
            `model_type` ENUM('openai', 'anthropic', 'custom', 'ias') NOT NULL DEFAULT 'custom',
            `api_format` ENUM('openai', 'ias') NOT NULL DEFAULT 'openai',
            `api_url` VARCHAR(500) NOT NULL,
            `api_key` TEXT NOT NULL,
            `api_version` VARCHAR(50),
            `description` TEXT,
            `is_active` BOOLEAN DEFAULT TRUE,
            `max_tokens` INT DEFAULT 4096,
            `temperature` INT DEFAULT 70,
            `stream_supported` BOOLEAN DEFAULT TRUE,
            `custom_headers` JSON,
            `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            `created_by` VARCHAR(36),
            FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
            INDEX `idx_model_name` (`name`),
            INDEX `idx_model_active` (`is_active`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # 7. 知识库分组表
    print("创建知识库分组表 (knowledge_groups)...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `knowledge_groups` (
            `id` VARCHAR(36) PRIMARY KEY,
            `name` VARCHAR(255) NOT NULL,
            `description` TEXT,
            `user_id` VARCHAR(36) NOT NULL,
            `color` VARCHAR(20) DEFAULT '#3B82F6',
            `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
            INDEX `idx_kg_user` (`user_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # 8. 知识库表
    print("创建知识库表 (knowledge_bases)...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `knowledge_bases` (
            `id` VARCHAR(36) PRIMARY KEY,
            `name` VARCHAR(255) NOT NULL,
            `description` TEXT,
            `user_id` VARCHAR(36) NOT NULL,
            `group_id` VARCHAR(36),
            `embedding_model` VARCHAR(100) DEFAULT 'bge-large-zh-v1.5',
            `chunk_size` INT DEFAULT 500,
            `chunk_overlap` INT DEFAULT 50,
            `is_active` BOOLEAN DEFAULT TRUE,
            `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
            FOREIGN KEY (`group_id`) REFERENCES `knowledge_groups`(`id`) ON DELETE SET NULL,
            INDEX `idx_kb_user` (`user_id`),
            INDEX `idx_kb_group` (`group_id`),
            INDEX `idx_kb_active` (`is_active`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # 9. 文档表
    print("创建文档表 (documents)...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `documents` (
            `id` VARCHAR(36) PRIMARY KEY,
            `knowledge_base_id` VARCHAR(36) NOT NULL,
            `filename` VARCHAR(255) NOT NULL,
            `file_type` VARCHAR(50),
            `file_size` INT,
            `chunk_count` INT DEFAULT 0,
            `upload_status` VARCHAR(50) DEFAULT 'processing',
            `error_message` TEXT,
            `uploaded_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            `processed_at` DATETIME,
            FOREIGN KEY (`knowledge_base_id`) REFERENCES `knowledge_bases`(`id`) ON DELETE CASCADE,
            INDEX `idx_doc_kb` (`knowledge_base_id`),
            INDEX `idx_doc_status` (`upload_status`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # 10. Agent配置表
    print("创建Agent配置表 (agents)...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `agents` (
            `id` VARCHAR(36) PRIMARY KEY,
            `name` VARCHAR(255) NOT NULL,
            `display_name` VARCHAR(255),
            `description` TEXT,
            `agent_type` VARCHAR(50) NOT NULL,
            `system_prompt` TEXT,
            `knowledge_base_ids` JSON,
            `tools` JSON,
            `config` JSON,
            `is_active` BOOLEAN DEFAULT TRUE,
            `created_by` VARCHAR(36),
            `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
            INDEX `idx_agent_type` (`agent_type`),
            INDEX `idx_agent_active` (`is_active`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # 11. Agent执行记录表
    print("创建Agent执行记录表 (agent_executions)...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `agent_executions` (
            `id` VARCHAR(36) PRIMARY KEY,
            `agent_id` VARCHAR(36) NOT NULL,
            `user_id` VARCHAR(36) NOT NULL,
            `session_id` VARCHAR(36),
            `input_prompt` TEXT NOT NULL,
            `status` VARCHAR(50) DEFAULT 'running',
            `steps` INT DEFAULT 0,
            `result` TEXT,
            `error_message` TEXT,
            `execution_log` JSON,
            `started_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            `completed_at` DATETIME,
            FOREIGN KEY (`agent_id`) REFERENCES `agents`(`id`) ON DELETE CASCADE,
            FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
            FOREIGN KEY (`session_id`) REFERENCES `sessions`(`id`) ON DELETE SET NULL,
            INDEX `idx_exec_agent` (`agent_id`),
            INDEX `idx_exec_user` (`user_id`),
            INDEX `idx_exec_status` (`status`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("\n✓ 所有表创建完成!")


def insert_default_users():
    """插入默认用户"""
    print("\n" + "=" * 80)
    print("步骤 2: 插入默认用户")
    print("Step 2: Inserting Default Users")
    print("=" * 80)

    conn = get_connection()
    cursor = conn.cursor()

    # 清空现有用户数据
    cursor.execute("DELETE FROM users")

    # 默认用户
    users = [
        {
            'id': str(uuid.uuid4()),
            'username': 'admin',
            'password': 'admin123',
            'role': 'ADMIN'
        },
        {
            'id': str(uuid.uuid4()),
            'username': 'sijia',
            'password': 'sijia',
            'role': 'USER'
        },
        {
            'id': str(uuid.uuid4()),
            'username': 'demo',
            'password': 'demo123',
            'role': 'USER'
        }
    ]

    for user_data in users:
        user_id = user_data['id']
        username = user_data['username']
        password_hash = hash_password(user_data['password'])
        role = user_data['role']

        cursor.execute("""
            INSERT INTO users (id, username, password_hash, role, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
        """, (user_id, username, password_hash, role))

        print(f"  ✓ 创建用户: {username} (密码: {user_data['password']})")

    conn.commit()
    cursor.close()
    conn.close()

    print("\n✓ 默认用户创建完成!")


def insert_default_llm_providers():
    """插入默认LLM提供商"""
    print("\n" + "=" * 80)
    print("步骤 3: 插入默认LLM提供商")
    print("Step 3: Inserting Default LLM Providers")
    print("=" * 80)

    conn = get_connection()
    cursor = conn.cursor()

    # 清空现有数据
    cursor.execute("DELETE FROM llm_providers")

    providers = [
        {
            'id': str(uuid.uuid4()),
            'name': 'openai',
            'display_name': 'OpenAI',
            'description': 'OpenAI官方API',
            'base_url': 'https://api.openai.com/v1',
            'api_format': 'openai',
            'is_active': True
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'custom',
            'display_name': '自定义API',
            'description': '自定义兼容OpenAI格式的API服务',
            'base_url': 'http://localhost:18063',
            'api_format': 'openai',
            'is_active': True
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'ias',
            'display_name': 'IAS MockServer',
            'description': 'IAS模拟服务API',
            'base_url': 'http://localhost:18063',
            'api_format': 'ias',
            'is_active': True
        }
    ]

    for provider in providers:
        cursor.execute("""
            INSERT INTO llm_providers (id, name, display_name, description, base_url, api_format, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            provider['id'], provider['name'], provider['display_name'],
            provider['description'], provider['base_url'],
            provider['api_format'], provider['is_active']
        ))
        print(f"  ✓ 创建提供商: {provider['display_name']} ({provider['name']})")

    conn.commit()
    cursor.close()
    conn.close()

    print("\n✓ 默认LLM提供商创建完成!")


def insert_default_llm_models():
    """插入默认LLM模型"""
    print("\n" + "=" * 80)
    print("步骤 4: 插入默认LLM模型")
    print("Step 4: Inserting Default LLM Models")
    print("=" * 80)

    conn = get_connection()
    cursor = conn.cursor()

    # 清空现有数据
    cursor.execute("DELETE FROM llm_models")

    # 获取admin用户ID作为创建者
    cursor.execute("SELECT id FROM users WHERE username='admin' LIMIT 1")
    admin_id = cursor.fetchone()[0] if cursor.rowcount > 0 else None

    models = [
        {
            'id': str(uuid.uuid4()),
            'name': 'gpt-3.5-turbo',
            'display_name': 'GPT-3.5 Turbo',
            'model_type': 'openai',
            'api_format': 'openai',
            'api_url': 'https://api.openai.com/v1/chat/completions',
            'api_key': 'sk-your-openai-api-key-here',
            'description': 'OpenAI GPT-3.5 Turbo 模型',
            'is_active': True,
            'max_tokens': 4096,
            'temperature': 70,
            'stream_supported': True,
            'created_by': admin_id
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'gpt-4',
            'display_name': 'GPT-4',
            'model_type': 'openai',
            'api_format': 'openai',
            'api_url': 'https://api.openai.com/v1/chat/completions',
            'api_key': 'sk-your-openai-api-key-here',
            'description': 'OpenAI GPT-4 模型',
            'is_active': True,
            'max_tokens': 8192,
            'temperature': 70,
            'stream_supported': True,
            'created_by': admin_id
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'glm-4',
            'display_name': '智谱 GLM-4',
            'model_type': 'custom',
            'api_format': 'openai',
            'api_url': 'http://localhost:18063/lmp-cloud-ias-server/api/llm/chat/completions/V2',
            'api_key': 'your-api-key',
            'description': '智谱AI GLM-4 模型',
            'is_active': True,
            'max_tokens': 4096,
            'temperature': 70,
            'stream_supported': True,
            'created_by': admin_id
        }
    ]

    for model in models:
        cursor.execute("""
            INSERT INTO llm_models
            (id, name, display_name, model_type, api_format, api_url, api_key,
             description, is_active, max_tokens, temperature, stream_supported, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            model['id'], model['name'], model['display_name'], model['model_type'],
            model['api_format'], model['api_url'], model['api_key'],
            model['description'], model['is_active'], model['max_tokens'],
            model['temperature'], model['stream_supported'], model['created_by']
        ))
        print(f"  ✓ 创建模型: {model['display_name']} ({model['name']})")

    conn.commit()
    cursor.close()
    conn.close()

    print("\n✓ 默认LLM模型创建完成!")


def insert_sample_agents():
    """插入示例Agent"""
    print("\n" + "=" * 80)
    print("步骤 5: 插入示例Agent")
    print("Step 5: Inserting Sample Agents")
    print("=" * 80)

    conn = get_connection()
    cursor = conn.cursor()

    # 获取admin用户ID
    cursor.execute("SELECT id FROM users WHERE username='admin' LIMIT 1")
    result = cursor.fetchone()
    if not result:
        print("  ⚠ 未找到admin用户，跳过Agent创建")
        conn.close()
        return

    admin_id = result[0]

    # 清空现有Agent
    cursor.execute("DELETE FROM agents")

    agents = [
        {
            'id': str(uuid.uuid4()),
            'name': 'general_assistant',
            'display_name': '通用助手',
            'description': '能够回答各种问题、执行计算、搜索信息的通用AI助手',
            'agent_type': 'tool',
            'system_prompt': '你是一个有用的AI助手。你可以使用各种工具来帮助用户解决问题。在回答问题时，要简洁、准确、友好。',
            'tools': '["calculator", "datetime", "knowledge_search"]',
            'config': '{"temperature": 0.7, "max_steps": 10}',
            'is_active': True,
            'created_by': admin_id
        }
    ]

    for agent in agents:
        cursor.execute("""
            INSERT INTO agents
            (id, name, display_name, description, agent_type, system_prompt, tools, config, is_active, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            agent['id'], agent['name'], agent['display_name'],
            agent['description'], agent['agent_type'], agent['system_prompt'],
            agent['tools'], agent['config'], agent['is_active'], agent['created_by']
        ))
        print(f"  ✓ 创建Agent: {agent['display_name']}")

    conn.commit()
    cursor.close()
    conn.close()

    print("\n✓ 示例Agent创建完成!")


def verify_data():
    """验证数据"""
    print("\n" + "=" * 80)
    print("步骤 6: 验证数据")
    print("Step 6: Verifying Data")
    print("=" * 80)

    conn = get_connection()
    cursor = conn.cursor()

    # 检查所有表的记录数
    tables = [
        'users', 'sessions', 'messages', 'message_favorites',
        'llm_providers', 'llm_models',
        'knowledge_groups', 'knowledge_bases', 'documents',
        'agents', 'agent_executions'
    ]

    print("\n表数据统计:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table:25s}: {count:5d} 条记录")

    # 显示用户列表
    print("\n用户列表:")
    cursor.execute("SELECT username, role FROM users")
    for username, role in cursor.fetchall():
        print(f"  - {username:15s} ({role})")

    cursor.close()
    conn.close()

    print("\n✓ 数据验证完成!")


def print_summary():
    """打印初始化摘要"""
    print("\n" + "=" * 80)
    print("数据库初始化完成!")
    print("Database Initialization Completed!")
    print("=" * 80)

    print("\n默认登录凭证:")
    print("Default Login Credentials:")
    print("-" * 80)
    print("  管理员账户:")
    print("    用户名: admin")
    print("    密码:   admin123")
    print("")
    print("  测试用户:")
    print("    用户名: sijia")
    print("    密码:   sijia")
    print("")
    print("    用户名: demo")
    print("    密码:   demo123")

    print("\n注意事项:")
    print("Important Notes:")
    print("-" * 80)
    print("  1. 生产环境请立即修改默认密码!")
    print("  2. LLM模型的API Key需要配置真实密钥才能使用")
    print("  3. 建议定期备份数据库")

    print("\n下一步:")
    print("Next Steps:")
    print("-" * 80)
    print("  1. 重启后端服务: docker restart AIWorkbench-backend")
    print("  2. 访问API文档: http://localhost:18080/docs")
    print("  3. 测试登录功能")
    print("  4. 配置LLM模型的API密钥")

    print("\n" + "=" * 80)


def main(reset=False):
    """主函数"""
    try:
        # 1. 创建表
        create_tables()

        # 2. 插入默认数据
        insert_default_users()
        insert_default_llm_providers()
        insert_default_llm_models()
        insert_sample_agents()

        # 3. 验证数据
        verify_data()

        # 4. 打印摘要
        print_summary()

        return 0

    except Exception as e:
        print(f"\n✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Bright-Chat 数据库初始化脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python init_database.py           # 初始化数据库
  python init_database.py --reset   # 重置数据库（删除所有数据）
        """
    )

    parser.add_argument(
        '--reset',
        action='store_true',
        help='重置数据库（删除所有现有数据）'
    )

    args = parser.parse_args()

    sys.exit(main(reset=args.reset))
