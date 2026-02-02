#!/usr/bin/env python3
"""
从 ModelScope 下载 BGE embedding 模型
Download BGE embedding model from ModelScope
"""
import os
import sys

def main():
    print("=" * 60)
    print("开始从 ModelScope 下载 BGE-Large-ZH-v1.5 模型")
    print("=" * 60)

    # 添加 modelscope 到路径
    try:
        from modelscope import snapshot_download
    except ImportError:
        print("错误: ModelScope 未安装")
        print("请运行: pip install modelscope")
        sys.exit(1)

    # 模型配置
    MODEL_ID = "Xorbits/bge-large-zh-v1.5"
    CACHE_DIR = "/data1/allresearchProject/Bright-Chat/models"

    print(f"模型ID: {MODEL_ID}")
    print(f"缓存目录: {CACHE_DIR}")
    print()

    # 创建目录
    os.makedirs(CACHE_DIR, exist_ok=True)

    try:
        print("正在下载模型...")
        print("提示：模型文件较大（约1.3GB），请耐心等待...")
        print()

        model_dir = snapshot_download(
            MODEL_ID,
            cache_dir=CACHE_DIR,
            revision='master'
        )

        print()
        print("=" * 60)
        print("✅ 模型下载成功！")
        print("=" * 60)
        print(f"模型路径: {model_dir}")
        print()

        # 检查模型文件
        print("模型文件列表:")
        for file in os.listdir(model_dir):
            file_path = os.path.join(model_dir, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                print(f"  - {file} ({size:.1f} MB)")

        print()
        print("下一步：")
        print("1. 模型已配置到: /data1/allresearchProject/Bright-Chat/backend-python/.env")
        print("2. RAG_USE_MOCK 已设置为 false")
        print("3. 重启服务或运行: python3 -c 'from rag.config import get_rag_config; c=get_rag_config(); print(c.health_check())'")

        return 0

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 模型下载失败")
        print("=" * 60)
        print(f"错误信息: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
