/**
 * Agent 管理面板
 * Agent Management Panel
 *
 * 提供数字员工（Agent）的配置管理功能
 * Provides configuration and management for digital employees (Agents)
 */
import React, { useState, useEffect } from 'react';
import {
  Bot,
  Plus,
  Edit2,
  Trash2,
  Power,
  Loader2,
  X,
  Eye,
  EyeOff,
} from 'lucide-react';
import { agentService } from '../services/agentService';
import { knowledgeService } from '../services/knowledgeService';
import { AgentAPI, KnowledgeBaseAPI, LLMModelSelectItem } from '../types';

interface AgentManagementPanelProps {
  refreshTrigger?: number;
  onAgentChange?: () => void;
}

// Agent 类型配置
const AGENT_TYPES = [
  { value: 'rag', label: '知识库增强型', color: 'bg-purple-100 text-purple-600' },
  { value: 'tool', label: '工具型', color: 'bg-blue-100 text-blue-600' },
  { value: 'custom', label: '自定义型', color: 'bg-green-100 text-green-600' },
];

// 可用工具（必须与后端 AVAILABLE_TOOLS 保持一致）
const AVAILABLE_TOOLS = [
  { value: 'knowledge_search', label: '知识库检索' },
  { value: 'web_search', label: '网络搜索' },
  { value: 'calculator', label: '计算器' },
  { value: 'code_interpreter', label: '代码解释器' },
  { value: 'database_query', label: '数据库查询' },
];

