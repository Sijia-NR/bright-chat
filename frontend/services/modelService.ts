
import { CONFIG } from '../config';
import { LLMModel, LLMModelCreate, LLMModelUpdate, LLMModelListResponse } from '../types';

const STORAGE_KEY = 'mock_llm_models';

const getMockModels = (): LLMModel[] => {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) return JSON.parse(stored);
  // 初始没有模型，需要管理员配置
  return [];
};

export const modelService = {
  /**
   * 获取所有启用的模型（所有认证用户可访问）
   */
  async getActiveModels(): Promise<LLMModel[]> {
    if (CONFIG.USE_MOCK) {
      return getMockModels().filter(m => m.is_active);
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}/models/active`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });
    if (!resp.ok) throw new Error('获取模型列表失败');
    const data = await resp.json();
    return data.models || [];
  },

  /**
   * 管理员：列出所有模型
   */
  async listModels(): Promise<LLMModelListResponse> {
    if (CONFIG.USE_MOCK) {
      const models = getMockModels();
      return { models, total: models.length };
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}/admin/models`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });
    if (!resp.ok) throw new Error('获取模型列表失败');
    return resp.json();
  },

  /**
   * 管理员：获取特定模型
   */
  async getModel(modelId: string): Promise<LLMModel> {
    if (CONFIG.USE_MOCK) {
      const models = getMockModels();
      const model = models.find(m => m.id === modelId);
      if (!model) throw new Error('模型不存在');
      return model;
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}/admin/models/${modelId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });
    if (!resp.ok) throw new Error('获取模型失败');
    return resp.json();
  },

  /**
   * 管理员：创建新模型
   */
  async createModel(modelData: LLMModelCreate): Promise<LLMModel> {
    if (CONFIG.USE_MOCK) {
      const models = getMockModels();
      // 检查名称唯一性
      if (models.some(m => m.name === modelData.name)) {
        throw new Error('模型名称已存在');
      }

      const newModel: LLMModel = {
        id: `mock-model-${Date.now()}`,
        name: modelData.name,
        display_name: modelData.display_name,
        model_type: modelData.model_type,
        api_url: modelData.api_url,
        api_version: modelData.api_version,
        description: modelData.description,
        is_active: modelData.is_active ?? true,
        max_tokens: modelData.max_tokens ?? 4096,
        temperature: modelData.temperature ?? 0.7,
        stream_supported: modelData.stream_supported ?? true,
        created_at: new Date().toISOString()
      };

      const updated = [newModel, ...models];
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return newModel;
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}/admin/models`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify(modelData)
    });
    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail || '创建模型失败');
    }
    return resp.json();
  },

  /**
   * 管理员：更新模型
   */
  async updateModel(modelId: string, modelData: LLMModelUpdate): Promise<LLMModel> {
    if (CONFIG.USE_MOCK) {
      const models = getMockModels();
      const index = models.findIndex(m => m.id === modelId);
      if (index === -1) throw new Error('模型不存在');

      models[index] = {
        ...models[index],
        ...(modelData.display_name !== undefined && { display_name: modelData.display_name }),
        ...(modelData.api_url !== undefined && { api_url: modelData.api_url }),
        ...(modelData.api_version !== undefined && { api_version: modelData.api_version }),
        ...(modelData.description !== undefined && { description: modelData.description }),
        ...(modelData.is_active !== undefined && { is_active: modelData.is_active }),
        ...(modelData.max_tokens !== undefined && { max_tokens: modelData.max_tokens }),
        ...(modelData.temperature !== undefined && { temperature: modelData.temperature }),
        ...(modelData.stream_supported !== undefined && { stream_supported: modelData.stream_supported }),
      };

      localStorage.setItem(STORAGE_KEY, JSON.stringify(models));
      return models[index];
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}/admin/models/${modelId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify(modelData)
    });
    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail || '更新模型失败');
    }
    return resp.json();
  },

  /**
   * 管理员：删除模型
   */
  async deleteModel(modelId: string): Promise<{ message: string }> {
    if (CONFIG.USE_MOCK) {
      const models = getMockModels();
      const updated = models.filter(m => m.id !== modelId);
      if (updated.length === models.length) {
        throw new Error('模型不存在');
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return { message: '模型已删除 (MOCK)' };
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}/admin/models/${modelId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });
    if (!resp.ok) throw new Error('删除模型失败');
    return resp.json();
  }
};
