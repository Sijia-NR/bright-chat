# 知识库API完整文档

## 概述

本文档列出了 Bright-Chat 知识库服务的所有API接口。

**最后更新**: 2026-01-27
**版本**: minimal_api v1.0.0
**Base URL**: `/api/v1`

---

## 认证

所有接口都需要JWT Bearer Token认证：

```bash
# 获取Token
curl -X POST http://localhost:18081/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pwd123"}'

# 使用Token
curl http://localhost:18081/api/v1/knowledge/groups \
  -H "Authorization: Bearer <token>"
```

---

## 知识库分组 API

### 1. 创建知识库分组

**接口**: `POST /api/v1/knowledge/groups`

**请求体**:
```json
{
  "name": "我的文档",
  "description": "个人文档库",
  "color": "#3B82F6"
}
```

**响应**: `KnowledgeGroupResponse`

**示例**:
```bash
curl -X POST http://localhost:18081/api/v1/knowledge/groups \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "工作文档",
    "description": "工作相关的文档",
    "color": "#10B981"
  }'
```

---

### 2. 获取知识库分组列表

**接口**: `GET /api/v1/knowledge/groups`

**响应**: `List[KnowledgeGroupResponse]`

**示例**:
```bash
curl http://localhost:18081/api/v1/knowledge/groups \
  -H "Authorization: Bearer <token>"
```

---

### 3. 删除知识库分组

**接口**: `DELETE /api/v1/knowledge/groups/{group_id}`

**响应**:
```json
{
  "message": "分组删除成功"
}
```

**示例**:
```bash
curl -X DELETE http://localhost:18081/api/v1/knowledge/groups/<group_id> \
  -H "Authorization: Bearer <token>"
```

---

## 知识库 API

### 4. 创建知识库

**接口**: `POST /api/v1/knowledge/bases`

**请求体**:
```json
{
  "name": "技术文档库",
  "description": "存储技术相关文档",
  "group_id": "分组ID（可选）",
  "embedding_model": "bge-large-zh-v1.5",
  "chunk_size": 500,
  "chunk_overlap": 50
}
```

**响应**: `KnowledgeBaseResponse`

**示例**:
```bash
curl -X POST http://localhost:18081/api/v1/knowledge/bases \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试知识库",
    "description": "用于测试"
  }'
```

---

### 5. 获取知识库列表

**接口**: `GET /api/v1/knowledge/bases`

**响应**: `List[KnowledgeBaseResponse]`

**示例**:
```bash
curl http://localhost:18081/api/v1/knowledge/bases \
  -H "Authorization: Bearer <token>"
```

---

### 6. 获取知识库详情

**接口**: `GET /api/v1/knowledge/bases/{kb_id}`

**响应**: `KnowledgeBaseResponse`

**示例**:
```bash
curl http://localhost:18081/api/v1/knowledge/bases/<kb_id> \
  -H "Authorization: Bearer <token>"
```

---

### 7. 更新知识库

**接口**: `PUT /api/v1/knowledge/bases/{kb_id}`

**请求体**:
```json
{
  "name": "新名称",
  "description": "新描述",
  "group_id": "新分组ID",
  "is_active": true
}
```

**响应**: `KnowledgeBaseResponse`

**示例**:
```bash
curl -X PUT http://localhost:18081/api/v1/knowledge/bases/<kb_id> \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "更新后的名称"
  }'
```

---

### 8. 删除知识库

**接口**: `DELETE /api/v1/knowledge/bases/{kb_id}`

**响应**:
```json
{
  "message": "知识库删除成功"
}
```

**示例**:
```bash
curl -X DELETE http://localhost:18081/api/v1/knowledge/bases/<kb_id> \
  -H "Authorization: Bearer <token>"
```

---

## 文档管理 API

### 9. 上传文档

**接口**: `POST /api/v1/knowledge/bases/{kb_id}/documents`

**Content-Type**: `multipart/form-data`

**参数**:
- `file`: 文件（form-data）

**响应**: `DocumentResponse`

**示例**:
```bash
curl -X POST http://localhost:18081/api/v1/knowledge/bases/<kb_id>/documents \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/document.pdf"
```

---

### 10. 获取文档列表

**接口**: `GET /api/v1/knowledge/bases/{kb_id}/documents`

**响应**: `List[DocumentResponse]`

**示例**:
```bash
curl http://localhost:18081/api/v1/knowledge/bases/<kb_id>/documents \
  -H "Authorization: Bearer <token>"
```

---

### 11. 获取文档详情

**接口**: `GET /api/v1/knowledge/documents/{doc_id}`

