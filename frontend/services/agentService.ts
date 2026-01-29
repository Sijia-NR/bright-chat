import { CONFIG } from '../config';
import { Agent, AgentType, AgentResponse, AgentAPI } from '../types';

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

// 获取认证头
const getAuthHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
  'Content-Type': 'application/json'
});

// Agent 事件类型
export interface AgentStreamEvent {
  type: 'stream' | 'complete' | 'error';
  content?: string;
  output?: string;
  error?: string;
}

// Agent 聊天请求
export interface AgentChatRequest {
  query: string;  // 关键：使用 query 字段，不是 message
  session_id?: string;
  stream?: boolean;
  [key: string]: any;
}

// Agent 创建请求
export interface CreateAgentRequest {
  name: string;
  display_name: string;
  description: string;
  type: string;
  icon?: string;
  system_prompt?: string;
  is_active?: boolean;
  order?: number;
  llm_model_id?: string;
}

// Agent 更新请求
export interface UpdateAgentRequest {
  name?: string;
  display_name?: string;
  description?: string;
  type?: string;
  icon?: string;
  system_prompt?: string;
  is_active?: boolean;
  order?: number;
  llm_model_id?: string;
}

export const agentService = {
  /**
   * 创建新的 Agent
   */
  async createAgent(data: CreateAgentRequest): Promise<Agent> {
    if (CONFIG.USE_MOCK) {
      const newAgent: Agent = {
        id: `agent-${Date.now()}`,
        name: data.name,
        displayName: data.display_name,
        description: data.description,
        type: data.type as AgentType,
        icon: data.icon,
        isActive: data.is_active ?? true,
        createdAt: Date.now(),
        order: data.order ?? MOCK_AGENTS.length + 1
      };
      return newAgent;
    }

    const response = await fetch(`${CONFIG.API_BASE_URL}/agents/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '创建 Agent 失败');
    }

    const result = await response.json();
    return {
      id: result.id,
      name: result.name,
      displayName: result.display_name,
      description: result.description,
      type: result.agent_type as AgentType,  // 修复：使用 agent_type
      icon: result.icon || undefined,
      systemPrompt: result.system_prompt || undefined,
      isActive: result.is_active,
      createdAt: new Date(result.created_at).getTime(),
      order: result.order
    };
  },

  /**
   * 获取 Agent 列表
   */
  async getAgents(): Promise<AgentAPI[]> {
    if (CONFIG.USE_MOCK) return MOCK_AGENTS;

    const response = await fetch(`${CONFIG.API_BASE_URL}/agents/`, {
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '获取 Agent 列表失败');
    }

    const data = await response.json();
    return data.agents.map((agent: any) => ({
      id: agent.id,
      name: agent.name,
      display_name: agent.display_name,
      description: agent.description,
      agent_type: agent.agent_type,
      system_prompt: agent.system_prompt,
      knowledge_base_ids: agent.knowledge_base_ids || [],
      tools: agent.tools || [],
      config: agent.config || {},
      llm_model_id: agent.llm_model_id,
      llm_model_name: agent.llm_model_name || null,
      is_active: agent.is_active,  // 保持蛇形命名，匹配 AgentAPI 类型
      created_by: agent.created_by,
      created_at: agent.created_at,
      updated_at: agent.updated_at
    }));
  },

  /**
   * 获取单个 Agent 详情
   */
  async getAgent(agentId: string): Promise<Agent> {
    if (CONFIG.USE_MOCK) {
      const agent = MOCK_AGENTS.find(a => a.id === agentId);
      if (!agent) throw new Error('Agent 不存在');
      return agent;
    }

    const response = await fetch(`${CONFIG.API_BASE_URL}/agents/${agentId}`, {
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '获取 Agent 详情失败');
    }

    const result = await response.json();
    return {
      id: result.id,
      name: result.name,
      displayName: result.display_name,
      description: result.description,
      type: result.agent_type as AgentType,  // 修复：使用 agent_type
      icon: result.icon || undefined,
      systemPrompt: result.system_prompt || undefined,
      isActive: result.is_active,
      createdAt: new Date(result.created_at).getTime(),
      order: result.order
    };
  },

  /**
   * 更新 Agent
   */
  async updateAgent(agentId: string, data: UpdateAgentRequest): Promise<Agent> {
    const response = await fetch(`${CONFIG.API_BASE_URL}/agents/${agentId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '更新 Agent 失败');
    }

    const result = await response.json();
    return {
      id: result.id,
      name: result.name,
      displayName: result.display_name,
      description: result.description,
      type: result.agent_type as AgentType,  // 修复：使用 agent_type
      icon: result.icon || undefined,
      systemPrompt: result.system_prompt || undefined,
      isActive: result.is_active,
      createdAt: new Date(result.created_at).getTime(),
      order: result.order
    };
  },

  /**
   * 删除 Agent
   */
  async deleteAgent(agentId: string): Promise<void> {
    const response = await fetch(`${CONFIG.API_BASE_URL}/agents/${agentId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '删除 Agent 失败');
    }
  },

  /**
   * Agent 聊天（流式响应）
   * 关键方法：使用 query 字段，不是 message
   */
  async agentChat(agentId: string, request: AgentChatRequest): Promise<AsyncIterable<AgentStreamEvent>> {
    console.log('[Agent Chat] 开始对话:', { agentId, request });

    const response = await fetch(`${CONFIG.API_BASE_URL}/agents/${agentId}/chat`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Agent 聊天请求失败');
    }

    // 返回异步迭代器用于处理 SSE 流
    return this.createStreamIterator(response);
  },

  /**
   * 创建 SSE 流迭代器
   */
  async *createStreamIterator(response: Response): AsyncIterable<AgentStreamEvent> {
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('响应体为空');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith(':')) continue;

          if (trimmed.startsWith('data:')) {
            const data = trimmed.slice(5).trim();
            if (data === '[DONE]') continue;

            try {
              const event = JSON.parse(data);
              yield event;
            } catch (e) {
              console.warn('[Agent Chat] 解析事件失败:', data, e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },

  /**
   * 获取 Agent 执行历史
   */
  async getAgentExecutions(agentId: string, limit: number = 10): Promise<any[]> {
    const response = await fetch(`${CONFIG.API_BASE_URL}/agents/${agentId}/executions/?limit=${limit}`, {
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '获取执行历史失败');
    }

    const data = await response.json();
    return data.executions || [];
  },

  /**
   * 获取可用工具列表
   */
  async getAvailableTools(): Promise<any[]> {
    const response = await fetch(`${CONFIG.API_BASE_URL}/agents/tools/`, {
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '获取工具列表失败');
    }

    const data = await response.json();
    return data.tools || [];
  },

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
  },

  /**
   * Agent Service 健康检查
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    const response = await fetch(`${CONFIG.API_BASE_URL}/agents/service-health/`);

    if (!response.ok) {
      throw new Error('Agent Service 不健康');
    }

    return await response.json();
  },

  /**
   * 兼容旧方法：通过 ID 获取 Agent
   */
  async getAgentById(id: string): Promise<Agent | null> {
    try {
      return await this.getAgent(id);
    } catch (e) {
      console.error('获取 Agent 失败:', e);
      return null;
    }
  }
};
