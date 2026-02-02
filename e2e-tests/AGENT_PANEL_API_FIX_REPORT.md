# Agent 管理面板 API 调用问题修复报告

## 问题描述

用户报告：点击 Agent 管理时调用了多个接口，其中有些返回 404 错误

## 网络请求日志分析

### ❌ 失败的请求

| 端点 | 状态码 | 错误 | 调用位置 |
|------|--------|------|----------|
| `/knowledge/bases` | 404 | Not Found | `knowledgeService.ts:125` |
| `/agents/models/` | 307 → 404 | 重定向后失败 | `agentService.ts:347` |
| `/models` | 404 | Not Found | 重定向目标 |

### ✅ 成功的请求

| 端点 | 状态码 | 说明 |
|------|--------|------|
| `/agents/` | 200 | Agent 列表获取成功 |
| `/models/active` | 200 | 活跃模型列表获取成功 |

## 根本原因分析

### 问题 1: `getKnowledgeBases()` 调用错误

**错误代码** (`AgentManagementPanel.tsx:88`):
```typescript
const [agentsData, kbData, modelsData] = await Promise.all([
  agentService.getAgents(),
  knowledgeService.getKnowledgeBases(),  // ❌ 缺少 groupId 参数
  agentService.getActiveLLMModels(),
]);
```

**问题分析**:
- `knowledgeService.getKnowledgeBases(groupId)` 需要传入 `groupId` 参数
- 但调用时没有传入，导致调用 `/knowledge/bases`（错误端点）
- 后端实际端点是 `/knowledge/groups/{groupId}/bases`

**影响**:
- 返回 404 错误
- 知识库列表无法加载

### 问题 2: `getActiveLLMModels()` 端点错误

**错误代码** (`agentService.ts:347`):
```typescript
async getActiveLLMModels(): Promise<any[]> {
  const response = await fetch(`${CONFIG.API_BASE_URL}/agents/models/`, {
    // ❌ 错误端点
    headers: getAuthHeaders()
  });
  // ...
}
```

**问题分析**:
- 前端调用 `/agents/models/`（不存在）
- 后端实际端点是 `/models/active`
- 这可能是从独立的 `agent-service` 遗留的代码
- Nginx 配置了 307 重定向，但重定向目标 `/models` 也不存在

**影响**:
- 307 重定向到 `/models`
- `/models` 返回 404
- 模型列表无法加载

## 修复方案

### 修复 1: 修正知识库加载逻辑

**修复后的代码** (`AgentManagementPanel.tsx:83-113`):
```typescript
const loadData = async () => {
  setLoading(true);
  try {
    const [agentsData, modelsData] = await Promise.all([
      agentService.getAgents(),
      agentService.getActiveLLMModels(),
    ]);
    setAgents(agentsData);
    setLLMModels(modelsData);

    // 知识库列表需要先获取分组，再获取每个分组的知识库
    try {
      const groups = await knowledgeService.getKnowledgeGroups();
      const allKbs: KnowledgeBaseAPI[] = [];
      for (const group of groups) {
        const kbs = await knowledgeService.getKnowledgeBases(group.id);
        allKbs.push(...kbs);
      }
      setKnowledgeBases(allKbs);
    } catch (kbError) {
      console.warn('Failed to load knowledge bases:', kbError);
      // 不阻塞整个加载流程
      setKnowledgeBases([]);
    }
  } catch (e) {
    console.error('Failed to load data:', e);
    showMessage('error', '加载数据失败');
  } finally {
    setLoading(false);
  }
};
```

**修复说明**:
1. 先获取 Agent 和模型数据（并行）
2. 单独处理知识库数据（顺序加载）
3. 先获取所有分组
4. 遍历每个分组，获取其知识库
5. 合并所有知识库到列表
6. 错误处理：知识库加载失败不阻塞整体加载

### 修复 2: 修正模型列表端点

**修复后的代码** (`agentService.ts:343-359`):
```typescript
/**
 * 获取活跃的 LLM 模型列表
 * 注意：使用 /models/active 端点，不是 /agents/models/
 */
async getActiveLLMModels(): Promise<any[]> {
  const response = await fetch(`${CONFIG.API_BASE_URL}/models/active`, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取模型列表失败');
  }

  const data = await response.json();
  return data.models || [];
}
```

**修复说明**:
1. 修改端点从 `/agents/models/` 到 `/models/active`
2. 添加注释说明正确的端点
3. 保持错误处理逻辑不变

## 验证结果

### 预期的网络请求

修复后，Agent 管理面板加载时的网络请求应该是：

| 端点 | 方法 | 预期状态 | 说明 |
|------|------|----------|------|
| `/agents/` | GET | 200 | ✅ 获取 Agent 列表 |
| `/models/active` | GET | 200 | ✅ 获取活跃模型 |
| `/knowledge/groups` | GET | 200 | ✅ 获取知识库分组 |
| `/knowledge/groups/{id}/bases` | GET | 200 | ✅ 获取每个分组的知识库 |

### 消除的错误

- ❌ `GET /knowledge/bases` - 404（已消除）
- ❌ `GET /agents/models/` - 307 → 404（已消除）
- ❌ `GET /models` - 404（已消除）

## 相关文件

### 修改的文件

1. **frontend/components/AgentManagementPanel.tsx**
   - 修正 `loadData()` 函数
   - 添加知识库分步加载逻辑
   - 添加错误处理

2. **frontend/services/agentService.ts**
   - 修正 `getActiveLLMModels()` 端点
   - 添加注释说明

### 后端端点文档

| 端点 | 方法 | 说明 |
|------|------|------|
| `/agents/` | GET | 获取 Agent 列表 |
| `/models/active` | GET | 获取活跃的模型列表 |
| `/admin/models` | GET | 获取所有模型（管理员） |
| `/knowledge/groups` | GET | 获取知识库分组列表 |
| `/knowledge/groups/{id}/bases` | GET | 获取指定分组的知识库列表 |

## 总结

通过系统化调试分析，我们发现并修复了两个 API 调用问题：

1. **知识库加载问题**: 缺少必需的 `groupId` 参数
2. **模型列表端点错误**: 调用了不存在的 `/agents/models/` 端点

修复后，Agent 管理面板应该能正常加载所有数据，不再有 404 错误。

## 建议

1. **API 文档同步**: 确保 API 文档与实际端点一致
2. **前端服务层审查**: 检查其他类似的服务调用是否也有端点错误
3. **错误处理增强**: 为所有 API 调用添加更详细的错误日志
4. **自动化测试**: 添加 E2E 测试验证 Agent 管理面板加载流程

---

**修复时间**: 2026-01-28
**修复方法**: 系统化调试（Phase 1-4）
**修复原则**: 找到根本原因后修复，不修复症状
