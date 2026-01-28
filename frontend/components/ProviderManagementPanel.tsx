import React, { useState, useEffect } from 'react';
import {
  Server, Plus, RefreshCw, Trash2, Edit2, X, Check, Loader2,
  Cloud, ChevronDown, ChevronUp, Eye, EyeOff, ChevronLeft
} from 'lucide-react';
import { providerService } from '../services/providerService';
import { modelService } from '../services/modelService';
import {
  LLMProvider, LLMProviderCreate, ModelWithProvider,
  ProviderModelSyncResponse
} from '../types';

interface ProviderManagementPanelProps {
  onModelChange?: () => void;
}

type ViewMode = 'providers' | 'models';
type SyncStatus = 'idle' | 'syncing' | 'success' | 'error';

const ProviderManagementPanel: React.FC<ProviderManagementPanelProps> = ({ onModelChange }) => {
  // 提供商管理状态
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('providers');

  // 创建/编辑提供商状态
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingProvider, setEditingProvider] = useState<LLMProvider | null>(null);
  const [formData, setFormData] = useState<LLMProviderCreate>({
    name: '',
    display_name: '',
    base_url: '',
    description: '',
    is_active: true,
    auth_type: 'bearer',
    default_api_key: ''
  });

  // 模型管理状态
  const [models, setModels] = useState<ModelWithProvider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider | null>(null);
  const [selectedModelIds, setSelectedModelIds] = useState<Set<string>>(new Set());
  const [syncStatus, setSyncStatus] = useState<SyncStatus>('idle');
  const [syncMessage, setSyncMessage] = useState('');
  const [listingAction, setListingAction] = useState<'idle' | 'listing' | 'unlisting'>('idle');

  // 消息提示
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  // 删除确认
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

  useEffect(() => {
    loadProviders();
  }, []);

  useEffect(() => {
    if (selectedProvider) {
      loadProviderModels(selectedProvider.id);
    }
  }, [selectedProvider]);

  const loadProviders = async () => {
    setLoading(true);
    try {
      const list = await providerService.listProviders();
      setProviders(list);
    } catch (e) {
      setMessage({ type: 'error', text: '加载提供商列表失败' });
    } finally {
      setLoading(false);
    }
  };

  const loadProviderModels = async (providerId: string) => {
    try {
      const result = await modelService.listAllModels({ provider_id: providerId });
      setModels(result.models);
    } catch (e) {
      console.error('Failed to load models:', e);
    }
  };

  const handleCreateProvider = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      await providerService.createProvider(formData);
      setMessage({ type: 'success', text: '提供商创建成功' });
      setShowCreateForm(false);
      resetForm();
      await loadProviders();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || '创建失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProvider = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProvider) return;
    setLoading(true);
    setMessage(null);
    try {
      const updateData: Partial<LLMProviderCreate> = {};
      if (formData.display_name !== editingProvider.display_name) updateData.display_name = formData.display_name;
      if (formData.base_url !== editingProvider.base_url) updateData.base_url = formData.base_url;
      if (formData.description !== editingProvider.description) updateData.description = formData.description;
      if (formData.is_active !== editingProvider.is_active) updateData.is_active = formData.is_active;
      if (formData.auth_type !== editingProvider.auth_type) updateData.auth_type = formData.auth_type;
      // 只有在输入了新的 API key 时才更新
      if (formData.default_api_key && formData.default_api_key !== '') {
        updateData.default_api_key = formData.default_api_key;
      }

      await providerService.updateProvider(editingProvider.id, updateData);
      setMessage({ type: 'success', text: '提供商更新成功' });
      setEditingProvider(null);
      resetForm();
      await loadProviders();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || '更新失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProvider = async (providerId: string) => {
    setLoading(true);
    try {
      await providerService.deleteProvider(providerId);
      setProviders(prev => prev.filter(p => p.id !== providerId));
      setPendingDeleteId(null);
      setMessage({ type: 'success', text: '提供商删除成功' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || '删除失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleSyncModels = async (providerId: string, apiKey?: string) => {
    setSyncStatus('syncing');
    setSyncMessage('');
    try {
      const result: ProviderModelSyncResponse = await providerService.syncModels(providerId, { api_key: apiKey });
      setSyncStatus('success');
      setSyncMessage(`同步成功：新增 ${result.synced} 个，更新 ${result.updated} 个，失败 ${result.failed} 个`);
      await loadProviderModels(providerId);
      onModelChange?.();
    } catch (err: any) {
      setSyncStatus('error');
      setSyncMessage(err.message || '同步失败');
    }
  };

  const handleBatchList = async () => {
    const ids = Array.from(selectedModelIds);
    if (ids.length === 0) return;

    setListingAction('listing');
    try {
      const result = await modelService.batchListModels(ids);
      setMessage({ type: 'success', text: `成功上架 ${result.updated} 个模型` });
      setSelectedModelIds(new Set());
      await loadProviderModels(selectedProvider!.id);
      onModelChange?.();
    } catch (err: any) {
      setMessage({ type: 'error', text: '批量上架失败' });
    } finally {
      setListingAction('idle');
    }
  };

  const handleBatchUnlist = async () => {
    const ids = Array.from(selectedModelIds);
    if (ids.length === 0) return;

    setListingAction('unlisting');
    try {
      const result = await modelService.batchUnlistModels(ids);
      setMessage({ type: 'success', text: `成功下架 ${result.updated} 个模型` });
      setSelectedModelIds(new Set());
      await loadProviderModels(selectedProvider!.id);
      onModelChange?.();
    } catch (err: any) {
      setMessage({ type: 'error', text: '批量下架失败' });
    } finally {
      setListingAction('idle');
    }
  };

  const handleToggleListing = async (modelId: string, currentStatus: boolean) => {
    try {
      await modelService.updateListingStatus(modelId, !currentStatus);
      setModels(prev => prev.map(m =>
        m.id === modelId ? { ...m, is_listed: !currentStatus } : m
      ));
      onModelChange?.();
    } catch (err) {
      setMessage({ type: 'error', text: '更新状态失败' });
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      display_name: '',
      base_url: '',
      description: '',
      is_active: true,
      auth_type: 'bearer',
      default_api_key: ''
    });
  };

  const startEdit = (provider: LLMProvider) => {
    setEditingProvider(provider);
    setFormData({
      name: provider.name,
      display_name: provider.display_name,
      base_url: provider.base_url,
      description: provider.description || '',
      is_active: provider.is_active,
      auth_type: provider.auth_type,
      default_api_key: '' // 不显示实际的 API key，只在创建时输入
    });
    setShowCreateForm(true);
  };

  const cancelEdit = () => {
    setEditingProvider(null);
    setShowCreateForm(false);
    resetForm();
  };

  // 切换视图
  const switchToModels = (provider: LLMProvider) => {
    setSelectedProvider(provider);
    setViewMode('models');
    setSelectedModelIds(new Set());
    setSyncMessage('');
    setSyncStatus('idle');
  };

  const switchToProviders = () => {
    setViewMode('providers');
    setSelectedProvider(null);
    setModels([]);
    setSelectedModelIds(new Set());
  };

  // 计算上架/未上架数量
  const listedCount = models.filter(m => m.is_listed).length;
  const unlistedCount = models.length - listedCount;

  return (
    <div className="animate-in fade-in duration-500">
      {/* 顶部导航 */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold text-gray-900">
            {viewMode === 'providers' ? '数字员工提供商管理' : `模型列表 - ${selectedProvider?.display_name}`}
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            {viewMode === 'providers'
              ? '配置和管理 LLM 提供商，同步可用模型'
              : `共 ${models.length} 个模型（${listedCount} 已上架，${unlistedCount} 未上架）`}
          </p>
        </div>
        {viewMode === 'models' && (
          <button
            onClick={switchToProviders}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-2xl text-gray-600 hover:text-gray-900 hover:shadow-md transition-all"
          >
            <ChevronLeft size={18} />
            <span className="text-sm font-bold">返回提供商</span>
          </button>
        )}
      </div>

      {message && (
        <div className={`mb-6 p-4 rounded-2xl flex items-center justify-between ${
          message.type === 'success'
            ? 'bg-green-50 text-green-700 border border-green-100'
            : 'bg-red-50 text-red-700 border border-red-100'
        }`}>
          <span className="font-bold text-sm">{message.text}</span>
          <button onClick={() => setMessage(null)}><X size={16} /></button>
        </div>
      )}

      {/* 提供商列表视图 */}
      {viewMode === 'providers' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* 创建表单 */}
          <section className="lg:col-span-4">
            <div className="bg-white rounded-[32px] p-8 border border-gray-100 shadow-sm sticky top-8">
              <div className="flex items-center gap-3 mb-8">
                <div className="p-3 bg-emerald-50 text-emerald-600 rounded-2xl">
                  {editingProvider ? <Edit2 size={24} /> : <Plus size={24} />}
                </div>
                <h2 className="text-lg font-bold text-gray-800">
                  {editingProvider ? '编辑提供商' : '添加提供商'}
                </h2>
              </div>

              <form onSubmit={editingProvider ? handleUpdateProvider : handleCreateProvider} className="space-y-5">
                <div>
                  <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">提供商名称</label>
                  <input
                    type="text" required
                    value={formData.name}
                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                    placeholder="例如: openai-provider"
                    disabled={!!editingProvider}
                    className="w-full px-5 py-3.5 bg-gray-50 border-2 border-transparent rounded-2xl outline-none focus:border-emerald-500 focus:bg-white transition-all text-sm disabled:opacity-50"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">显示名称</label>
                  <input
                    type="text" required
                    value={formData.display_name}
                    onChange={e => setFormData({ ...formData, display_name: e.target.value })}
                    placeholder="例如: OpenAI Provider"
                    className="w-full px-5 py-3.5 bg-gray-50 border-2 border-transparent rounded-2xl outline-none focus:border-emerald-500 focus:bg-white transition-all text-sm"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">API 地址</label>
                  <input
                    type="url" required
                    value={formData.base_url}
                    onChange={e => setFormData({ ...formData, base_url: e.target.value })}
                    placeholder="https://api.openai.com"
                    className="w-full px-5 py-3.5 bg-gray-50 border-2 border-transparent rounded-2xl outline-none focus:border-emerald-500 focus:bg-white transition-all text-sm"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">认证方式</label>
                  <select
                    value={formData.auth_type}
                    onChange={e => setFormData({ ...formData, auth_type: e.target.value })}
                    className="w-full px-5 py-3.5 bg-gray-50 border-2 border-transparent rounded-2xl outline-none focus:border-emerald-500 focus:bg-white transition-all text-sm appearance-none"
                  >
                    <option value="bearer">Bearer Token</option>
                    <option value="api_key">API Key</option>
                    <option value="none">无需认证</option>
                  </select>
                </div>
                {(formData.auth_type === 'bearer' || formData.auth_type === 'api_key') && (
                  <div>
                    <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">默认 API Key</label>
                    <input
                      type="password"
                      value={formData.default_api_key}
                      onChange={e => setFormData({ ...formData, default_api_key: e.target.value })}
                      placeholder="sk-..."
                      className="w-full px-5 py-3.5 bg-gray-50 border-2 border-transparent rounded-2xl outline-none focus:border-emerald-500 focus:bg-white transition-all text-sm"
                    />
                  </div>
                )}
                <div>
                  <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">描述（可选）</label>
                  <textarea
                    value={formData.description}
                    onChange={e => setFormData({ ...formData, description: e.target.value })}
                    placeholder="提供商的简要描述..."
                    rows={3}
                    className="w-full px-5 py-3.5 bg-gray-50 border-2 border-transparent rounded-2xl outline-none focus:border-emerald-500 focus:bg-white transition-all text-sm resize-none"
                  />
                </div>
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={e => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-5 h-5 rounded-lg border-gray-300 text-emerald-600 focus:ring-emerald-500"
                  />
                  <label htmlFor="is_active" className="text-sm font-bold text-gray-700">启用提供商</label>
                </div>

                <div className="flex gap-3">
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 py-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl font-bold shadow-xl shadow-emerald-100 transition-all active:scale-[0.98] disabled:opacity-50"
                  >
                    {loading ? <Loader2 className="animate-spin mx-auto" size={20} /> : (editingProvider ? '保存更改' : '创建提供商')}
                  </button>
                  {editingProvider && (
                    <button
                      type="button"
                      onClick={cancelEdit}
                      className="px-6 py-4 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-2xl font-bold transition-all"
                    >
                      取消
                    </button>
                  )}
                </div>
              </form>
            </div>
          </section>

          {/* 提供商列表 */}
          <section className="lg:col-span-8">
            <div className="bg-white rounded-[32px] p-8 border border-gray-100 shadow-sm min-h-[500px]">
              <div className="flex items-center gap-3 mb-8">
                <div className="p-3 bg-gray-50 text-gray-500 rounded-2xl">
                  <Server size={24} />
                </div>
                <h2 className="text-lg font-bold text-gray-800">提供商列表</h2>
              </div>

              {loading && providers.length === 0 ? (
                <div className="flex items-center justify-center py-20">
                  <Loader2 className="animate-spin text-gray-400" size={40} />
                </div>
              ) : providers.length === 0 ? (
                <div className="text-center py-20">
                  <Cloud className="mx-auto text-gray-300 mb-4" size={48} />
                  <p className="text-gray-500 font-medium">暂无提供商</p>
                  <p className="text-sm text-gray-400 mt-1">添加您的第一个 LLM 提供商</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {providers.map(provider => (
                    <div key={provider.id} className="group p-6 border border-gray-50 rounded-3xl hover:bg-gray-50/50 transition-all">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-bold text-gray-900">{provider.display_name}</h3>
                            <span className={`px-2.5 py-0.5 text-[10px] font-black uppercase rounded-lg ${
                              provider.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-500'
                            }`}>
                              {provider.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                          <p className="text-sm text-gray-500 mb-2 font-mono">{provider.base_url}</p>
                          <div className="flex items-center gap-4 text-xs text-gray-400">
                            <span>{provider.model_count || 0} 个模型</span>
                            {provider.description && <span>•</span>}
                            {provider.description && <span>{provider.description}</span>}
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleSyncModels(provider.id)}
                            disabled={syncStatus === 'syncing'}
                            className="p-2.5 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-xl transition-all disabled:opacity-50"
                            title="同步模型"
                          >
                            <RefreshCw size={18} className={syncStatus === 'syncing' ? 'animate-spin' : ''} />
                          </button>
                          <button
                            onClick={() => switchToModels(provider)}
                            className="px-4 py-2.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-600 rounded-xl text-sm font-bold transition-all"
                          >
                            管理模型
                          </button>
                          <button
                            onClick={() => startEdit(provider)}
                            className="p-2.5 text-gray-300 hover:text-emerald-600 hover:bg-emerald-50 rounded-xl transition-all"
                          >
                            <Edit2 size={18} />
                          </button>
                          {pendingDeleteId === provider.id ? (
                            <div className="flex items-center gap-2 animate-in slide-in-from-right-2">
                              <button
                                onClick={() => setPendingDeleteId(null)}
                                className="text-xs font-bold text-gray-400 hover:text-gray-600"
                              >取消</button>
                              <button
                                onClick={() => handleDeleteProvider(provider.id)}
                                className="px-3 py-1.5 bg-red-600 text-white text-xs font-bold rounded-lg hover:bg-red-700 shadow-lg shadow-red-100"
                              >
                                确认
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => setPendingDeleteId(provider.id)}
                              className="p-2.5 text-gray-300 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all"
                            >
                              <Trash2 size={18} />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        </div>
      )}

      {/* 模型列表视图 */}
      {viewMode === 'models' && selectedProvider && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* 同步控制面板 */}
          <section className="lg:col-span-4">
            <div className="bg-white rounded-[32px] p-8 border border-gray-100 shadow-sm sticky top-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-blue-50 text-blue-600 rounded-2xl">
                  <Cloud size={24} />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-800">模型同步</h2>
                  <p className="text-xs text-gray-500">从提供商同步可用模型</p>
                </div>
              </div>

              {syncStatus === 'success' && (
                <div className="mb-6 p-4 bg-green-50 border border-green-100 rounded-2xl">
                  <div className="flex items-center gap-2 text-green-700 mb-1">
                    <Check size={16} />
                    <span className="font-bold text-sm">同步成功</span>
                  </div>
                  <p className="text-xs text-green-600">{syncMessage}</p>
                </div>
              )}

              {syncStatus === 'error' && (
                <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-2xl">
                  <div className="flex items-center gap-2 text-red-700 mb-1">
                    <X size={16} />
                    <span className="font-bold text-sm">同步失败</span>
                  </div>
                  <p className="text-xs text-red-600">{syncMessage}</p>
                </div>
              )}

              <button
                onClick={() => handleSyncModels(selectedProvider.id)}
                disabled={syncStatus === 'syncing'}
                className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-2xl font-bold shadow-xl shadow-blue-100 transition-all active:scale-[0.98] disabled:opacity-50 mb-4"
              >
                {syncStatus === 'syncing' ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 size={18} className="animate-spin" />
                    同步中...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <RefreshCw size={18} />
                    同步模型
                  </span>
                )}
              </button>

              <div className="space-y-3">
                <h3 className="text-xs font-black text-gray-400 uppercase tracking-widest ml-1">批量操作</h3>
                <button
                  onClick={handleBatchList}
                  disabled={selectedModelIds.size === 0 || listingAction !== 'idle'}
                  className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {listingAction === 'listing' ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 size={16} className="animate-spin" />
                      上架中...
                    </span>
                  ) : (
                    `上架选中 (${selectedModelIds.size})`
                  )}
                </button>
                <button
                  onClick={handleBatchUnlist}
                  disabled={selectedModelIds.size === 0 || listingAction !== 'idle'}
                  className="w-full py-3.5 bg-gray-600 hover:bg-gray-700 text-white rounded-2xl font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {listingAction === 'unlisting' ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 size={16} className="animate-spin" />
                      下架中...
                    </span>
                  ) : (
                    `下架选中 (${selectedModelIds.size})`
                  )}
                </button>
              </div>

              <div className="mt-6 p-4 bg-gray-50 rounded-2xl">
                <h4 className="text-xs font-bold text-gray-600 uppercase tracking-widest mb-2">说明</h4>
                <ul className="space-y-1.5 text-xs text-gray-500">
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-500 mt-0.5">•</span>
                    <span>同步的模型默认处于"未上架"状态</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-500 mt-0.5">•</span>
                    <span>只有上架的模型对前端用户可见</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-500 mt-0.5">•</span>
                    <span>可批量或单个上架/下架模型</span>
                  </li>
                </ul>
              </div>
            </div>
          </section>

          {/* 模型列表 */}
          <section className="lg:col-span-8">
            <div className="bg-white rounded-[32px] p-8 border border-gray-100 shadow-sm min-h-[500px]">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-gray-50 text-gray-500 rounded-2xl">
                    <Server size={24} />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-gray-800">模型列表</h2>
                    <p className="text-xs text-gray-400 mt-0.5">{selectedProvider.display_name}</p>
                  </div>
                </div>
              </div>

              {models.length === 0 ? (
                <div className="text-center py-20">
                  <Cloud className="mx-auto text-gray-300 mb-4" size={48} />
                  <p className="text-gray-500 font-medium">暂无模型</p>
                  <p className="text-sm text-gray-400 mt-1">点击"同步模型"从提供商获取可用模型</p>
                </div>
              ) : (
                <>
                  {/* 全选 */}
                  <div className="mb-4 p-3 bg-gray-50 rounded-2xl flex items-center justify-between">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedModelIds.size === models.length && models.length > 0}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedModelIds(new Set(models.map(m => m.id)));
                          } else {
                            setSelectedModelIds(new Set());
                          }
                        }}
                        className="w-5 h-5 rounded-lg border-gray-300 text-emerald-600 focus:ring-emerald-500"
                      />
                      <span className="text-sm font-bold text-gray-700">全选</span>
                    </label>
                    <span className="text-xs text-gray-400">
                      已选 {selectedModelIds.size} / {models.length}
                    </span>
                  </div>

                  <div className="space-y-3">
                    {models.map(model => (
                      <div
                        key={model.id}
                        className={`p-4 border-2 rounded-2xl transition-all ${
                          selectedModelIds.has(model.id)
                            ? 'border-emerald-500 bg-emerald-50/30'
                            : 'border-gray-100 hover:border-gray-200'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4 flex-1">
                            <input
                              type="checkbox"
                              checked={selectedModelIds.has(model.id)}
                              onChange={(e) => {
                                const newSet = new Set(selectedModelIds);
                                if (e.target.checked) {
                                  newSet.add(model.id);
                                } else {
                                  newSet.delete(model.id);
                                }
                                setSelectedModelIds(newSet);
                              }}
                              className="w-5 h-5 rounded-lg border-gray-300 text-emerald-600 focus:ring-emerald-500"
                            />
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <h4 className="font-bold text-gray-900">{model.display_name}</h4>
                                <span className={`px-2 py-0.5 text-[10px] font-black uppercase rounded-lg ${
                                  model.is_listed
                                    ? 'bg-emerald-100 text-emerald-700'
                                    : 'bg-gray-100 text-gray-500'
                                }`}>
                                  {model.is_listed ? '已上架' : '未上架'}
                                </span>
                                {model.synced_from_provider && (
                                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-[10px] font-black uppercase rounded-lg">
                                    已同步
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-gray-400 font-mono">{model.name}</p>
                            </div>
                          </div>

                          <button
                            onClick={() => handleToggleListing(model.id, model.is_listed || false)}
                            className={`p-2.5 rounded-xl transition-all ${
                              model.is_listed
                                ? 'bg-emerald-100 text-emerald-600 hover:bg-emerald-200'
                                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                            }`}
                            title={model.is_listed ? '点击下架' : '点击上架'}
                          >
                            {model.is_listed ? <Eye size={18} /> : <EyeOff size={18} />}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  );
};

export default ProviderManagementPanel;
