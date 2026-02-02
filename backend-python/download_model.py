#!/usr/bin/env python3
"""
从 ModelScope 下载 BGE embedding 模型
Download BGE embedding model from ModelScope
"""
import os
from modelscope import snapshot_download

# 模型配置
MODEL_ID = "Xorbits/bge-large-zh-v1.5"
CACHE_DIR = "/data1/allresearchProject/Bright-Chat/models"

def main():
    print("=" * 60)
    print("开始从 ModelScope 下载 BGE-Large-ZH-v1.5 模型")
    print("=" * 60)
    print(f"模型ID: {MODEL_ID}")
    print(f"缓存目录: {CACHE_DIR}")
    print()

    # 创建目录
    os.makedirs(CACHE_DIR, exist_ok=True)

    try:
        print("正在下载模型...")
        print("提示：模型文件较大（约1.3GB），请耐心等待...")

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
        print("请更新 .env 文件中的配置：")
        print(f"BGE_MODEL_PATH={model_dir}")
        print()

        return model_dir

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 模型下载失败")
        print("=" * 60)
        print(f"错误信息: {e}")
        return None

if __name__ == "__main__":
    model_path = main()
    if model_path:
        print("\n下一步：")
        print("1. 更新 .env 文件设置 BGE_MODEL_PATH")
        print("2. 设置 RAG_USE_MOCK=false")
        print("3. 重启服务")
    else:
        print("\n请检查网络连接和 ModelScope 访问权限")
        exit(1)
