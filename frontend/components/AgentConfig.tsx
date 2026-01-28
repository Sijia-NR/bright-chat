/**
 * Agent 配置面板
 * Agent Configuration Panel
 *
 * 用于管理员创建和配置数字员工
 * For admins to create and configure digital employees
 */
import { useState, useEffect } from 'react';
import { Robot, Plus, Trash2, Edit } from 'lucide-react';
import { agentService } from '../services/agentService';
import { knowledgeService } from '../services/knowledgeService';
import { AgentAPI, AgentTool, KnowledgeBaseAPI } from '../types';

interface AgentConfigProps {
  onClose?: () => void;
}

export function AgentConfig({ onClose }: AgentConfigProps) {
  const [agents, setAgents] = useState<AgentAPI[]>([]);
  const [tools, setTools] = useState<AgentTool[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseAPI[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
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

  // 创建 Agent（简化版本）
  const handleCreateAgent = async () => {
    const name = prompt('请输入 Agent 名称:');
    if (!name) return;

    const displayName = prompt('请输入显示名称（可选）:') || name;
    const description = prompt('请输入描述（可选）:') || '';

    try {
      await agentService.createAgent({
        name,
        display_name: displayName,
        description,
        agent_type: 'tool',
        tools: ['calculator', 'datetime'], // 默认工具
        config: {
          temperature: 0.7,
          max_steps: 10,
        },
      });
      loadData();
    } catch (err: any) {
      alert('创建 Agent 失败: ' + err.message);
    }
  };

  // 删除 Agent
  const handleDeleteAgent = async (agent: AgentAPI) => {
    if (!confirm(`确定要删除 Agent "${agent.display_name || agent.name}" 吗？`)) return;

    try {
      await agentService.deleteAgent(agent.id);
      loadData();
    } catch (err: any) {
      alert('删除 Agent 失败: ' + err.message);
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
          onClick={handleCreateAgent}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus size={18} />
          创建 Agent
        </button>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-500">加载中...</div>
      ) : agents.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          暂无 Agent
          <br />
          <button onClick={handleCreateAgent} className="text-blue-600 underline">
            创建第一个 Agent
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Robot size={24} className="text-blue-600" />
                  <h3 className="font-semibold">{agent.display_name || agent.name}</h3>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => handleDeleteAgent(agent)}
                    className="p-1 hover:bg-red-100 text-red-600 rounded"
                    title="删除"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>

              {agent.description && (
                <p className="text-sm text-gray-600 mb-3">{agent.description}</p>
              )}

              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">类型:</span>
                  <span className="font-medium">{agent.agent_type}</span>
                </div>

                {agent.tools && agent.tools.length > 0 && (
                  <div>
                    <span className="text-gray-500">工具:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {agent.tools.map((tool) => {
                        const toolDef = tools.find((t) => t.name === tool);
                        return (
                          <span
                            key={tool}
                            className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs"
                          >
                            {toolDef?.display_name || tool}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                )}

                {agent.knowledge_base_ids && agent.knowledge_base_ids.length > 0 && (
                  <div>
                    <span className="text-gray-500">知识库:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {agent.knowledge_base_ids.map((kbId) => {
                        const kb = knowledgeBases.find((k) => k.id === kbId);
                        return kb ? (
                          <span
                            key={kbId}
                            className="px-2 py-0.5 bg-green-100 text-green-800 rounded text-xs"
                          >
                            {kb.name}
                          </span>
                        ) : null;
                      })}
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <span className="text-gray-500">状态:</span>
                  <span
                    className={`font-medium ${
                      agent.is_active ? 'text-green-600' : 'text-gray-400'
                    }`}
                  >
                    {agent.is_active ? '激活' : '未激活'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 可用工具列表（管理员参考） */}
      <div className="mt-8 border-t pt-4">
        <h2 className="text-lg font-semibold mb-3">可用工具列表</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {tools.map((tool) => (
            <div key={tool.name} className="bg-gray-50 p-3 rounded text-sm">
              <div className="font-medium">{tool.display_name}</div>
              <div className="text-gray-600">{tool.description}</div>
              <div className="text-xs text-gray-500 mt-1">分类: {tool.category}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
