#!/usr/bin/env python3
"""
强制创建数据库表
解决表已存在但服务器无法识别的问题
"""

import os
import sys
from urllib.parse import quote_plus
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# 添加当前目录到路径
sys.path.insert(0, '/data1/allresearchProject/Bright-Chat/backend-python')

# 导入模型（minimal_api.py 中已定义）
from minimal_api import (
    Base, User, Session, Message, MessageFavorite,
    LLMModel, LLMModelType, LLMProvider,
    KnowledgeGroup, KnowledgeBase, Document,
    Agent, AgentExecution
)

# 数据库配置
DB_HOST = os.getenv("DB_HOST", "47.116.218.206")
DB_PORT = os.getenv("DB_PORT", "13306")
DB_USERNAME = os.getenv("DB_USERNAME", os.getenv("MYSQL_USER", "root"))
DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("MYSQL_PASSWORD") or "123456"
DB_DATABASE = os.getenv("DB_DATABASE", os.getenv("MYSQL_DATABASE", "bright_chat"))

if os.getenv("DB_HOST") == "mysql":
    DB_PORT = "3306"
    DB_USERNAME = "bright_chat"
    DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "BrightChat2024!@#")

DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD)
DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"

print("="*80)
print("强制创建数据库表")
print("="*80)
print(f"数据库: {DB_USERNAME}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}")
print()

# 创建引擎
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 检查现有表
inspector = inspect(engine)
existing_tables = inspector.get_table_names()

print(f"当前数据库中的表 ({len(existing_tables)}):")
for table in sorted(existing_tables):
    print(f"  - {table}")
print()

# 定义所有需要的表
all_tables = [
    'users', 'sessions', 'messages', 'message_favorites',
    'llm_models', 'llm_providers',
    'knowledge_groups', 'knowledge_bases', 'documents',
    'agents', 'agent_executions'
]

# 检查缺失的表
missing_tables = [t for t in all_tables if t not in existing_tables]

if missing_tables:
    print(f"缺失的表 ({len(missing_tables)}):")
    for table in missing_tables:
        print(f"  - {table}")
    print()
    print("创建缺失的表...")
    Base.metadata.create_all(bind=engine)
    print("✓ 表创建完成")
else:
    print("✓ 所有表都已存在")

print()
print("="*80)
print("验证表结构")
print("="*80)

# 重新检查
inspector = inspect(engine)
final_tables = inspector.get_table_names()

print(f"\n最终表数量: {len(final_tables)}")
for table in all_tables:
    if table in final_tables:
        print(f"  ✓ {table}")
    else:
        print(f"  ✗ {table} (缺失)")

print()
print("="*80)
print("完成！请重启服务器")
print("="*80)
print("\n执行以下命令重启服务器:")
print("  cd /data1/allresearchProject/Bright-Chat/backend-python")
print("  ./restart_server.sh")
