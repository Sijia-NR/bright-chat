#!/usr/bin/env python3
"""
前端代码审查 - 检查 handleToggleActive 函数
"""

# 让我打印出 handleToggleActive 函数的完整代码
code = """
const handleToggleActive = async (agent: AgentAPI) => {
  setLoading(true);
  try {
    await agentService.updateAgent(agent.id, { is_active: !agent.is_active });
    await loadData();
    showMessage('success', agent.is_active ? 'Agent 已下线' : 'Agent 已上线');
    onAgentChange?.();
  } catch (e) {
    showMessage('error', '操作失败，请重试');
  } finally {
    setLoading(false);
  }
};
"""

print("=" * 80)
print("handleToggleActive 函数代码审查")
print("=" * 80)
print(code)
print("=" * 80)

print("\n代码分析:")
print("✓ 函数调用 agentService.updateAgent(agent.id, { is_active: !agent.is_active })")
print("✓ updateAgent 使用 PUT 方法 (已在 agentService.ts:139 确认)")
print("✓ 后端路由 PUT /api/v1/agents/{agent_id} 正确处理更新")
print("\n结论: 前端代码逻辑正确，不应该调用删除 API")
print("\n可能的问题:")
print("1. 用户误点了删除按钮（Power 和 Trash2 图标可能相似）")
print("2. 按钮点击事件被错误绑定")
print("3. 存在其他代码路径调用了删除")
