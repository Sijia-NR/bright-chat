
import React, { useState, useEffect } from 'react';
import { Server, Plus, Trash2, Loader2, Edit2, X, Eye, EyeOff } from 'lucide-react';
import { modelService } from '../services/modelService';
import { LLMModel, LLMModelCreate, LLMModelType } from '../types';

interface ModelManagementPanelProps {
  refreshTrigger?: number;
  onModelChange?: () => void;
}

const MODEL_TYPE_LABELS: Record<LLMModelType, string> = {
  'openai': 'OpenAI',
  'anthropic': 'Anthropic',
  'custom': 'Custom',
  'ias': 'IAS'
};

const MODEL_TYPE_COLORS: Record<LLMModelType, string> = {
  'openai': 'bg-green-100 text-green-600',
  'anthropic': 'bg-purple-100 text-purple-600',
  'custom': 'bg-gray-100 text-gray-600',
  'ias': 'bg-blue-100 text-blue-600'
};

const ModelManagementPanel: React.FC<ModelManagementPanelProps> = ({ refreshTrigger = 0, onModelChange }) => {
  const [models, setModels] = useState<LLMModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const [editingModel, setEditingModel] = useState<LLMModel | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({});
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  // 表单状态
  const [formData, setFormData] = useState<LLMModelCreate>({
    name: '',
    display_name: '',
    model_type: 'custom',
    api_url: '',
    api_key: '',
    api_version: '',
    description: '',
    is_active: true,
    max_tokens: 4096,
    temperature: 0.7,
    stream_supported: true
  });

  useEffect(() => {
    loadModels();
  }, [refreshTrigger]);

  const loadModels = async () => {
    try {
      setLoading(true);
      const data = await modelService.listModels();
      setModels(data.models);
    } catch (e) {
      console.error("Load models failed", e);
      setMessage({ type: 'error', text: '加载模型列表失败' });
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      display_name: '',
      model_type: 'custom',
      api_url: '',
      api_key: '',
      api_version: '',
      description: '',
      is_active: true,
      max_tokens: 4096,
      temperature: 0.7,
      stream_supported: true
    });
    setShowApiKey({});
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      await modelService.createModel(formData);
      setMessage({ type: 'success', text: '模型创建成功' });
      resetForm();
      setShowForm(false);
      await loadModels();
      onModelChange?.();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || '创建失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingModel) return;
    setLoading(true);
    setMessage(null);
    try {
      await modelService.updateModel(editingModel.id, formData);
      setMessage({ type: 'success', text: '模型更新成功' });
      setEditingModel(null);
      resetForm();
      setShowForm(false);
      await loadModels();
      onModelChange?.();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || '更新失败' });
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (model: LLMModel) => {
    setEditingModel(model);
    setFormData({
      name: model.name,
      display_name: model.display_name,
      model_type: model.model_type,
      api_url: model.api_url,
      api_key: model.api_key || '', // 预填充 API Key
      api_version: model.api_version || '',
      description: model.description || '',
      is_active: model.is_active,
      max_tokens: model.max_tokens,
      temperature: model.temperature,
      stream_supported: model.stream_supported
    });
    setShowForm(true);
  };

  const executeDelete = async (modelId: string) => {
    setActionLoadingId(modelId);
    try {
      await modelService.deleteModel(modelId);
      setModels(prev => prev.filter(m => m.id !== modelId));
      setPendingDeleteId(null);
      setMessage({ type: 'success', text: '模型已删除' });
      onModelChange?.();
    } catch (err) {
      setMessage({ type: 'error', text: '删除失败' });
    } finally {
      setActionLoadingId(null);
    }
  };

  const cancelEdit = () => {
    setEditingModel(null);
    resetForm();
    setShowForm(false);
  };

  return (
    <div className="bg-white rounded-[32px] p-8 border border-gray-100 shadow-sm min-h-[500px]">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-2xl">
            <Server size={24} />
          </div>
          <h2 className="text-lg font-bold text-gray-800">LLM 模型管理</h2>
        </div>
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold transition-all active:scale-95"
          >
            <Plus size={18} />
            添加模型
          </button>
        )}
      </div>

      {/* 表单 */}
      {showForm && (
        <div className="mb-8 p-6 bg-gray-50 rounded-2xl animate-in slide-in-from-top-2 duration-300">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-sm font-bold text-gray-700">
              {editingModel ? '编辑模型' : '创建新模型'}
            </h3>
            <button onClick={cancelEdit} className="text-gray-400 hover:text-gray-600">
              <X size={20} />
            </button>
          </div>

          <form onSubmit={editingModel ? handleUpdate : handleCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                  模型名称 (唯一标识)
                </label>
                <input
                  type="text" required
                  value={formData.name}
                  onChange={e => setFormData({ ...formData, name: e.target.value })}
                  disabled={!!editingModel}
                  placeholder="如: gpt-4-turbo"
                  className="w-full px-4 py-3 bg-white border-2 border-gray-100 rounded-xl outline-none focus:border-indigo-500 transition-all text-sm disabled:bg-gray-100"
                />
              </div>
              <div>
                <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                  显示名称
                </label>
                <input
                  type="text" required
                  value={formData.display_name}
                  onChange={e => setFormData({ ...formData, display_name: e.target.value })}
                  placeholder="如: GPT-4 Turbo"
                  className="w-full px-4 py-3 bg-white border-2 border-gray-100 rounded-xl outline-none focus:border-indigo-500 transition-all text-sm"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                  模型类型
                </label>
                <select
                  value={formData.model_type}
                  onChange={e => setFormData({ ...formData, model_type: e.target.value as LLMModelType })}
                  className="w-full px-4 py-3 bg-white border-2 border-gray-100 rounded-xl outline-none focus:border-indigo-500 transition-all text-sm appearance-none"
                >
                  <option value="custom">Custom API</option>
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="ias">IAS</option>
                </select>
              </div>
              <div>
                <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                  API 版本 (可选)
                </label>
                <input
                  type="text"
                  value={formData.api_version || ''}
                  onChange={e => setFormData({ ...formData, api_version: e.target.value })}
                  placeholder="如: v1, 2023-06-01"
                  className="w-full px-4 py-3 bg-white border-2 border-gray-100 rounded-xl outline-none focus:border-indigo-500 transition-all text-sm"
                />
              </div>
            </div>

            <div>
              <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                API 地址
              </label>
              <input
                type="url" required
                value={formData.api_url}
                onChange={e => setFormData({ ...formData, api_url: e.target.value })}
                placeholder="https://api.example.com/v1/chat/completions"
                className="w-full px-4 py-3 bg-white border-2 border-gray-100 rounded-xl outline-none focus:border-indigo-500 transition-all text-sm"
              />
            </div>

            <div>
              <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                API Key {editingModel && '(留空不修改)'}
              </label>
              <div className="relative">
                <input
                  type={showApiKey['form'] ? 'text' : 'password'}
                  required={!editingModel}
                  value={formData.api_key}
                  onChange={e => setFormData({ ...formData, api_key: e.target.value })}
                  placeholder="sk-..."
                  className="w-full px-4 py-3 pr-24 bg-white border-2 border-gray-100 rounded-xl outline-none focus:border-indigo-500 transition-all text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey({ ...showApiKey, ['form']: !showApiKey['form'] })}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showApiKey['form'] ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div>
              <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                描述 (可选)
              </label>
              <textarea
                value={formData.description || ''}
                onChange={e => setFormData({ ...formData, description: e.target.value })}
                placeholder="模型描述信息..."
                rows={2}
                className="w-full px-4 py-3 bg-white border-2 border-gray-100 rounded-xl outline-none focus:border-indigo-500 transition-all text-sm resize-none"
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                  最大 Token
                </label>
                <input
                  type="number" required
                  value={formData.max_tokens}
                  onChange={e => setFormData({ ...formData, max_tokens: parseInt(e.target.value) || 4096 })}
                  min={1}
                  className="w-full px-4 py-3 bg-white border-2 border-gray-100 rounded-xl outline-none focus:border-indigo-500 transition-all text-sm"
                />
              </div>
              <div>
                <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">
                  Temperature
                </label>
                <input
                  type="number" required step="0.1" min={0} max={2}
                  value={formData.temperature}
                  onChange={e => setFormData({ ...formData, temperature: parseFloat(e.target.value) || 0.7 })}
                  className="w-full px-4 py-3 bg-white border-2 border-gray-100 rounded-xl outline-none focus:border-indigo-500 transition-all text-sm"
                />
              </div>
              <div className="flex items-end">
                <label className="flex items-center gap-2 px-4 py-3 bg-white border-2 border-gray-100 rounded-xl cursor-pointer hover:border-indigo-300 transition-all">
                  <input
                    type="checkbox"
                    checked={formData.stream_supported}
                    onChange={e => setFormData({ ...formData, stream_supported: e.target.checked })}
                    className="w-4 h-4 text-indigo-600 rounded"
                  />
                  <span className="text-sm text-gray-700">支持流式</span>
                </label>
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold transition-all active:scale-[0.98] disabled:opacity-50"
              >
                {loading ? <Loader2 className="animate-spin mx-auto" size={20} /> : (editingModel ? '更新模型' : '创建模型')}
              </button>
              <button
                type="button"
                onClick={cancelEdit}
                className="px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-bold transition-all"
              >
                取消
              </button>
            </div>
          </form>
        </div>
      )}

      {/* 消息提示 */}
      {message && (
        <div className={`mb-4 p-4 rounded-xl flex items-center justify-between ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-100' : 'bg-red-50 text-red-700 border border-red-100'}`}>
          <span className="text-sm font-bold">{message.text}</span>
          <button onClick={() => setMessage(null)}><X size={16} /></button>
        </div>
      )}

      {/* 模型列表 */}
      {loading && !showForm ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="animate-spin text-gray-400" size={32} />
        </div>
      ) : models.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <Server size={36} className="text-gray-300" />
          </div>
          <h3 className="text-lg font-bold text-gray-600 mb-2">还未配置任何模型</h3>
          <p className="text-sm text-gray-400 mb-6">请先配置 LLM 模型后再使用对话功能</p>
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold transition-all"
          >
            <Plus size={18} />
            添加第一个模型
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {models.map(model => (
            <div key={model.id} className="group p-5 border border-gray-100 rounded-2xl hover:bg-gray-50/50 transition-all">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-bold text-gray-900">{model.display_name}</span>
                    <span className={`px-2 py-0.5 text-[10px] rounded-lg font-black uppercase ${MODEL_TYPE_COLORS[model.model_type]}`}>
                      {MODEL_TYPE_LABELS[model.model_type]}
                    </span>
                    {!model.is_active && (
                      <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-[10px] rounded-lg font-bold">已禁用</span>
                    )}
                  </div>
                  <div className="text-xs text-gray-400 space-y-1">
                    <div>名称: <span className="font-mono text-gray-600">{model.name}</span></div>
                    <div className="truncate">API: <span className="font-mono text-gray-600">{model.api_url}</span></div>
                    <div className="flex items-center gap-1">
                      API Key:
                      {showApiKey[model.id] ? (
                        <>
                          <span className="font-mono text-gray-600">{model.api_key}</span>
                          <button
                            onClick={() => setShowApiKey(prev => ({ ...prev, [model.id]: false }))}
                            className="ml-1 text-gray-400 hover:text-gray-600"
                          >
                            <EyeOff size={12} />
                          </button>
                        </>
                      ) : (
                        <>
                          <span className="font-mono text-gray-600">••••••••</span>
                          <button
                            onClick={() => setShowApiKey(prev => ({ ...prev, [model.id]: true }))}
                            className="ml-1 text-gray-400 hover:text-gray-600"
                          >
                            <Eye size={12} />
                          </button>
                        </>
                      )}
                    </div>
                    {model.description && <div className="text-gray-500">{model.description}</div>}
                  </div>
                </div>

                <div className="flex items-center gap-1 ml-4">
                  <button
                    onClick={() => startEdit(model)}
                    className="p-2 text-gray-300 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all opacity-0 group-hover:opacity-100"
                    title="编辑"
                  >
                    <Edit2 size={18} />
                  </button>
                  <button
                    onClick={() => setPendingDeleteId(model.id)}
                    className="p-2 text-gray-300 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all opacity-0 group-hover:opacity-100"
                    title="删除"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 删除确认 */}
      {pendingDeleteId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 animate-in fade-in">
          <div className="bg-white rounded-2xl p-6 max-w-sm mx-4 shadow-2xl animate-in zoom-in-95">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Trash2 size={32} className="text-red-600" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">确认删除模型</h3>
              <p className="text-sm text-gray-500">此操作无法撤销，确定要删除这个模型配置吗？</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setPendingDeleteId(null)}
                className="flex-1 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-bold transition-all"
              >
                取消
              </button>
              <button
                onClick={() => executeDelete(pendingDeleteId)}
                disabled={actionLoadingId === pendingDeleteId}
                className="flex-1 py-3 bg-red-600 hover:bg-red-700 text-white rounded-xl font-bold transition-all disabled:opacity-50"
              >
                {actionLoadingId === pendingDeleteId ? <Loader2 size={20} className="animate-spin mx-auto" /> : '确认删除'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelManagementPanel;
