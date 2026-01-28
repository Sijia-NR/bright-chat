# ChromaDB 优化关键点总结

## 问题诊断

### 发现的核心问题

1. **Collection元数据损坏** ✅ 已修复
   - 原因：ChromaDB版本不兼容
   - 解决：重置ChromaDB容器
   - 状态：已恢复正常

2. **文档处理失败** ⚠️ 仍存在
   - 原因：后台任务执行不稳定
   - 表现：文档状态始终为 `error`
   - 影响：无法向量化文档，无法进行知识检索

3. **缺少健康检查** ❌ 未实现
   - 无法自动检测collection损坏
   - 需要手动修复

---

## 需要优化的关键点

### 1. 文档处理流程（高优先级）

**当前问题：**
```
文档上传成功 → 状态: pending → 处理超时 → 状态: error
```

**根本原因：**
- 后台任务队列不稳定
- BGE模型加载失败
- ChromaDB写入失败

**优化方案：**

#### A. 添加同步处理选项

```python
# minimal_api.py 修改文档上传端点

@app.post(f"{API_PREFIX}/knowledge/bases/{kb_id}/upload")
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    background_tasks: BackgroundTasks = None,
    sync: bool = False,  # 新增：是否同步处理
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传并处理文档"""

    # ... 创建文档记录 ...

    if sync:
        # 同步处理（立即完成）
        try:
            from app.rag.document_processor import DocumentProcessor
            processor = DocumentProcessor()

            # 保存文件
            file_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"
            with open(file_path, 'wb') as f:
                f.write(await file.read())

            # 处理文档
            chunks = await processor.process_document(
                file_path=str(file_path),
                knowledge_base_id=kb_id,
                user_id=current_user.id,
                filename=file.filename,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )

            doc.status = "completed"
            doc.chunk_count = len(chunks)
            db.commit()

            logger.info(f"✅ 文档同步处理成功: {len(chunks)} 个chunks")
        except Exception as e:
            doc.status = "error"
            doc.error_message = str(e)
            db.commit()
            logger.error(f"❌ 文档处理失败: {e}")
    else:
        # 异步处理（后台任务）
        background_tasks.add_task(
            process_document_background,
            doc_id, kb_id, current_user.id, file.filename,
            chunk_size, chunk_overlap
        )

    return doc
```

#### B. 改进DocumentProcessor错误处理

```python
# app/rag/document_processor.py

class DocumentProcessor:
    async def process_document(self, file_path, knowledge_base_id,
                               user_id, filename, chunk_size=500,
                               chunk_overlap=50, document_id=None):
        """处理文档（增强错误处理）"""

        try:
            logger.info(f"开始处理文档: {filename}")

            # 1. 读取文件
            logger.info("步骤1: 读取文件内容")
            content = await self._read_file(file_path)
            logger.info(f"  ✅ 文件大小: {len(content)} 字符")

            # 2. 分块
            logger.info("步骤2: 文档分块")
            chunks = await self._chunk_text(content, chunk_size, chunk_overlap)
            logger.info(f"  ✅ 分块完成: {len(chunks)} 个chunks")

            # 3. 向量化
            logger.info("步骤3: 生成向量")
            try:
                embeddings = await self._embed_texts(chunks)
                logger.info(f"  ✅ 向量化完成: {len(embeddings)} 个向量")
            except Exception as e:
                logger.error(f"  ❌ 向量化失败: {e}")
                raise Exception(f"向量化失败: {e}")

            # 4. 存储到ChromaDB
            logger.info("步骤4: 存储到向量数据库")
            try:
                await self._store_vectors(knowledge_base_id, document_id,
                                         user_id, filename, chunks, embeddings)
                logger.info("  ✅ 存储完成")
            except Exception as e:
                logger.error(f"  ❌ 存储失败: {e}")
                raise Exception(f"向量存储失败: {e}")

            return chunks

        except Exception as e:
            logger.error(f"文档处理失败: {e}")
            raise

    async def _store_vectors(self, knowledge_base_id, document_id,
                            user_id, filename, chunks, embeddings):
        """存储向量到ChromaDB（带重试）"""

        max_retries = 3
        for attempt in range(max_retries):
            try:
                rag_config = get_rag_config()
                collection = rag_config.get_or_create_collection(KNOWLEDGE_COLLECTION)

                # 准备数据
                ids = []
                metadatas = []

                for i, chunk in enumerate(chunks):
                    chunk_id = f"{document_id}_{i}" if document_id else f"{uuid.uuid4()}"
                    ids.append(chunk_id)
                    metadatas.append({
                        "knowledge_base_id": knowledge_base_id,
                        "document_id": document_id or "",
                        "user_id": user_id,
                        "filename": filename,
                        "chunk_index": i,
                        "created_at": datetime.now().isoformat()
                    })

                # 添加到collection
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=metadatas
                )

                logger.info(f"✅ 成功存储 {len(chunks)} 个向量")
                return

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    logger.warning(f"存储失败，{wait_time}秒后重试 (尝试 {attempt+1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### 2. Collection健康检查（中优先级）

**优化方案：**

```python
# app/rag/config.py 添加到RAGConfig类

def check_collection_health(self, collection_name: str) -> dict:
    """
    检查collection健康状态

    Returns:
        {
            'healthy': bool,
            'count': int,
            'error': str or None
        }
    """
    result = {'healthy': False, 'count': 0, 'error': None}

    try:
        collection = self.chroma_client.get_collection(collection_name)
        count = collection.count()
        result['healthy'] = True
        result['count'] = count
        logger.info(f"Collection {collection_name} 健康: {count} 个向量")
    except Exception as e:
        result['error'] = str(e)
        logger.warning(f"Collection {collection_name} 不健康: {e}")

    return result

