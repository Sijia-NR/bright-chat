
import { CONFIG } from '../config';
import { ChatSession, Message } from '../types';

const SESSION_KEY = 'mock_sessions';
const MESSAGE_PREFIX = 'mock_msg_';

const getMockSessions = (): ChatSession[] => {
  const stored = localStorage.getItem(SESSION_KEY);
  if (stored) return JSON.parse(stored);
  return [
    { id: '1', title: '关于 IAS 规范的咨询', lastUpdated: Date.now(), userId: 'mock-admin-id' },
    { id: '2', title: '如何实现前端三层架构', lastUpdated: Date.now() - 100000, userId: 'mock-admin-id' }
  ];
};

const saveMockSessions = (sessions: ChatSession[]) => {
  localStorage.setItem(SESSION_KEY, JSON.stringify(sessions));
};

export const sessionService = {
  async getSessions(userId: string): Promise<ChatSession[]> {
    if (CONFIG.USE_MOCK) return getMockSessions();
    const resp = await fetch(`${CONFIG.API_BASE_URL}/sessions?user_id=${userId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });
    if (!resp.ok) throw new Error('获取会话列表失败');
    return resp.json();
  },

  async createSession(title: string, userId: string, agentId?: string): Promise<ChatSession> {
    const newSession: ChatSession = {
      id: `s-${Date.now()}`,
      title: title.slice(0, 20) + (title.length > 20 ? '...' : ''),
      lastUpdated: Date.now(),
      userId,
      agentId  // 新增
    };
    if (CONFIG.USE_MOCK) {
      const sessions = getMockSessions();
      saveMockSessions([newSession, ...sessions]);
      return newSession;
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({
        title,
        user_id: userId,
        agent_id: agentId  // 新增
      })
    });
    if (!resp.ok) throw new Error('创建会话失败');
    const data = await resp.json();
    return {
      id: data.id,
      title: data.title,
      lastUpdated: new Date(data.last_updated).getTime(),
      userId: data.user_id,
      agentId: data.agent_id  // 新增
    };
  },

  async getMessages(sessionId: string): Promise<Message[]> {
    if (CONFIG.USE_MOCK) {
      const stored = localStorage.getItem(MESSAGE_PREFIX + sessionId);
      if (stored) return JSON.parse(stored);
      return [
        { id: 'm1', role: 'user', content: `这是历史会话内容。`, timestamp: Date.now() - 5000 },
        { id: 'm2', role: 'assistant', content: '欢迎继续咨询。', timestamp: Date.now() - 4000 }
      ];
    }
    const resp = await fetch(`${CONFIG.API_BASE_URL}/sessions/${sessionId}/messages`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });
    if (!resp.ok) throw new Error('获取消息失败');
    const messages = await resp.json();
    // 转换后端时间戳格式为前端需要的格式
    return messages.map((msg: any) => ({
      id: msg.id,
      role: msg.role,
      content: msg.content,
      timestamp: new Date(msg.timestamp).getTime()
    }));
  },

  async saveMessages(sessionId: string, messages: Message[]): Promise<void> {
    if (CONFIG.USE_MOCK) {
      localStorage.setItem(MESSAGE_PREFIX + sessionId, JSON.stringify(messages));
      return;
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}/sessions/${sessionId}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({
        messages: messages.map(msg => ({
          id: msg.id,  // 确保发送ID
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.timestamp).toISOString()
        }))
      })
    });
    if (!resp.ok) throw new Error('保存消息失败');
  },

  async deleteSession(sessionId: string): Promise<void> {
    if (CONFIG.USE_MOCK) {
      const current = getMockSessions();
      saveMockSessions(current.filter(s => s.id !== sessionId));
      localStorage.removeItem(MESSAGE_PREFIX + sessionId);
      return;
    }
    const resp = await fetch(`${CONFIG.API_BASE_URL}/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });
    if (!resp.ok) throw new Error('删除会话失败');
  }
};
