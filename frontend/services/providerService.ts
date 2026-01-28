import { CONFIG } from '../config';
import {
  LLMProvider,
  LLMProviderCreate,
  LLMProviderUpdate,
  LLMProviderListResponse,
  ProviderModelSyncResponse,
} from '../types';

class ProviderService {
  private getAuthHeaders() {
    const token = localStorage.getItem('auth_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }

  async listProviders(): Promise<LLMProvider[]> {
    const resp = await fetch(`${CONFIG.API_BASE_URL}/admin/providers`, {
      headers: this.getAuthHeaders()
    });
    if (!resp.ok) throw new Error('Failed to list providers');
    const data: LLMProviderListResponse = await resp.json();
    return data.providers;
  }

  async getProvider(id: string): Promise<LLMProvider> {
    const resp = await fetch(`${CONFIG.API_BASE_URL}/admin/providers/${id}`, {
      headers: this.getAuthHeaders()
    });
    if (!resp.ok) throw new Error('Failed to get provider');
    return await resp.json();
  }

  async createProvider(data: LLMProviderCreate): Promise<LLMProvider> {
    const resp = await fetch(`${CONFIG.API_BASE_URL}/admin/providers`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data)
    });
    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail || 'Failed to create provider');
    }
    return await resp.json();
  }

  async updateProvider(id: string, data: LLMProviderUpdate): Promise<LLMProvider> {
    const resp = await fetch(`${CONFIG.API_BASE_URL}/admin/providers/${id}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data)
    });
    if (!resp.ok) throw new Error('Failed to update provider');
    return await resp.json();
  }

  async deleteProvider(id: string): Promise<void> {
    const resp = await fetch(`${CONFIG.API_BASE_URL}/admin/providers/${id}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });
    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail || 'Failed to delete provider');
    }
  }

  async syncModels(providerId: string, request: { api_key?: string }): Promise<ProviderModelSyncResponse> {
    const resp = await fetch(`${CONFIG.API_BASE_URL}/admin/providers/${providerId}/sync-models`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request)
    });
    if (!resp.ok) {
      const error = await resp.json();
      throw new Error(error.detail || 'Failed to sync models');
    }
    return await resp.json();
  }
}

export const providerService = new ProviderService();
