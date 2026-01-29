import { CONFIG } from '../config';
import { KnowledgeBase, KnowledgeBaseResponse } from '../types';

// Mock 数据
const MOCK_BASES: KnowledgeBase[] = [
  {
    id: 'kb-1',
    name: '产品文档',
    description: '产品使用说明文档',
    type: 'file',
    size: 1024000,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    documentCount: 5
  },
  {
    id: 'kb-2',
    name: 'API 规范',
    description: '后端 API 接口文档',
    type: 'url',
    url: 'https://api.example.com/docs',
    createdAt: Date.now(),
    updatedAt: Date.now(),
    documentCount: 12
  }
];

export const knowledgeService = {
  // ==================== 知识库相关方法 ====================

  async getKnowledgeBases(): Promise<KnowledgeBase[]> {
    if (CONFIG.USE_MOCK) return MOCK_BASES;

    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/bases`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    });

    if (!resp.ok) throw new Error('获取知识库列表失败');
    const data = await resp.json();

    // 后端直接返回数组
    return data.map((b: KnowledgeBaseResponse) => ({
      id: b.id,
      name: b.name,
      description: b.description || undefined,
      type: 'file' as const,
      size: undefined,
      url: undefined,
      createdAt: new Date(b.created_at).getTime(),
      updatedAt: b.updated_at ? new Date(b.updated_at).getTime() : undefined,
      embeddingModel: b.embedding_model,
      chunkSize: b.chunk_size,
      chunkOverlap: b.chunk_overlap,
      documentCount: b.document_count
    }));
  },

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
    user_id?: string;
  }): Promise<KnowledgeBase> {
    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/bases`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({
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
      name: result.name,
      description: result.description,
      type: 'file',
      createdAt: new Date(result.created_at).getTime(),
      updatedAt: new Date(result.updated_at).getTime()
    };
  },

  async deleteKnowledgeBase(kbId: string): Promise<void> {
    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/bases/${kbId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    });

    if (!resp.ok) throw new Error('删除知识库失败');
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

    const url = `${CONFIG.API_BASE_URL}/knowledge/bases/${kbId}/documents/${docId}/chunks?${params}`;
    console.log('🌐 请求 URL:', url);

    const resp = await fetch(url, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    });

    console.log('🌐 响应状态:', resp.status);
    console.log('🌐 响应 OK:', resp.ok);

    if (!resp.ok) {
      const errorText = await resp.text();
      console.error('❌ API 错误响应:', errorText);
      throw new Error('获取文档切片失败');
    }

    const data = await resp.json();
    console.log('📦 API 返回数据:', data);
    console.log('📦 数据类型:', typeof data);
    console.log('📦 是否为数组:', Array.isArray(data));

    return data;
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

  // ==================== 知识库检索相关方法 ====================

  async search(query: string, knowledgeBaseIds?: string[], topK: number = 5): Promise<{
    query: string;
    results: Array<{
      content: string;
      metadata: {
        document_id: string;
        knowledge_base_id: string;
        user_id: string;
        chunk_index: number;
        filename: string;
        file_type: string;
      };
      score: number;
    }>;
  }> {
    const params = new URLSearchParams({ query, top_k: topK.toString() });
    if (knowledgeBaseIds && knowledgeBaseIds.length > 0) {
      params.append('knowledge_base_ids', knowledgeBaseIds.join(','));
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}/knowledge/search?${params}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    });

    if (!resp.ok) throw new Error('知识库搜索失败');
    return resp.json();
  }
};
