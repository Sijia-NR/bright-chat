#!/usr/bin/env python3
"""
验证本地 BGE 模型加载和文档处理
Verify local BGE model loading and document processing
"""
import os
import sys
import asyncio

# 添加当前目录到路径
sys.path.insert(0, '.')

def check_model_files():
    """检查模型文件是否存在"""
    model_path = "/data1/allresearchProject/Bright-Chat/models/Xorbits/bge-large-zh-v1.5"

    print("=" * 60)
    print("检查模型文件")
    print("=" * 60)

    if not os.path.exists(model_path):
        print(f"❌ 模型目录不存在: {model_path}")
        return False

    print(f"✅ 模型目录存在: {model_path}")
    print("\n模型文件:")
    total_size = 0
    for file in sorted(os.listdir(model_path)):
        file_path = os.path.join(model_path, file)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            total_size += size
            print(f"  ✓ {file:40} {size:8.1f} MB")

    print(f"\n总大小: {total_size:.1f} MB")
    print()

    # 检查关键文件
    required_files = [
        "model.safetensors",
        "config.json",
        "tokenizer_config.json",
        "vocab.txt"
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(os.path.join(model_path, file)):
            missing_files.append(file)

    if missing_files:
        print(f"❌ 缺少关键文件: {', '.join(missing_files)}")
        return False

    print("✅ 所有关键文件都存在")
    return True

async def test_model_loading():
    """测试模型加载"""
    print("\n" + "=" * 60)
    print("测试模型加载")
    print("=" * 60)

    try:
        from rag.config import get_rag_config, reset_rag_config

        # 重置配置以确保使用新的环境变量
        reset_rag_config()

        # 设置环境变量
        os.environ['BGE_MODEL_PATH'] = "/data1/allresearchProject/Bright-Chat/models/Xorbits/bge-large-zh-v1.5"
        os.environ['RAG_USE_MOCK'] = 'false'
        os.environ['CHROMADB_PERSIST_DIRECTORY'] = "/data1/allresearchProject/Bright-Chat/data/chroma"

        # 获取配置
        config = get_rag_config()

        # 加载模型
        print("正在加载模型...")
        model = config.embedding_model

        print(f"✅ 模型加载成功")
        print(f"   模型维度: {model.get_sentence_embedding_dimension()}")
        print()

        return True

    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_document_processing():
    """测试文档处理"""
    print("\n" + "=" * 60)
    print("测试文档处理")
    print("=" * 60)

    try:
        from rag.document_processor import DocumentProcessor

        processor = DocumentProcessor()

        # 创建测试文件
        test_file = '/tmp/test_local_model.txt'
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('这是一个测试文档。\n用于验证本地 BGE 模型是否正常工作。\n包含多个句子以测试分块功能。')

        print(f"创建测试文件: {test_file}")
        print("正在处理文档...")

        # 处理文档
        result = await processor.process_document(
            file_path=test_file,
            knowledge_base_id='test_kb_local',
            user_id='test_user',
            filename='test_local_model.txt',
            chunk_size=500,
            chunk_overlap=50
        )

        print(f"\n处理结果:")
        print(f"  状态: {result.get('status')}")
        print(f"  分块数: {result.get('chunk_count')}")
        print(f"  消息: {result.get('message')}")

        if result.get('status') == 'completed' and result.get('chunk_count', 0) > 0:
            print("\n✅ 文档处理成功！")
            return True
        else:
            print(f"\n❌ 文档处理失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ 文档处理出错: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("\n" + "=" * 60)
    print("本地 BGE 模型验证工具")
    print("=" * 60)
    print()

    # 检查模型文件
    if not check_model_files():
        print("\n❌ 模型文件检查失败")
        print("请先运行: python3 download_bgemodel.py")
        return 1

    # 测试模型加载
    if not await test_model_loading():
        print("\n❌ 模型加载失败")
        return 1

    # 测试文档处理
    if not await test_document_processing():
        print("\n❌ 文档处理失败")
        return 1

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
    print("\n本地 BGE 模型已成功部署并对接到知识库系统。")
    print("\n下一步:")
    print("  1. 重启 API 服务")
    print("  2. 通过 API 上传文档进行测试")
    print()

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
