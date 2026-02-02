#!/usr/bin/env python3
"""
修复 admin 用户密码为正确的 bcrypt 格式
"""
import pymysql
import bcrypt

# 数据库配置
DB_CONFIG = {
    'host': '47.116.218.206',
    'port': 13306,
    'user': 'root',
    'password': '123456',
    'database': 'bright_chat',
    'charset': 'utf8mb4'
}

def fix_admin_password():
    """修复 admin 用户密码"""
    print("=" * 60)
    print("修复 admin 用户密码")
    print("=" * 60)

    try:
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 生成新的 bcrypt 密码哈希
        new_password = "admin123"
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        print(f"\n新的密码哈希 (bcrypt):")
        print(f"{password_hash}")

        # 更新 admin 用户密码
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE username = 'admin'",
            (password_hash,)
        )

        connection.commit()

        # 验证更新
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()

        print("\n" + "=" * 60)
        print("✅ admin 用户密码已更新！")
        print(f"  用户名: {admin_user['username']}")
        print(f"  新密码哈希: {admin_user['password_hash'][:60]}...")
        print(f"\n现在可以使用以下凭证登录:")
        print(f"  用户名: admin")
        print(f"  密码: {new_password}")
        print("=" * 60)

        cursor.close()
        connection.close()

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_admin_password()
