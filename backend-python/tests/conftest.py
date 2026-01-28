"""
测试配置和共享 fixtures
Test configuration and shared fixtures
"""
import os
import sys
import pytest
import tempfile
from typing import AsyncGenerator, Generator
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置测试环境变量
os.environ['APP_DEBUG'] = 'true'
os.environ['DB_DRIVER'] = 'mysql'
os.environ['CHROMADB_PERSIST_DIRECTORY'] = tempfile.mkdtemp(prefix='chroma_test_')
os.environ['RAG_USE_MOCK'] = 'true'  # 使用Mock模型避免网络问题

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

# 导入应用模块
try:
    from rag.config import RAGConfig, get_rag_config, reset_rag_config
    from agents.agent_service import AgentService, get_agent_service
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database_url():
    """测试数据库URL"""
    return "mysql+pymysql://root:123456@47.116.218.206:13306/bright_chat"


@pytest.fixture(scope="session")
def db_engine(test_database_url):
    """创建数据库引擎"""
    engine = create_engine(
        test_database_url,
        pool_pre_ping=True,
        echo=False
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """创建数据库会话"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()

    yield session

    session.rollback()
    session.close()


@pytest.fixture(scope="session")
def rag_config():
    """创建RAG配置（使用Mock模型和临时目录）"""
    if not RAG_AVAILABLE:
        pytest.skip("RAG模块未安装")

    # 使用Mock模式避免网络问题
    config = RAGConfig(use_mock=True)
    yield config

    # 清理
    reset_rag_config()

    # 清理临时目录
    import shutil
    try:
        if 'CHROMADB_PERSIST_DIRECTORY' in os.environ:
            shutil.rmtree(os.environ['CHROMADB_PERSIST_DIRECTORY'])
    except:
        pass


@pytest.fixture(scope="session")
def agent_service():
    """创建Agent服务"""
    if not RAG_AVAILABLE:
        pytest.skip("Agent模块未安装")

    service = AgentService()
    yield service


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator:
    """创建异步HTTP客户端"""
    # 这里可以创建实际的FastAPI测试客户端
    # 暂时返回一个模拟客户端
    async with AsyncClient(app=None, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
def test_user_data():
    """测试用户数据"""
    return {
        "id": "test-user-001",
        "username": "test_user",
        "role": "user"
    }


@pytest.fixture(scope="function")
def test_knowledge_base_data(test_user_data):
    """测试知识库数据"""
    return {
        "id": "test-kb-001",
        "name": "测试知识库",
        "description": "用于测试的知识库",
        "user_id": test_user_data["id"],
        "embedding_model": "bge-large-zh-v1.5",
        "chunk_size": 500,
        "chunk_overlap": 50
    }


@pytest.fixture(scope="function")
def test_document_data(test_knowledge_base_data):
    """测试文档数据"""
    return {
        "id": "test-doc-001",
        "knowledge_base_id": test_knowledge_base_data["id"],
        "filename": "test_document.txt",
        "file_type": "text",
        "file_size": 1024
    }


@pytest.fixture(scope="function")
def test_agent_data(test_user_data):
    """测试Agent数据"""
    return {
        "id": "test-agent-001",
        "name": "test_assistant",
        "display_name": "测试助手",
        "description": "用于测试的AI助手",
        "agent_type": "tool",
        "system_prompt": "你是一个测试助手",
        "tools": ["calculator", "datetime"],
        "config": {
            "temperature": 0.7,
            "max_steps": 10
        },
        "created_by": test_user_data["id"]
    }


# 测试辅助函数
def create_test_document(content: str, filename: str = "test.txt") -> str:
    """创建测试文档"""
    temp_dir = tempfile.mkdtemp(prefix='test_doc_')
    file_path = os.path.join(temp_dir, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path


def assert_valid_uuid(id_str: str):
    """验证UUID格式"""
    import uuid
    try:
        uuid.UUID(id_str)
        return True
    except ValueError:
        return False


def cleanup_test_chroma(collection_name: str = "test_collection"):
    """清理测试ChromaDB数据"""
    if not RAG_AVAILABLE:
        return

    try:
        config = get_rag_config()
        try:
            config.chroma_client.delete_collection(collection_name)
        except:
            pass
    except:
        pass
