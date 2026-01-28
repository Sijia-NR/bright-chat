# ChromaDB 优化方案

## 问题诊断

### 当前问题

1. **Collection元数据损坏**
   - 错误：`KeyError: '_type'`
   - 原因：ChromaDB版本不兼容或异常关闭
   - 影响：无法获取、创建或删除collection

2. **知识检索失败**
   - API返回500错误
   - 无法进行向量检索

3. **文档处理超时**
   - 后台任务执行不稳定
   - 向量化失败

### 根本原因

**ChromaDB版本兼容性问题**

当前环境：
- Python 3.12
- ChromaDB版本可能存在破坏性更新
- 元数据格式变化导致旧collection无法读取

---

## 立即修复方案

### 方案1：完全重置ChromaDB（推荐）

```bash
# 1. 停止ChromaDB容器
docker stop bright-chat-chromadb 2>/dev/null || true

# 2. 删除ChromaDB数据卷
docker volume rm bright-chat_chromadb_data 2>/dev/null || true

# 3. 重新启动ChromaDB
docker run -d \
  --name bright-chat-chromadb \
  -p 8002:8000 \
  -v chromadb_data:/chroma/chroma \
  chromadb/chroma:latest

# 4. 验证连接
curl http://localhost:8002/api/v1/heartbeat

# 5. 重启后端（会自动创建新collection）
cd /data1/allresearchProject/Bright-Chat/backend-python
export CHROMADB_HOST=localhost
export CHROMADB_PORT=8002
python3 minimal_api.py
```

### 方案2：使用ChromaDB持久化替代方案

如果Docker方式持续出现问题，可以改用文件持久化：

```python
# 修改 app/rag/config.py
import chromadb

# 使用文件持久化而不是HTTP客户端
self.chroma_client = chromadb.PersistentClient(
    path="/data1/allresearchProject/Bright-Chat/chromadb_data"
)
```

**优点：**
- 更稳定，避免网络问题
- 数据持久化在本地磁盘
- 版本兼容性更好

**缺点：**
- 性能略低于Docker方式
- 无法跨服务共享

---

## 长期优化方案

### 1. 升级ChromaDB版本

```bash
# 卸载旧版本
pip uninstall chromadb -y

# 安装特定稳定版本
pip install chromadb==0.4.22  # 稳定版本

# 或者安装最新版本
pip install chromadb --upgrade
```

### 2. 添加Collection健康检查

在`app/rag/config.py`中添加：

```python
def check_collection_health(self, collection_name: str) -> bool:
    """检查collection是否健康"""
    try:
        collection = self.chroma_client.get_collection(collection_name)
        # 尝试执行查询
        collection.peek(limit=1)
        return True
    except Exception as e:
        logger.warning(f"Collection {collection_name} 不健康: {e}")
        return False

def recreate_collection_if_broken(self, collection_name: str):
    """如果collection损坏则重建"""
    if not self.check_collection_health(collection_name):
        logger.warning(f"Collection {collection_name} 损坏，尝试重建...")

        try:
            # 备份数量信息
            old_count = 0
            try:
                old_collection = self.chroma_client.get_collection(collection_name)
                old_count = old_collection.count()
            except:
                pass

            # 删除旧collection
            self.chroma_client.delete_collection(collection_name)

            # 创建新collection
            new_collection = self.chroma_client.create_collection(collection_name)

            logger.info(f"✅ Collection {collection_name} 已重建")
            logger.info(f"   原有数据: {old_count} 条 -> 新数据: 0 条")
            logger.info(f"   ⚠️  需要重新上传文档")

            return new_collection
        except Exception as e:
            logger.error(f"重建失败: {e}")
            raise
```

### 3. 实现自动恢复机制

在`minimal_api.py`的启动代码中添加：

```python
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("正在初始化RAG系统...")

    try:
        rag_config = get_rag_config()

        # 检查并修复knowledge_chunks collection
        if not rag_config.health_check():
            logger.error("ChromaDB连接失败，请检查ChromaDB服务")
            return

        # 检查collection健康状态
        collection_name = "knowledge_chunks"
        if not rag_config.check_collection_health(collection_name):
            logger.warning(f"Collection {collection_name} 不健康，尝试自动修复...")
            rag_config.recreate_collection_if_broken(collection_name)

        logger.info("✅ RAG系统初始化完成")
    except Exception as e:
        logger.error(f"RAG系统初始化失败: {e}")
        # 不阻塞应用启动，RAG功能可后续手动启用
```

### 4. 添加向量数据备份

