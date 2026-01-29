/**
 * Agent 配置面板
 * Agent Configuration Panel
 *
 * 用于管理员创建和配置数字员工
 * For admins to create and configure digital employees
 */
import { useState, useEffect } from 'react';
import { Robot, Plus, Trash2, Edit, X, Save } from 'lucide-react';
import { agentService } from '../services/agentService';
import { knowledgeService } from '../services/knowledgeService';
import { AgentAPI, AgentTool, KnowledgeBaseAPI } from '../types';
import ToolSelector from './ToolSelector';

interface AgentConfigProps {
  onClose?: () => void;
}

interface AgentFormData {
  name: string;
  display_name: string;
  description: string;
  agent_type: string;
  system_prompt?: string;
  tools: string[];
  knowledge_base_ids?: string[];
  llm_model_id?: string;
  config: Record<string, any>;
  is_active: boolean;
}

const INITIAL_FORM: AgentFormData = {
  name: '',
  display_name: '',
  description: '',
  agent_type: 'tool',
  system_prompt: '',
  tools: [],
  knowledge_base_ids: [],
  llm_model_id: undefined,
  config: {
    temperature: 0.7,
    max_steps: 10,
    timeout: 300,
  },
  is_active: true,
};

export function AgentConfig({ onClose }: AgentConfigProps) {
  const [agents, setAgents] = useState<AgentAPI[]>([]);
  const [tools, setTools] = useState<AgentTool[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseAPI[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingAgent, setEditingAgent] = useState<AgentAPI | null>(null);
  const [formData, setFormData] = useState<AgentFormData>(INITIAL_FORM);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [agentsData, toolsData, kbData] = await Promise.all([
        agentService.getAgents(),
        agentService.getAvailableTools(),
        knowledgeService.getKnowledgeBases(),
      ]);
      setAgents(agentsData);
      setTools(toolsData);
      setKnowledgeBases(kbData);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const openCreateForm = () => {
    setEditingAgent(null);
    setFormData({
      ...INITIAL_FORM,
      tools: ['calculator', 'datetime'], // 默认工具
    });
    setFormErrors({});
    setShowCreateForm(true);
  };

  const openEditForm = (agent: AgentAPI) => {
    setEditingAgent(agent);
    setFormData({
      name: agent.name,
      display_name: agent.display_name || '',
      description: agent.description || '',
      agent_type: agent.agent_type,
      system_prompt: agent.system_prompt || '',
      tools: agent.tools || [],
      knowledge_base_ids: agent.knowledge_base_ids || [],
      llm_model_id: agent.llm_model_id || undefined,
      config: agent.config || { temperature: 0.7, max_steps: 10 },
      is_active: agent.is_active,
    });
    setFormErrors({});
    setShowCreateForm(true);
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.name.trim()) {
      errors.name = '名称不能为空';
    }
    if (!formData.display_name.trim()) {
      errors.display_name = '显示名称不能为空';
    }
    if (formData.tools.length === 0) {
      errors.tools = '请至少选择一个工具';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);
    setError(null);
    try {
      if (editingAgent) {
        await agentService.updateAgent(editingAgent.id, formData);
        alert('Agent 更新成功');
      } else {
        await agentService.createAgent(formData);
        alert('Agent 创建成功');
      }
      setShowCreateForm(false);
      loadData();
    } catch (err: any) {
      setError(err.message || '操作失败');
      alert('操作失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAgent = async (agent: AgentAPI) => {
    if (!confirm(`确定要删除 Agent "${agent.display_name || agent.name}" 吗？`)) return;

    setLoading(true);
    try {
      await agentService.deleteAgent(agent.id);
      loadData();
    } catch (err: any) {
      alert('删除 Agent 失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleAgentActive = async (agent: AgentAPI) => {
    setLoading(true);
    try {
      await agentService.updateAgent(agent.id, {
        is_active: !agent.is_active
      });
      loadData();
    } catch (err: any) {
      alert('更新状态失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Robot size={28} />
          数字员工管理
        </h1>
        <button
          onClick={openCreateForm}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={18} />
          创建 Agent
        </button>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* 创建/编辑表单 */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between rounded-t-xl">
              <h2 className="text-xl font-bold">
                {editingAgent ? '编辑 Agent' : '创建 Agent'}
              </h2>
              <button
                onClick={() => setShowCreateForm(false)}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-6 space-y-4">
              {/* 基本信息 */}
              <div className="space-y-3">
                <h3 className="font-semibold text-gray-900">基本信息</h3>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    名称 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                      formErrors.name ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="英文名称，如: calculator_assistant"
                  />
                  {formErrors.name && (
                    <p className="text-red-500 text-xs mt-1">{formErrors.name}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    显示名称 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.display_name}
                    onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                      formErrors.display_name ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="中文名称，如: 计算助手"
                  />
                  {formErrors.display_name && (
                    <p className="text-red-500 text-xs mt-1">{formErrors.display_name}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    描述
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="描述这个 Agent 的功能"
                    rows={2}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    系统提示词
                  </label>
                  <textarea
                    value={formData.system_prompt}
                    onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="定义 Agent 的行为和角色"
                    rows={3}
                  />
                </div>
              </div>

              {/* 工具选择 */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">
                  工具选择 <span className="text-red-500">*</span>
                </h3>
                {formErrors.tools && (
                  <p className="text-red-500 text-xs mb-2">{formErrors.tools}</p>
                )}
                <ToolSelector
                  availableTools={tools}
                  selectedTools={formData.tools}
                  onSelectionChange={(tools) => setFormData({ ...formData, tools })}
                  disabled={loading}
                />
              </div>

              {/* 知识库选择 */}
              {knowledgeBases.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">关联知识库</h3>
                  <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                    {knowledgeBases.map((kb) => (
                      <label
                        key={kb.id}
                        className={`flex items-center gap-2 px-3 py-2 border rounded-lg cursor-pointer hover:bg-gray-50 ${
                          formData.knowledge_base_ids?.includes(kb.id)
                            ? 'bg-blue-50 border-blue-300'
                            : 'border-gray-200'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={formData.knowledge_base_ids?.includes(kb.id) || false}
                          onChange={(e) => {
                            const kbs = formData.knowledge_base_ids || [];
                            if (e.target.checked) {
                              setFormData({ ...formData, knowledge_base_ids: [...kbs, kb.id] });
                            } else {
                              setFormData({
                                ...formData,
                                knowledge_base_ids: kbs.filter((id) => id !== kb.id)
                              });
                            }
                          }}
                          className="rounded"
                        />
                        <span className="text-sm">{kb.name}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* 配置 */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">配置</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      温度
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="1"
                      step="0.1"
                      value={formData.config.temperature}
                      onChange={(e) => setFormData({
                        ...formData,
                        config: { ...formData.config, temperature: parseFloat(e.target.value) }
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      最大步数
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="50"
                      value={formData.config.max_steps}
                      onChange={(e) => setFormData({
                        ...formData,
                        config: { ...formData.config, max_steps: parseInt(e.target.value) }
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      超时（秒）
                    </label>
                    <input
                      type="number"
                      min="10"
                      max="600"
                      value={formData.config.timeout || 300}
                      onChange={(e) => setFormData({
                        ...formData,
                        config: { ...formData.config, timeout: parseInt(e.target.value) }
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="sticky bottom-0 bg-white border-t px-6 py-4 flex gap-3 rounded-b-xl">
              <button
                onClick={() => setShowCreateForm(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                disabled={loading}
              >
                取消
              </button>
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {loading ? '保存中...' : (
                  <>
                    <Save size={16} />
                    {editingAgent ? '更新' : '创建'}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Agent 列表 */}
      {loading ? (
        <div className="text-center py-8 text-gray-500">加载中...</div>
      ) : agents.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Robot size={48} className="mx-auto mb-4 text-gray-300" />
          <p className="text-lg mb-2">暂无 Agent</p>
          <button
            onClick={openCreateForm}
            className="text-blue-600 underline hover:text-blue-700"
          >
            创建第一个 Agent →
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    agent.is_active ? 'bg-blue-600' : 'bg-gray-400'
                  }`}>
                    <Robot size={20} className="text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {agent.display_name || agent.name}
                    </h3>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {agent.name}
                    </div>
                  </div>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => openEditForm(agent)}
                    className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-600"
                    title="编辑"
                  >
                    <Edit size={16} />
                  </button>
                  <button
                    onClick={() => handleDeleteAgent(agent)}
                    className="p-1.5 hover:bg-red-100 rounded-lg text-red-600"
                    title="删除"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>

              {agent.description && (
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">{agent.description}</p>
              )}

              <div className="space-y-2 text-sm">
                {/* 工具标签 */}
                {agent.tools && agent.tools.length > 0 && (
                  <div>
                    <span className="text-gray-500">工具:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {agent.tools.map((tool) => {
                        const toolDef = tools.find((t) => t.name === tool);
                        return (
                          <span
                            key={tool}
                            className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-medium"
                          >
                            {toolDef?.display_name || tool}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* 知识库标签 */}
                {agent.knowledge_base_ids && agent.knowledge_base_ids.length > 0 && (
                  <div>
                    <span className="text-gray-500">知识库:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {agent.knowledge_base_ids.map((kbId) => {
                        const kb = knowledgeBases.find((k) => k.id === kbId);
                        return kb ? (
                          <span
                            key={kbId}
                            className="px-2 py-0.5 bg-green-100 text-green-800 rounded text-xs font-medium"
                          >
                            {kb.name}
                          </span>
                        ) : null;
                      })}
                    </div>
                  </div>
                )}

                {/* 状态 */}
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">状态:</span>
                  <button
                    onClick={() => toggleAgentActive(agent)}
                    className={`px-2 py-0.5 rounded-full text-xs font-medium transition-colors ${
                      agent.is_active
                        ? 'bg-green-100 text-green-700 hover:bg-green-200'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {agent.is_active ? '激活' : '未激活'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