**响应**: `DocumentResponse`

**示例**:
```bash
curl http://localhost:18081/api/v1/knowledge/documents/<doc_id> \
  -H "Authorization: Bearer <token>"
```

---

### 12. 删除文档

**接口**: `DELETE /api/v1/knowledge/documents/{doc_id}`

**响应**:
```json
{
  "message": "文档删除成功"
}
```

**示例**:
```bash
curl -X DELETE http://localhost:18081/api/v1/knowledge/documents/<doc_id> \
  -H "Authorization: Bearer <token>"
```

---

### 13. 获取文档切片

**接口**: `GET /api/v1/knowledge/documents/{doc_id}/chunks`

**查询参数**:
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认15）
- `include_embeddings`: 是否包含向量（默认false）

**响应**: `DocumentChunksListResponse`

**结构**:
```json
{
  "document_id": "文档ID",
  "filename": "文件名.pdf",
  "total_chunks": 10,
  "chunks": [],
  "pagination": {
    "page": 1,
    "page_size": 15,
    "total_count": 10,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

**示例**:
```bash
curl "http://localhost:18081/api/v1/knowledge/documents/<doc_id>/chunks?page=1&page_size=15" \
  -H "Authorization: Bearer <token>"
```

---

## 数据模型

### KnowledgeGroup

```python
{
  "id": "uuid",
  "name": "分组名称",
  "description": "分组描述",
  "user_id": "用户ID",
  "color": "#3B82F6",
  "created_at": "2026-01-27T..."
}
```

### KnowledgeBase

```python
{
  "id": "uuid",
  "name": "知识库名称",
  "description": "知识库描述",
  "user_id": "用户ID",
  "group_id": "分组ID（可选）",
  "embedding_model": "bge-large-zh-v1.5",
  "chunk_size": 500,
  "chunk_overlap": 50,
  "is_active": true,
  "created_at": "2026-01-27T...",
  "updated_at": "2026-01-27T...",
  "document_count": 0
}
```

### Document

```python
{
  "id": "uuid",
  "knowledge_base_id": "知识库ID",
  "filename": "document.pdf",
  "file_type": "application/pdf",
  "file_size": 12345,
  "chunk_count": 0,
  "upload_status": "completed",
  "error_message": null,
  "uploaded_at": "2026-01-27T...",
  "processed_at": "2026-01-27T..."
}
```

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或Token无效 |
| 403 | 无权限访问资源 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 使用场景示例

### 场景1: 创建完整知识库

```bash
# 1. 登录获取Token
TOKEN=$(curl -s -X POST http://localhost:18081/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"pwd123"}' \
  | jq -r '.token')

# 2. 创建知识库分组
GROUP_ID=$(curl -s -X POST http://localhost:18081/api/v1/knowledge/groups \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"项目文档","color":"#10B981"}' \
  | jq -r '.id')

# 3. 创建知识库
KB_ID=$(curl -s -X POST http://localhost:18081/api/v1/knowledge/bases \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"项目资料\",\"group_id\":\"$GROUP_ID\"}" \
  | jq -r '.id')

# 4. 上传文档
curl -X POST http://localhost:18081/api/v1/knowledge/bases/$KB_ID/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@project.pdf"

# 5. 查看文档列表
curl http://localhost:18081/api/v1/knowledge/bases/$KB_ID/documents \
  -H "Authorization: Bearer $TOKEN"
```

### 场景2: 查询知识库内容

```bash
TOKEN="..."

# 获取所有分组
curl http://localhost:18081/api/v1/knowledge/groups \
  -H "Authorization: Bearer $TOKEN"

# 获取所有知识库
curl http://localhost:18081/api/v1/knowledge/bases \
  -H "Authorization: Bearer $TOKEN"

# 获取特定知识库的文档
curl http://localhost:18081/api/v1/knowledge/bases/<kb_id>/documents \
  -H "Authorization: Bearer $TOKEN"

# 获取文档的切片
curl "http://localhost:18081/api/v1/knowledge/documents/<doc_id>/chunks?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 注意事项

1. **权限**: 所有操作只能访问当前用户创建的资源
2. **文件上传**: 支持所有文件类型，建议大小限制50MB
3. **分页**: 文档切片查询支持分页，默认每页15条
4. **删除**: 删除知识库会级联删除其下所有文档
5. **认证**: Token有效期24小时，过期需要重新登录

---

**相关文档**:
- CLAUDE.md - 项目开发指南
- MdDocs/knowledge-base/api/knowledge-base-api.md - 原始知识库API文档
- MdDocs/common/deployment/unified-deployment.md - 部署指南