def repair_collection(self, collection_name: str) -> bool:
    """修复损坏的collection"""

    health = self.check_collection_health(collection_name)

    if health['healthy']:
        return True

    logger.warning(f"Collection {collection_name} 损坏，尝试修复...")

    try:
        # 尝试删除
        try:
            self.chroma_client.delete_collection(collection_name)
            logger.info(f"已删除损坏的collection: {collection_name}")
        except:
            pass

        # 创建新collection
        self.chroma_client.create_collection(collection_name)
        logger.info(f"✅ 已重建collection: {collection_name}")

        return True
    except Exception as e:
        logger.error(f"修复失败: {e}")
        return False
```

### 3. 应用启动时自动修复（中优先级）

**优化方案：**

```python
# minimal_api.py 添加启动事件

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化和检查"""

    logger.info("="*60)
    logger.info("系统初始化")
    logger.info("="*60)

    # 1. 检查数据库连接
    logger.info("1. 检查数据库连接...")
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        logger.info("   ✅ 数据库连接正常")
    except Exception as e:
        logger.error(f"   ❌ 数据库连接失败: {e}")

    # 2. 检查ChromaDB
    logger.info("2. 检查ChromaDB...")
    try:
        rag_config = get_rag_config()

        if not rag_config.health_check():
            logger.error("   ❌ ChromaDB连接失败")
            logger.error("   请启动ChromaDB: docker run -d -p 8002:8000 chromadb/chroma:latest")
        else:
            logger.info("   ✅ ChromaDB连接正常")

            # 检查并修复knowledge_chunks collection
            logger.info("3. 检查knowledge_chunks collection...")
            health = rag_config.check_collection_health("knowledge_chunks")

            if not health['healthy']:
                logger.warning(f"   ⚠️  Collection损坏: {health['error']}")
                logger.info("   尝试自动修复...")
                if rag_config.repair_collection("knowledge_chunks"):
                    logger.info("   ✅ Collection修复成功")
                else:
                    logger.error("   ❌ Collection修复失败")
            else:
                logger.info(f"   ✅ Collection健康 ({health['count']} 个向量)")

    except Exception as e:
        logger.error(f"   ❌ ChromaDB初始化失败: {e}")

    logger.info("="*60)
    logger.info("系统初始化完成")
    logger.info("="*60)
```

### 4. 监控和日志（低优先级）

**优化方案：**

```python
# 添加监控端点

@app.get(f"{API_PREFIX}/system/health")
async def system_health_check(current_user: User = Depends(get_current_user)):
    """系统健康检查"""

    health = {
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy',
        'components': {}
    }

    # 检查数据库
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health['components']['database'] = {'status': 'healthy'}
    except Exception as e:
        health['components']['database'] = {'status': 'unhealthy', 'error': str(e)}
        health['status'] = 'degraded'

    # 检查ChromaDB
    try:
        rag_config = get_rag_config()
        collection_health = rag_config.check_collection_health("knowledge_chunks")

        health['components']['chromadb'] = {
            'status': 'healthy' if collection_health['healthy'] else 'unhealthy',
            'vector_count': collection_health['count'],
            'error': collection_health['error']
        }

        if not collection_health['healthy']:
            health['status'] = 'degraded'
    except Exception as e:
        health['components']['chromadb'] = {'status': 'down', 'error': str(e)}
        health['status'] = 'unhealthy'

    # 检查BGE模型
    try:
        rag_config = get_rag_config()
        model = rag_config.embedding_model
        health['components']['embedding_model'] = {
            'status': 'healthy',
            'dimension': model.get_sentence_embedding_dimension()
        }
    except Exception as e:
        health['components']['embedding_model'] = {'status': 'unhealthy', 'error': str(e)}
        health['status'] = 'degraded'

    return health
```

---

## 推荐实施优先级

### 🔴 立即执行（今天）

1. **修复文档处理流程**
   - 添加同步处理选项
   - 改进错误处理和日志
   - 添加重试机制

**预期时间：** 2小时
**影响：** 修复知识库核心功能

### 🟡 本周完成

2. **添加健康检查**
   - Collection健康检查
   - 应用启动时自动修复
   - 系统健康监控端点

**预期时间：** 4小时
**影响：** 提升系统稳定性

### 🟢 本月完成

3. **完善监控和备份**
   - 定期数据备份
   - 详细的性能监控
   - 告警机制

**预期时间：** 1天
**影响：** 长期稳定性保障

---

## 快速修复命令

### 1. 一键重置ChromaDB

```bash
docker stop bright-chat-chromadb && \
docker rm bright-chat-chromadb && \
docker run -d --name bright-chat-chromadb -p 8002:8000 chromadb/chroma:latest
```

### 2. 同步处理文档（绕过后台任务）

```bash
# 使用sync=true参数
curl -X POST http://localhost:8080/api/v1/knowledge/bases/{kb_id}/upload?sync=true \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.txt" \
  -F "chunk_size=500" \
  -F "chunk_overlap=50"
```

### 3. 检查系统健康

```bash
curl http://localhost:8080/api/v1/system/health \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 总结

### 当前状态
- ✅ ChromaDB容器已重置并正常运行
- ❌ 文档后台处理失败
- ❌ 缺少健康检查和自动修复

### 核心问题
**文档处理流程不稳定** - 这是影响知识库功能的关键问题

### 解决方案
1. 添加同步处理选项（临时解决）
2. 改进后台任务队列（根本解决）
3. 添加健康检查和自动恢复（预防措施）

### 建议行动
**优先修复文档处理流程**，这是知识库功能正常工作的前提。
