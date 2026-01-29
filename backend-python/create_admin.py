#!/usr/bin/env python3
"""创建 admin 用户的简单脚本"""
import pymysql
import uuid
from datetime import datetime

# 使用一个已知的 bcrypt 哈希值（admin123）
# 这是通过 bcrypt.hash("admin123") 生成的
password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEmc0i"

conn = pymysql.connect(
    host='localhost',
    port=13306,
    user='root',
    password='root_password_change_me',
    database='bright_chat'
)

cursor = conn.cursor()

user_id = str(uuid.uuid4())
created_at = datetime.utcnow()

sql = """
INSERT INTO users (id, username, password_hash, role, created_at, updated_at)
VALUES (%s, %s, %s, %s, %s, %s)
"""

try:
    cursor.execute(sql, (user_id, "admin", password_hash, "ADMIN", created_at, created_at))
    conn.commit()
    print(f"✓ Admin 用户创建成功")
    print(f"  用户名: admin")
    print(f"  密码: admin123")
    print(f"  ID: {user_id}")
except Exception as e:
    print(f"✗ 创建用户失败: {e}")

cursor.close()
conn.close()
