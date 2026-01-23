import { CONFIG } from '../config';
import { KnowledgeGroup, KnowledgeBase, KnowledgeGroupResponse, KnowledgeBaseResponse } from '../types';

// Mock 数据
const MOCK_GROUPS: KnowledgeGroup[] = [
  {
    id: 'group-default',
    userId: 'mock-user-id',
    name: '默认组',
    description: '默认知识库分组',
    order: 1,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    knowledgeBaseCount: 2
  }
];

const MOCK_BASES: KnowledgeBase[] = [
  {
    id: 'kb-1',
    groupId: 'group-default',
    name: '产品文档.pdf',
    description: '产品使用说明文档',
    type: 'file',
    size: 1024000,
    createdAt: Date.now(),
    updatedAt: Date.now()
  },
  {
    id: 'kb-2',
    groupId: 'group-default',
    name: 'API 规范',
    description: '后端 API 接口文档',
    type: 'url',
    url: 'https://api.example.com/docs',
    createdAt: Date.now(),
    updatedAt: Date.now()
  }
];

export const knowledgeService = {
  async getGroups(userId: string): Promise<KnowledgeGroup[]> {
    if (CONFIG.USE_MOCK) return MOCK_GROUPS;

    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/groups?user_id=${userId}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    });

    if (!resp.ok) throw new Error('获取知识库分组失败');
    const data = await resp.json();

    return data.groups.map((g: KnowledgeGroupResponse) => ({
      id: g.id,
      userId: '',  // 后端暂未返回，需填充
      name: g.name,
      description: g.description || undefined,
      order: g.order,
      createdAt: new Date(g.created_at).getTime(),
      updatedAt: new Date(g.updated_at).getTime()
    }));
  },

  async createGroup(userId: string, name: string, description?: string): Promise<KnowledgeGroup> {
    if (CONFIG.USE_MOCK) {
      const newGroup: KnowledgeGroup = {
        id: `group-${Date.now()}`,
        userId,
        name,
        description,
        order: MOCK_GROUPS.length + 1,
        createdAt: Date.now(),
        updatedAt: Date.now()
      };
      MOCK_GROUPS.push(newGroup);
      return newGroup;
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/groups`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({ user_id: userId, name, description })
    });

    if (!resp.ok) throw new Error('创建分组失败');
    return this.transformGroupResponse(await resp.json());
  },

  async updateGroup(id: string, name: string, description?: string): Promise<KnowledgeGroup> {
    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/groups/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({ name, description })
    });

    if (!resp.ok) throw new Error('更新分组失败');
    return this.transformGroupResponse(await resp.json());
  },

  async deleteGroup(id: string): Promise<void> {
    if (CONFIG.USE_MOCK) {
      const idx = MOCK_GROUPS.findIndex((g: KnowledgeGroup) => g.id === id);
      if (idx > -1) MOCK_GROUPS.splice(idx, 1);
      return;
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/groups/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    });

    if (!resp.ok) throw new Error('删除分组失败');
  },

  async getKnowledgeBases(groupId: string): Promise<KnowledgeBase[]> {
    if (CONFIG.USE_MOCK) {
      return MOCK_BASES.filter((kb: KnowledgeBase) => kb.groupId === groupId);
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/groups/${groupId}/bases`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    });

    if (!resp.ok) throw new Error('获取知识库列表失败');
    const data = await resp.json();

    return data.bases.map((b: KnowledgeBaseResponse) => ({
      id: b.id,
      groupId: b.group_id,
      name: b.name,
      description: b.description || undefined,
      type: b.type as 'file' | 'url' | 'text',
      size: b.size || undefined,
      url: b.url || undefined,
      createdAt: new Date(b.created_at).getTime(),
      updatedAt: new Date(b.updated_at).getTime()
    }));
  },

  transformGroupResponse(resp: KnowledgeGroupResponse): KnowledgeGroup {
    return {
      id: resp.id,
      userId: '',
      name: resp.name,
      description: resp.description || undefined,
      order: resp.order,
      createdAt: new Date(resp.created_at).getTime(),
      updatedAt: new Date(resp.updated_at).getTime()
    };
  }
};