```python
def backup_collection_data(collection_name: str, backup_path: str):
    """备份collection数据"""
    try:
        client = get_rag_config().chroma_client
        collection = client.get_collection(collection_name)

        # 获取所有数据
        data = collection.get(include=["embeddings", "documents", "metadatas"])

        # 保存到文件
        import json
        with open(backup_path, 'w') as f:
            json.dump(data, f)

        logger.info(f"✅ Collection {collection_name} 已备份到 {backup_path}")
    except Exception as e:
        logger.error(f"备份失败: {e}")

def restore_collection_data(collection_name: str, backup_path: str):
    """从备份恢复collection数据"""
    try:
        import json
        with open(backup_path, 'r') as f:
            data = json.load(f)

        client = get_rag_config().chroma_client
        collection = client.get_or_create_collection(collection_name)

        # 恢复数据
        if data["embeddings"]:
            collection.add(
                embeddings=data["embeddings"],
                documents=data["documents"],
                metadatas=data["metadatas"],
                ids=[f"doc_{i}" for i in range(len(data["documents"]))]
            )

        logger.info(f"✅ Collection {collection_name} 已从备份恢复")
    except Exception as e:
        logger.error(f"恢复失败: {e}")
```

### 5. 使用向量数据库替代方案

如果ChromaDB问题持续存在，可以考虑替代方案：

#### 选项A：Qdrant

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# 安装：pip install qdrant-client
client = QdrantClient(host="localhost", port=6333)

# 创建collection
client.create_collection(
    collection_name="knowledge_chunks",
    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
)
```

**优点：**
- 性能更好
- 更稳定
- 支持过滤和混合搜索

**缺点：**
- 需要额外的服务
- API稍有不同

#### 选项B：FAISS（本地）

```python
import faiss
import numpy as np

# 创建索引
dimension = 1024
index = faiss.IndexFlatL2(dimension)

# 添加向量
vectors = np.array([...]).astype('float32')
index.add(vectors)

# 搜索
D, I = index.search(query_vector, k=5)
```

**优点：**
- 无需额外服务
- 极快速度
- 完全本地化

**缺点：**
- 不支持持久化（需要手动保存）
- 不支持元数据过滤

---

## 推荐执行步骤

### 立即执行（5分钟）

```bash
# 1. 完全重置ChromaDB
docker stop bright-chat-chromadb 2>/dev/null || true
docker rm bright-chat-chromadb 2>/dev/null || true

# 2. 启动新的ChromaDB
docker run -d \
  --name bright-chat-chromadb \
  -p 8002:8000 \
  -v chromadb_data:/chroma/chroma \
  chromadb/chroma:0.4.22

# 3. 验证
curl http://localhost:8002/api/v1/heartbeat

# 4. 测试知识检索
python3 tests/test_knowledge_integration.py
```

### 短期优化（1小时）

1. 在`app/rag/config.py`添加健康检查
2. 在`minimal_api.py`添加启动时自动修复
3. 实现数据备份脚本

### 长期优化（1天）

1. 评估Qdrant作为替代方案
2. 实现自动备份和恢复
3. 添加监控告警

---

## 监控和诊断

### 诊断脚本

```bash
#!/bin/bash
# check_chromadb.sh

echo "ChromaDB 健康检查"
echo "=================="

# 1. 检查容器状态
echo -n "1. 容器状态: "
docker ps | grep chromadb && echo "✅ 运行中" || echo "❌ 未运行"

# 2. 检查端口监听
echo -n "2. 端口监听: "
nc -z localhost 8002 && echo "✅ 8002端口正常" || echo "❌ 8002端口不可达"

# 3. 检查API响应
echo -n "3. API健康: "
curl -s http://localhost:8002/api/v1/heartbeat > /dev/null && echo "✅ API正常" || echo "❌ API异常"

# 4. 检查collections
echo "4. Collections状态:"
python3 -c "
import chromadb
client = chromadb.HttpClient(host='localhost', port=8002)
try:
    cols = client.list_collections()
    print(f'   ✅ 共有 {len(cols)} 个collections')
    for col in cols:
        print(f'   - {col.name}')
except Exception as e:
    print(f'   ❌ 错误: {e}')
"

echo "=================="
echo "检查完成"
```

### 监控指标

- Collection数量
- 向量总数
- 查询延迟
- 错误率

---

## 总结

### 最佳实践

1. **定期备份向量数据**
2. **监控ChromaDB健康状态**
3. **实施自动恢复机制**
4. **准备替代方案**

### 紧急修复命令

```bash
# 一键重置
docker stop bright-chat-chromadb && \
docker rm bright-chat-chromadb && \
docker run -d --name bright-chat-chromadb -p 8002:8000 chromadb/chroma:0.4.22
```

### 联系支持

如果问题持续：
- 检查ChromaDB日志：`docker logs bright-chat-chromadb`
- 查看后端日志：`tail -f /tmp/backend.log`
- 考虑切换到Qdrant或FAISS
