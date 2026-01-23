import { CONFIG } from '../config';
import { Agent, AgentType, AgentResponse } from '../types';

// Mock 数据
const MOCK_AGENTS: Agent[] = [
  {
    id: 'agent-1',
    name: 'team_leader',
    displayName: '数字组长',
    description: '负责协调和分配任务',
    type: AgentType.TEAM_LEADER,
    icon: 'Crown',
    isActive: true,
    createdAt: Date.now(),
    order: 1
  },
  {
    id: 'agent-2',
    name: 'data_analyst',
    displayName: '问数员工',
    description: '擅长数据分析和可视化',
    type: AgentType.DATA_ANALYST,
    icon: 'BarChart3',
    isActive: true,
    createdAt: Date.now(),
    order: 2
  },
  {
    id: 'agent-3',
    name: 'writing_assistant',
    displayName: '写作助手',
    description: '帮助撰写各类文档',
    type: AgentType.WRITING_ASSISTANT,
    icon: 'PenTool',
    isActive: true,
    createdAt: Date.now(),
    order: 3
  }
];

export const agentService = {
  async getAgents(): Promise<Agent[]> {
    if (CONFIG.USE_MOCK) return MOCK_AGENTS;

    const resp = await fetch(`${CONFIG.API_BASE_URL}/agents`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    });

    if (!resp.ok) throw new Error('获取 Agent 列表失败');
    const data = await resp.json();

    return data.agents.map((agent: AgentResponse) => ({
      id: agent.id,
      name: agent.name,
      displayName: agent.display_name,
      description: agent.description,
      type: agent.type as AgentType,
      icon: agent.icon || undefined,
      systemPrompt: agent.system_prompt || undefined,
      isActive: agent.is_active,
      createdAt: new Date(agent.created_at).getTime(),
      order: agent.order
    }));
  },

  async getAgentById(id: string): Promise<Agent | null> {
    const agents = await this.getAgents();
    return agents.find((a: Agent) => a.id === id) || null;
  }
};
