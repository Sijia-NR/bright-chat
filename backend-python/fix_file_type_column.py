#!/usr/bin/env python3
"""
修复 file_type 列长度

问题: MIME 类型如 application/vnd.openxmlformats-officedocument.wordprocessingml.document
     超过了原有列的长度限制

解决方案: 将 file_type 列修改为 VARCHAR(255)
"""

import pymysql
from sqlalchemy import create_engine, text

# 数据库配置
DB_HOST = "47.116.218.206"
DB_PORT = 13306
DB_USER = "root"
DB_PASSWORD = "123456"
DB_DATABASE = "bright_chat"

def fix_file_type_column():
    """修复 file_type 列长度"""

    try:
        # 创建连接
        engine = create_engine(
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}",
            echo=False
        )

        with engine.connect() as conn:
            # 执行 ALTER TABLE
            print("正在修改 file_type 列...")
            conn.execute(text("ALTER TABLE documents MODIFY COLUMN file_type VARCHAR(255) NOT NULL"))
            conn.commit()

            # 验证修改
            result = conn.execute(text("DESCRIBE documents"))
            columns = result.fetchall()

            print("\n✅ 成功！file_type 列已修改为 VARCHAR(255)")
            print("\ndocuments 表结构:")
            for column in columns:
                print(f"  {column[0]:20} {column[1]:20} {column[2]:10} {column[3]:10} {column[4] or ''}")

            return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    print("开始修复 file_type 列长度...\n")
    success = fix_file_type_column()

    if success:
        print("\n✅ 迁移完成！")
        print("现在可以重新上传文件了。")
    else:
        print("\n❌ 迁移失败！")
        exit(1)
