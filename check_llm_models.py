#!/usr/bin/env python3
"""检查数据库中的 LLM 模型配置"""

from sqlalchemy import create_engine, text

# 直接使用数据库连接信息
engine = create_engine(
    "mysql+pymysql://root:123456@47.116.218.206:13306/bright_chat"
)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT id, name, display_name, model_type, api_url,
               SUBSTRING(api_key, 1, 30) as api_key_preview,
               is_active
        FROM llm_models
        WHERE is_active = 1
        ORDER BY created_at DESC
        LIMIT 10
    """))

    print("\n活跃的 LLM 模型配置:")
    print("-" * 150)
    print(f"{'ID':<38} {'名称':<20} {'显示名':<20} {'类型':<12} {'API URL':<40} {'API Key 预览':<30}")
    print("-" * 150)

    for row in result:
        print(f"{row.id:<38} {row.name:<20} {row.display_name:<20} {row.model_type:<12} {row.api_url:<40} {row.api_key_preview:<30}")

    print("-" * 150)
