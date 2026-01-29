# 贡献指南

感谢你考虑为 BrightChat 项目做出贡献！本文档将帮助你了解开发流程和代码规范。

---

## 开发环境设置

### 1. Fork 和 Clone

```bash
# Fork 项目到你的 GitHub 账号
git clone https://github.com/your-username/Bright-Chat.git
cd Bright-Chat

# 添加上游仓库
git remote add upstream https://github.com/original-org/Bright-Chat.git
```

### 2. 本地开发

```bash
# 后端
cd backend-python
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 前端
cd ../frontend
npm install

# 启动 ChromaDB
docker run -d -p 8002:8000 --name bright-chat-chromadb chromadb/chroma:latest
```

### 3. 创建特性分支

```bash
git checkout -b feature/your-feature-name
```

---

## 代码规范

### 代码风格

#### 1. 不可变性（CRITICAL）

**永远创建新对象，不要直接修改**：

```javascript
// 错误：直接修改
function updateUser(user, name) {
  user.name = name  // MUTATION!
  return user
}

// 正确：创建新对象
function updateUser(user, name) {
  return {
    ...user,
    name
  }
}
```

#### 2. 文件组织

- **小文件优于大文件**: 200-400 行典型，800 行上限
- **高内聚低耦合**: 按功能/领域组织，不按类型
- **提取工具函数**: 从大组件中提取可复用逻辑

#### 3. 错误处理

**始终处理错误**：

```typescript
try {
  const result = await riskyOperation()
  return result
} catch (error) {
  console.error('Operation failed:', error)
  throw new Error('Detailed user-friendly message')
}
```

#### 4. 输入验证

```typescript
import { z } from 'zod'

const schema = z.object({
  email: z.string().email(),
  age: z.number().int().min(0).max(150)
})

const validated = schema.parse(input)
```

### 代码质量清单

提交前检查：

- [ ] 代码可读且命名清晰
- [ ] 函数简短（<50 行）
- [ ] 文件聚焦（<800 行）
- [ ] 没有深度嵌套（>4 层）
- [ ] 适当的错误处理
- [ ] 没有 console.log 语句
- [ ] 没有硬编码值
- [ ] 使用了不可变模式

---

## Git 工作流

### 提交消息格式

```
<type>: <description>

<optional body>
```

**类型（type）**：
- `feat` - 新功能
- `fix` - Bug 修复
- `refactor` - 重构
- `docs` - 文档更新
- `test` - 测试相关
- `chore` - 构建/工具相关
- `perf` - 性能优化
- `ci` - CI 配置

**示例**：

```bash
git commit -m "feat: 添加知识库文档分页功能"
git commit -m "fix: 修复 Agent 对话状态同步问题"
git commit -m "docs: 更新 API 文档"
```

### Pull Request 流程

1. **推送分支**
   ```bash
   git push -u origin feature/your-feature-name
   ```

2. **创建 PR**
   - 在 GitHub 上创建 Pull Request
   - 填写 PR 模板
   - 关联相关 Issue

3. **PR 描述模板**
   ```markdown
   ## 概述
   简要描述此 PR 的目的

   ## 变更内容
   - 添加了 XXX 功能
   - 修复了 YYY 问题
   - 重构了 ZZZ 模块

   ## 测试计划
   - [ ] 单元测试通过
   - [ ] 手动测试完成
   - [ ] 文档已更新

   ## 截图（如适用）
   <!-- 添加截图 -->
   ```

---

## 测试要求

### 测试覆盖率

**最低覆盖率**: 80%

### 测试类型

1. **单元测试** - 测试单个函数/组件
2. **集成测试** - 测试 API 端点、数据库操作
3. **E2E 测试** - 测试关键用户流程（Playwright）

### TDD 工作流

```bash
# 1. 编写测试（RED - 应该失败）
pytest tests/test_new_feature.py -v

# 2. 实现功能（GREEN - 通过测试）
# ... 编写代码 ...

# 3. 重构（IMPROVE - 改进代码质量）
# ... 优化代码 ...

# 4. 验证覆盖率
pytest --cov=. --cov-report=html
```

### 测试命令

```bash
# 后端测试
cd backend-python
pytest -v
pytest tests/test_agent_chat.py -v  # 运行特定测试

# 前端测试
cd frontend
npm test
npm run test:e2e  # E2E 测试
```

---

## 安全准则

### 提交前检查

- [ ] 没有硬编码密钥（API keys、密码、tokens）
- [ ] 所有用户输入已验证
- [ ] SQL 注入防护（参数化查询）
- [ ] XSS 防护（HTML 转义）
- [ ] CSRF 保护已启用
- [ ] 认证/授权已验证
- [ ] 所有端点有速率限制
- [ ] 错误消息不泄露敏感信息

### 密钥管理

```typescript
// 错误：硬编码密钥
const apiKey = "sk-proj-xxxxx"

// 正确：环境变量
const apiKey = process.env.OPENAI_API_KEY

if (!apiKey) {
  throw new Error('OPENAI_API_KEY not configured')
}
```

---

## 文档要求

### 代码注释

```python
def process_document(file_path: str, chunk_size: int = 500) -> List[Document]:
    """
    处理文档并将其分割为块。

    Args:
        file_path: 文档文件路径
        chunk_size: 每个块的大小（字符数）

    Returns:
        包含所有文档块的列表

    Raises:
        FileNotFoundError: 如果文件不存在
        ValueError: 如果文件格式不支持
    """
    # 实现代码
    pass
```

### API 文档

所有新 API 端点需要：
1. 在 `MdDocs/` 中添加文档
2. 更新 Swagger 注解（FastAPI）
3. 提供请求/响应示例

---

## 项目特定规范

### 前端

#### 服务层模式

所有 API 调用通过 `services/` 目录：

```typescript
// services/myNewService.ts
export const myNewService = {
  async getItem(id: string) {
    const response = await fetch(`/api/v1/items/${id}`, {
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    })
    if (!response.ok) throw new Error('Failed to fetch')
    return response.json()
  }
}
```

#### 组件组织

```
components/
├── common/           # 通用组件
├── chat/             # 聊天相关
├── admin/            # 管理面板
└── knowledge/        # 知识库相关
```

### 后端

#### 模块结构

```
app/
├── agents/           # Agent 相关
├── rag/              # RAG 知识库
├── api/              # API 路由
├── models/           # 数据模型
├── services/         # 业务逻辑
└── core/             # 核心配置
```

#### 双实现说明

项目有**两个后端实现**：
1. `minimal_api.py` - 单文件实现（当前运行）
2. `app/` - 模块化结构

**重要**: 修改后端时更新 `minimal_api.py`

---

## 获取帮助

### 文档资源

- [CLAUDE.md](CLAUDE.md) - 项目完整指南
- [MdDocs/INDEX.md](MdDocs/INDEX.md) - 文档索引
- [README.md](README.md) - 项目概述

### 问题排查

1. 查看现有 Issues
2. 查看 `MdDocs/*/troubleshooting/` 目录
3. 搜索代码库

---

## 行为准则

1. **尊重他人** - 友好、包容的语言
2. **建设性反馈** - 关注问题，不针对个人
3. **协作优先** - 寻求共识，开放讨论
4. **遵守许可** - 尊重知识产权

---

## 许可

贡献的代码将按照项目的 MIT 许可证发布。

---

**最后更新**: 2026-01-29
