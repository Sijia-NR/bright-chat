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

    // ✅ 修复：后端直接返回数组，而不是 { groups: [...] }
    return data.map((g: KnowledgeGroupResponse) => ({
      id: g.id,
      userId: g.user_id,
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

  async getKnowledgeBases(groupId?: string): Promise<KnowledgeBase[]> {
    if (CONFIG.USE_MOCK) {
      return MOCK_BASES.filter((kb: KnowledgeBase) => !groupId || kb.groupId === groupId);
    }

    const params = groupId ? `?group_id=${groupId}` : '';
    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/bases${params}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    });

    if (!resp.ok) throw new Error('获取知识库列表失败');
    const data = await resp.json();

    // ✅ 修复：后端直接返回数组，而不是 { bases: [...] }
    return data.map((b: KnowledgeBaseResponse) => ({
      id: b.id,
      groupId: b.group_id || null,  // 允许为空
      name: b.name,
      description: b.description || undefined,
      type: 'file' as const,  // 默认类型
      size: undefined,
      url: undefined,
      createdAt: new Date(b.created_at).getTime(),
      updatedAt: b.updated_at ? new Date(b.updated_at).getTime() : undefined,
      embeddingModel: b.embedding_model,
      chunkSize: b.chunk_size,
      chunkOverlap: b.chunk_overlap
    }));
  },

  transformGroupResponse(resp: KnowledgeGroupResponse): KnowledgeGroup {
    return {
      id: resp.id,
      userId: resp.user_id,  // 使用后端返回的 user_id
      name: resp.name,
      description: resp.description || undefined,
      order: resp.order,
      createdAt: new Date(resp.created_at).getTime(),
      updatedAt: new Date(resp.updated_at).getTime()
    };
  },

  // ==================== 知识库相关方法 ====================

  async getKnowledgeBase(baseId: string): Promise<any> {
    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/bases/${baseId}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    });

    if (!resp.ok) throw new Error('获取知识库详情失败');
    return resp.json();
  },

  async createKnowledgeBase(data: {
    name: string;
    description?: string;
    user_id: string;
  }): Promise<KnowledgeBase> {
    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/bases`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({
        // ✅ 不传 group_id，让后端自动处理或设为 NULL
        name: data.name,
        description: data.description
      })
    });

    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail || '创建知识库失败');
    }

    const result = await resp.json();
    return {
      id: result.id,
      groupId: result.group_id || undefined,
      name: result.name,
      description: result.description,
      type: 'file',
      createdAt: new Date(result.created_at).getTime(),
      updatedAt: new Date(result.updated_at).getTime()
    };
  },

  // ==================== 文档相关方法 ====================

  async getDocuments(kbId: string): Promise<any[]> {
    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/bases/${kbId}/documents`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    });

    if (!resp.ok) throw new Error('获取文档列表失败');
    const data = await resp.json();
    return data;
  },

  async getDocumentChunks(docId: string, kbId: string, offset: number = 0, limit?: number): Promise<any> {
    const params = new URLSearchParams({ offset: offset.toString() });
    if (limit !== undefined) params.append('limit', limit.toString());

    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/bases/${kbId}/documents/${docId}/chunks?${params}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    });

    if (!resp.ok) throw new Error('获取文档切片失败');
    return resp.json();
  },

  async uploadDocument(kbId: string, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/bases/${kbId}/documents`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` },
      body: formData
    });

    if (!resp.ok) throw new Error('文档上传失败');
    return resp.json();
  },

  async deleteDocument(kbId: string, docId: string): Promise<void> {
    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/bases/${kbId}/documents/${docId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    });

    if (!resp.ok) throw new Error('删除文档失败');
  },

  async deleteKnowledgeBase(kbId: string): Promise<void> {
    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/bases/${kbId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    });

    if (!resp.ok) throw new Error('删除知识库失败');
  }
};