const AgentManagementPanel: React.FC<AgentManagementPanelProps> = ({
  refreshTrigger = 0,
  onAgentChange,
}) => {
  // 状态管理
  const [agents, setAgents] = useState<AgentAPI[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseAPI[]>([]);
  const [llmModels, setLLMModels] = useState<LLMModelSelectItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const [editingAgent, setEditingAgent] = useState<AgentAPI | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // 表单状态
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    agent_type: 'rag',
    system_prompt: '',
    enable_knowledge: false,              // 是否启用知识库功能
    tools: [] as string[],
    knowledge_base_ids: [] as string[],   // 仅用于更新时设置默认知识库
    llm_model_id: undefined as string | undefined,
    config: {
      temperature: 0.7,
      max_steps: 10,
      timeout: 300,
    },
  });

  // 加载数据
  useEffect(() => {
    loadData();
  }, [refreshTrigger]);

  // 刷新 Agent 列表（不重新加载模型和知识库）
  const refreshAgents = async () => {
    try {
      const agentsData = await agentService.getAgents();
      setAgents(agentsData);
    } catch (e) {
      console.error('Failed to refresh agents:', e);
    }
  };

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

  // 显示消息
  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  // 重置表单
  const resetForm = () => {
    setFormData({
      name: '',
      display_name: '',
      description: '',
      agent_type: 'rag',
      system_prompt: '',
      enable_knowledge: false,
      tools: [],
      knowledge_base_ids: [],
      llm_model_id: undefined,
      config: {
        temperature: 0.7,
        max_steps: 10,
        timeout: 300,
      },
    });
  };

  // 开始编辑
  const handleEdit = (agent: AgentAPI) => {
    setEditingAgent(agent);
    setFormData({
      name: agent.name,
      display_name: agent.display_name || '',
      description: agent.description || '',
      agent_type: agent.agent_type,
      system_prompt: agent.system_prompt || '',
      enable_knowledge: (agent as any).enable_knowledge || false,
      tools: agent.tools || [],
      knowledge_base_ids: agent.knowledge_base_ids || [],
      llm_model_id: agent.llm_model_id || undefined,
      config: agent.config || {
        temperature: 0.7,
        max_steps: 10,
        timeout: 300,
      },
    });
    setShowForm(true);
  };

  // 取消编辑
  const cancelEdit = () => {
    setEditingAgent(null);
    resetForm();
    setShowForm(false);
  };

  // 提交表单
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      // 验证：启用知识库功能时必须包含 knowledge_search 工具
      if (formData.enable_knowledge && !formData.tools.includes('knowledge_search')) {
        showMessage('error', '启用知识库功能时，必须包含"知识库检索"工具');
        setLoading(false);
        return;
      }

      if (editingAgent) {
        // 更新 - 支持所有字段包括 knowledge_base_ids（设置默认知识库）
        await agentService.updateAgent(editingAgent.id, formData);
        showMessage('success', 'Agent 更新成功');
      } else {
        // 创建 - 不传递 knowledge_base_ids
        const { knowledge_base_ids, ...createData } = formData as any;
        await agentService.createAgent(createData);
        showMessage('success', 'Agent 创建成功');
      }

      await loadData();
      cancelEdit();
      onAgentChange?.();
    } catch (e: any) {
      console.error('Submit failed:', e);
      showMessage('error', e?.message || '操作失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 删除 Agent
  const executeDelete = async (agentId: string) => {
    setActionLoadingId(agentId);
    try {
      await agentService.deleteAgent(agentId);
      setAgents(prev => prev.filter(a => a.id !== agentId));
      setPendingDeleteId(null);
      showMessage('success', 'Agent 删除成功');
      onAgentChange?.();
    } catch (e) {
      showMessage('error', '删除失败，请重试');
    } finally {
      setActionLoadingId(null);
    }
  };

  // 切换上线/下线状态
  const handleToggleActive = async (agent: AgentAPI) => {
    const newStatus = !agent.is_active;

    // 乐观更新：立即更新 UI
    setAgents(prevAgents =>
      prevAgents.map(a =>
        a.id === agent.id
          ? { ...a, is_active: newStatus }
          : a
      )
    );

    try {
      // 调用 API 更新后端
      await agentService.updateAgent(agent.id, { is_active: newStatus });
      showMessage('success', newStatus ? 'Agent 已上线' : 'Agent 已下线');

      // 刷新 Agent 列表以获取最新数据（不加载模型和知识库）
      await refreshAgents();
    } catch (e) {
      console.error('切换 Agent 状态失败:', e);
      showMessage('error', '操作失败，请重试');
      // 失败时恢复状态并重新加载
      await refreshAgents();
    }
  };

  // 获取 Agent 类型标签
  const getAgentTypeLabel = (type: string) => {
    return AGENT_TYPES.find(t => t.value === type)?.label || type;
  };

  // 获取 Agent 类型颜色
  const getAgentTypeColor = (type: string) => {
    return AGENT_TYPES.find(t => t.value === type)?.color || 'bg-gray-100 text-gray-600';
  };

  return (
    <div className="bg-white rounded-[32px] p-8 border border-gray-100 shadow-sm min-h-[500px]">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-2xl">
            <Bot size={24} />
          </div>
          <h2 className="text-lg font-bold text-gray-800">数字员工配置</h2>
        </div>
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-sm font-bold transition-all active:scale-95"
          >
            <Plus size={18} />
            创建 Agent
          </button>
        )}
      </div>

      {/* 表单 */}
      {showForm && (
        <div className="mb-8 p-6 bg-gray-50 rounded-2xl animate-in slide-in-from-top-2 duration-300">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-sm font-bold text-gray-700">
              {editingAgent ? '编辑 Agent' : '创建新 Agent'}
            </h3>
            <button onClick={cancelEdit} className="text-gray-400 hover:text-gray-600">
              <X size={20} />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 基础信息 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                  Agent 标识（英文）
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  disabled={!!editingAgent}
                  placeholder="如: research_assistant"
                  className="w-full px-4 py-3 bg-white border-2 border-gray-100 rounded-xl outline-none focus:border-emerald-500 transition-all text-sm disabled:bg-gray-100"
                />
              </div>
              <div>
                <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                  显示名称（中文）
                </label>
                <input
                  type="text"
                  value={formData.display_name}
                  onChange={e => setFormData(prev => ({ ...prev, display_name: e.target.value }))}
                  placeholder="如: 研究助手"
                  className="w-full px-4 py-3 bg-white border-2 border-gray-100 rounded-xl outline-none focus:border-emerald-500 transition-all text-sm"
                />
              </div>
            </div>

            {/* Agent 类型 */}
            <div>
              <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                Agent 类型
              </label>
              <select
                value={formData.agent_type}
                onChange={e => setFormData(prev => ({ ...prev, agent_type: e.target.value }))}
                className="w-full px-4 py-3 bg-white border-2 border-gray-100 rounded-xl outline-none focus:border-emerald-500 transition-all text-sm appearance-none"
              >
                {AGENT_TYPES.map(type => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
            </div>

            {/* LLM 模型选择 */}
            <div>
              <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                LLM 模型
              </label>
              <select
                value={formData.llm_model_id || ''}
                onChange={e => setFormData(prev => ({
                  ...prev,
                  llm_model_id: e.target.value || undefined
                }))}
                className="w-full px-4 py-3 bg-white border-2 border-gray-100 rounded-xl outline-none focus:border-emerald-500 transition-all text-sm appearance-none"
              >
                <option value="">使用默认模型</option>
                {llmModels.map(model => (
                  <option key={model.id} value={model.id}>
                    {model.display_name} {model.provider_name ? `(${model.provider_name})` : ''}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-400 mt-1 ml-1">
                不选择时使用系统默认的第一个激活模型
              </p>
            </div>

            {/* 描述 */}
            <div>
              <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                描述信息（可选）
              </label>
              <textarea
                value={formData.description}
                onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="描述这个 Agent 的功能和用途"
                rows={2}
                className="w-full px-4 py-3 bg-white border-2 border-gray-100 rounded-xl outline-none focus:border-emerald-500 transition-all text-sm resize-none"
              />
            </div>

            {/* 知识库功能开关 */}
            <div>
              <label className="flex items-center gap-3 px-4 py-3 bg-white border-2 border-gray-100 rounded-xl cursor-pointer hover:border-purple-200 transition-all">
                <input
                  type="checkbox"
                  checked={formData.enable_knowledge}
                  onChange={e => {
                    const newValue = e.target.checked;
                    if (newValue) {
                      // 启用时自动添加 knowledge_search 工具
                      setFormData(prev => ({
                        ...prev,
                        enable_knowledge: true,
                        tools: [...new Set([...prev.tools, 'knowledge_search'])]
                      }));
                    } else {
                      // 禁用时移除 knowledge_search 工具
                      setFormData(prev => ({
                        ...prev,
                        enable_knowledge: false,
                        tools: prev.tools.filter(t => t !== 'knowledge_search')
                      }));
                    }
                  }}
                  className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
                />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-700">启用知识库检索功能</div>
                  <div className="text-xs text-gray-400">启用后可在聊天时动态指定知识库，系统会自动添加"知识库检索"工具</div>
                </div>
                {formData.enable_knowledge && (
                  <span className="px-2 py-1 bg-purple-100 text-purple-600 text-xs rounded-lg font-bold">已启用</span>
                )}
              </label>
            </div>

            {/* 工具配置 */}
            <div>
              <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                工具配置（可选）
              </label>
              <div className="grid grid-cols-2 gap-2">
                {AVAILABLE_TOOLS.map(tool => {
                  const isKnowledgeSearch = tool.value === 'knowledge_search';
                  const isDisabled = isKnowledgeSearch && formData.enable_knowledge;

                  return (
                    <label
                      key={tool.value}
                      className={`flex items-center gap-2 px-4 py-3 bg-white border-2 rounded-xl transition-all ${
                        formData.tools.includes(tool.value)
                          ? 'border-emerald-500 bg-emerald-50'
                          : 'border-gray-100 hover:border-gray-200'
                      } ${isDisabled ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
                    >
                      <input
                        type="checkbox"
                        checked={formData.tools.includes(tool.value)}
                        disabled={isDisabled}
                        onChange={e => {
                          if (e.target.checked) {
                            setFormData(prev => ({ ...prev, tools: [...prev.tools, tool.value] }));
                          } else {
                            setFormData(prev => ({ ...prev, tools: prev.tools.filter(t => t !== tool.value) }));
                          }
                        }}
                        className="w-4 h-4 text-emerald-600 rounded"
                      />
                      <span className="text-sm text-gray-700">{tool.label}</span>
                      {isKnowledgeSearch && formData.enable_knowledge && (
                        <span className="text-xs text-purple-600 ml-auto">（已自动启用）</span>
                      )}
                    </label>
                  );
                })}
              </div>
              {formData.enable_knowledge && (
                <p className="text-xs text-purple-600 mt-2 ml-1 flex items-center gap-1">
                  💡 知识库检索工具已自动启用，无需手动勾选
                </p>
              )}
            </div>

            {/* 默认知识库（仅编辑模式且启用知识库功能时显示） */}
            {editingAgent && formData.enable_knowledge && knowledgeBases.length > 0 && (
              <div>
                <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                  默认知识库（可选）
                </label>
                <p className="text-xs text-gray-400 mb-2 ml-1">
                  设置此 Agent 的默认知识库，聊天时如未指定知识库将使用这些知识库
                </p>
                <div className="max-h-40 overflow-y-auto space-y-2 p-3 bg-white border-2 border-gray-100 rounded-xl">
                  {knowledgeBases.map(kb => (
                    <label
                      key={kb.id}
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all ${
                        formData.knowledge_base_ids?.includes(kb.id)
                          ? 'bg-purple-50'
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={formData.knowledge_base_ids?.includes(kb.id) || false}
                        onChange={e => {
                          if (e.target.checked) {
                            setFormData(prev => ({
                              ...prev,
                              knowledge_base_ids: [...(prev.knowledge_base_ids || []), kb.id],
                            }));
                          } else {
                            setFormData(prev => ({
                              ...prev,
                              knowledge_base_ids: prev.knowledge_base_ids?.filter(id => id !== kb.id) || [],
                            }));
                          }
                        }}
                        className="w-4 h-4 text-purple-600 rounded"
                      />
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-700">{kb.name}</div>
                        <div className="text-xs text-gray-400">{kb.document_count} 个文档</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* 系统提示词 */}
            <div>
              <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                系统提示词（可选）
              </label>
              <textarea
                value={formData.system_prompt}
                onChange={e => setFormData(prev => ({ ...prev, system_prompt: e.target.value }))}
                placeholder="为 Agent 设置系统提示词，定义其行为和回答风格"
                rows={4}
                className="w-full px-4 py-3 bg-white border-2 border-gray-100 rounded-xl outline-none focus:border-emerald-500 transition-all text-sm resize-none font-mono"
              />
            </div>

            {/* 高级配置 */}
            <details className="group">
              <summary className="cursor-pointer text-[11px] font-black text-gray-400 uppercase tracking-widest mb-3 ml-1 list-none flex items-center gap-2">
                <span>高级配置</span>
                <span className="group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="grid grid-cols-3 gap-4 p-4 bg-white border-2 border-gray-100 rounded-xl">
                <div>
                  <label className="text-xs font-medium text-gray-600 mb-1 block">Temperature</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    value={formData.config.temperature}
                    onChange={e => setFormData(prev => ({
                      ...prev,
                      config: { ...prev.config, temperature: parseFloat(e.target.value) || 0.7 }
                    }))}
                    className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-600 mb-1 block">最大步数</label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={formData.config.max_steps}
                    onChange={e => setFormData(prev => ({
                      ...prev,
                      config: { ...prev.config, max_steps: parseInt(e.target.value) || 10 }
                    }))}
                    className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-600 mb-1 block">超时（秒）</label>
                  <input
                    type="number"
                    min="10"
                    max="600"
                    value={formData.config.timeout}
                    onChange={e => setFormData(prev => ({
                      ...prev,
                      config: { ...prev.config, timeout: parseInt(e.target.value) || 300 }
                    }))}
                    className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
                  />
                </div>
              </div>
            </details>

            {/* 提交按钮 */}
            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold transition-all active:scale-[0.98] disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="animate-spin mx-auto" size={20} />
                ) : (
                  editingAgent ? '更新 Agent' : '创建 Agent'
                )}
              </button>
              <button
                type="button"
                onClick={cancelEdit}
                className="px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-bold transition-all"
              >
                取消
              </button>
            </div>
          </form>
        </div>
      )}

      {/* 消息提示 */}
      {message && (
        <div className={`mb-4 p-4 rounded-xl flex items-center justify-between ${
          message.type === 'success'
            ? 'bg-green-50 text-green-700 border border-green-100'
            : 'bg-red-50 text-red-700 border border-red-100'
        }`}>
          <span className="text-sm font-bold">{message.text}</span>
          <button onClick={() => setMessage(null)}>
            <X size={16} />
          </button>
        </div>
      )}

      {/* Agent 列表 */}
      {loading && !showForm ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="animate-spin text-gray-400" size={32} />
        </div>
      ) : agents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <Bot size={36} className="text-gray-300" />
          </div>
          <h3 className="text-lg font-bold text-gray-600 mb-2">还未创建任何数字员工</h3>
          <p className="text-sm text-gray-400 mb-6">创建您的第一个 Agent 开始使用智能助手功能</p>
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold transition-all"
          >
            <Plus size={18} />
            创建第一个 Agent
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {agents.map(agent => (
            <div
              key={agent.id}
              className={`group p-5 border rounded-2xl transition-all ${
                agent.is_active
                  ? 'border-gray-100 hover:bg-gray-50/50'
                  : 'border-gray-100 bg-gray-50 opacity-70'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  {/* 标题行 */}
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-bold text-gray-900">
                      {agent.display_name || agent.name}
                    </span>
                    <span className={`px-2 py-0.5 text-[10px] rounded-lg font-black uppercase ${getAgentTypeColor(agent.agent_type)}`}>
                      {getAgentTypeLabel(agent.agent_type)}
                    </span>
                    {agent.is_active ? (
                      <span className="px-2 py-0.5 bg-green-100 text-green-600 text-[10px] rounded-lg font-bold">上线</span>
                    ) : (
                      <span className="px-2 py-0.5 bg-gray-200 text-gray-500 text-[10px] rounded-lg font-bold">下线</span>
                    )}
                  </div>

                  {/* 详情行 */}
                  <div className="text-xs text-gray-400 space-y-1">
                    <div>标识: <span className="font-mono text-gray-600">{agent.name}</span></div>
                    {agent.description && <div className="text-gray-500">{agent.description}</div>}

                    {/* 标签 */}
                    <div className="flex flex-wrap gap-2 mt-2">
                      {agent.llm_model_name && (
                        <span className="px-2 py-1 bg-indigo-50 text-indigo-600 rounded-lg flex items-center gap-1 text-xs">
                          模型: {agent.llm_model_name}
                        </span>
                      )}
                      {(agent as any).enable_knowledge && (
                        <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-lg flex items-center gap-1 text-xs font-bold">
                          📚 知识库功能
                        </span>
                      )}
                      {agent.tools && agent.tools.length > 0 && (
                        <span className="px-2 py-1 bg-blue-50 text-blue-600 rounded-lg flex items-center gap-1 text-xs">
                          工具: {agent.tools.length}
                        </span>
                      )}
                      {!editingAgent && agent.knowledge_base_ids && agent.knowledge_base_ids.length > 0 && (
                        <span className="px-2 py-1 bg-purple-50 text-purple-600 rounded-lg flex items-center gap-1 text-xs">
                          默认知识库: {agent.knowledge_base_ids.length}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* 操作按钮 */}
                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => handleEdit(agent)}
                    className="p-2 text-gray-300 hover:text-emerald-600 hover:bg-emerald-50 rounded-xl transition-all opacity-0 group-hover:opacity-100"
                    title="编辑"
                  >
                    <Edit2 size={18} />
                  </button>
                  <button
                    onClick={() => handleToggleActive(agent)}
                    className={`p-2 rounded-xl transition-all opacity-0 group-hover:opacity-100 ${
                      agent.is_active
                        ? 'text-gray-300 hover:text-orange-600 hover:bg-orange-50'
                        : 'text-green-500 hover:text-green-600 hover:bg-green-50'
                    }`}
                    title={agent.is_active ? '下线 Agent' : '上线 Agent'}
                  >
                    <Power size={18} />
                  </button>
                  <button
                    onClick={() => setPendingDeleteId(agent.id)}
                    className="p-2 text-gray-300 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all opacity-0 group-hover:opacity-100 border border-transparent hover:border-red-200"
                    title="删除 Agent（无法撤销）"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 删除确认 */}
      {pendingDeleteId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 animate-in fade-in">
          <div className="bg-white rounded-2xl p-6 max-w-sm mx-4 shadow-2xl animate-in zoom-in-95">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Trash2 size={32} className="text-red-600" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">确认删除 Agent</h3>
              <p className="text-sm text-gray-500">此操作无法撤销，确定要删除这个数字员工吗？</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setPendingDeleteId(null)}
                className="flex-1 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-bold transition-all"
              >
                取消
              </button>
              <button
                onClick={() => executeDelete(pendingDeleteId)}
                disabled={actionLoadingId === pendingDeleteId}
                className="flex-1 py-3 bg-red-600 hover:bg-red-700 text-white rounded-xl font-bold transition-all disabled:opacity-50"
              >
                {actionLoadingId === pendingDeleteId ? (
                  <Loader2 size={20} className="animate-spin mx-auto" />
                ) : (
                  '确认删除'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentManagementPanel;
