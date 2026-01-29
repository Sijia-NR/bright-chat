import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2, Database, Loader2, Check, AlertCircle } from 'lucide-react';
import { useModal } from '../contexts/ModalContext';
import { knowledgeService } from '../services/knowledgeService';
import { KnowledgeBase } from '../types';

interface KnowledgeManageModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRefresh: () => void;
}

interface FormData {
  name: string;
  description: string;
}

interface FormErrors {
  name?: string;
}

const KnowledgeManageModal: React.FC<KnowledgeManageModalProps> = ({
  isOpen,
  onClose,
  onRefresh
}) => {
  const { showToast } = useModal();
  const [view, setView] = useState<'list' | 'create'>('list');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [bases, setBases] = useState<KnowledgeBase[]>([]);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  // 表单状态
  const [formData, setFormData] = useState<FormData>({
    name: '',
    description: ''
  });
  const [errors, setErrors] = useState<FormErrors>({});

  // 加载数据
  const loadData = async () => {
    if (!isOpen) return;

    setLoading(true);
    try {
      const basesData = await knowledgeService.getKnowledgeBases();
      setBases(basesData);
    } catch (e: any) {
      showToast('加载数据失败: ' + e.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [isOpen]);

  // 重置表单
  const resetForm = () => {
    setFormData({
      name: '',
      description: ''
    });
    setErrors({});
  };

  // 切换到创建视图
  const handleShowCreate = () => {
    resetForm();
    setView('create');
  };

  // 返回列表视图
  const handleBackToList = () => {
    setView('list');
    setDeleteConfirmId(null);
  };

  // 验证表单
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = '请输入知识库名称';
    } else if (formData.name.trim().length < 2) {
      newErrors.name = '知识库名称至少需要2个字符';
    } else if (formData.name.trim().length > 50) {
      newErrors.name = '知识库名称不能超过50个字符';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 提交创建
  const handleSubmit = async () => {
    if (!validateForm()) return;

    setSubmitting(true);
    try {
      await knowledgeService.createKnowledgeBase({
        name: formData.name.trim(),
        description: formData.description.trim()
      });

      showToast('知识库创建成功', 'success');
      await loadData();
      onRefresh();
      handleBackToList();
    } catch (e: any) {
      showToast('创建失败: ' + e.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  // 删除知识库
  const handleDelete = async (baseId: string, baseName: string) => {
    if (deleteConfirmId !== baseId) {
      setDeleteConfirmId(baseId);
      return;
    }

    try {
      await knowledgeService.deleteKnowledgeBase(baseId);
      showToast('知识库已删除', 'success');
      await loadData();
      onRefresh();
      setDeleteConfirmId(null);
    } catch (e: any) {
      showToast('删除失败: ' + e.message, 'error');
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-white">
          {view === 'create' ? (
            <button
              onClick={handleBackToList}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X size={20} className="text-gray-600" />
            </button>
          ) : (
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X size={20} className="text-gray-600" />
            </button>
          )}

          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
              <Database size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">
                {view === 'create' ? '新建知识库' : '知识库管理'}
              </h2>
              <p className="text-xs text-gray-500">
                {view === 'create' ? '创建新的知识库' : `共 ${bases.length} 个知识库`}
              </p>
            </div>
          </div>

          <div className="w-10"></div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 size={32} className="animate-spin text-blue-600" />
            </div>
          ) : view === 'list' ? (
            <div className="p-6">
              {/* 工具栏 */}
              <div className="flex items-center justify-between mb-6">
                <div className="text-sm text-gray-500">
                  选择知识库进行管理或创建新知识库
                </div>
                <button
                  onClick={handleShowCreate}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl font-medium transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  <Plus size={18} />
                  <span>新建知识库</span>
                </button>
              </div>

              {/* 知识库列表 */}
              <div className="space-y-3">
                {bases.length === 0 ? (
                  <div className="text-center py-12 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200">
                    <Database size={48} className="mx-auto mb-3 text-gray-300" />
                    <p className="text-gray-500 mb-2">暂无知识库</p>
                    <button
                      onClick={handleShowCreate}
                      className="text-blue-600 hover:text-blue-700 font-medium"
                    >
                      创建第一个知识库 →
                    </button>
                  </div>
                ) : (
                  bases.map(base => {
                    const isConfirming = deleteConfirmId === base.id;

                    return (
                      <div
                        key={base.id}
                        className={`group p-4 bg-white border-2 rounded-xl transition-all hover:shadow-md ${
                          isConfirming
                            ? 'border-red-300 bg-red-50'
                            : 'border-gray-200 hover:border-blue-300'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <Database size={18} className="text-blue-600 flex-shrink-0" />
                              <h3 className="font-semibold text-gray-900 truncate">{base.name}</h3>
                            </div>
                            {base.description && (
                              <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                                {base.description}
                              </p>
                            )}
                            <div className="flex items-center gap-3 text-xs text-gray-500">
                              <span>{base.documentCount || 0} 个文档</span>
                              <span>•</span>
                              <span>
                                创建于 {new Date(base.createdAt).toLocaleDateString()}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 ml-4">
                            {isConfirming ? (
                              <>
                                <button
                                  onClick={() => handleDelete(base.id, base.name)}
                                  className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg font-medium transition-colors flex items-center gap-1"
                                >
                                  <Check size={14} />
                                  确认删除
                                </button>
                                <button
                                  onClick={() => setDeleteConfirmId(null)}
                                  className="px-3 py-1.5 bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm rounded-lg font-medium transition-colors"
                                >
                                  取消
                                </button>
                              </>
                            ) : (
                              <button
                                onClick={() => handleDelete(base.id, base.name)}
                                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                                title="删除知识库"
                              >
                                <Trash2 size={16} />
                              </button>
                            )}
                          </div>
                        </div>

                        {isConfirming && (
                          <div className="mt-3 pt-3 border-t border-red-200">
                            <div className="flex items-start gap-2 text-sm text-red-600">
                              <AlertCircle size={16} className="flex-shrink-0 mt-0.5" />
                              <span>删除知识库将同时删除所有文档和向量数据，此操作无法撤销。确认要删除吗？</span>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          ) : (
            <div className="p-6">
              <div className="max-w-lg mx-auto">
                <div className="mb-6">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    知识库名称 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                    placeholder="例如：产品文档、技术规范..."
                    className={`w-full px-4 py-3 border-2 rounded-xl focus:outline-none focus:ring-2 transition-all ${
                      errors.name
                        ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                        : 'border-gray-200 focus:ring-blue-500 focus:border-blue-500'
                    }`}
                  />
                  {errors.name && (
                    <p className="mt-2 text-sm text-red-600 flex items-center gap-1">
                      <AlertCircle size={14} />
                      {errors.name}
                    </p>
                  )}
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    描述（可选）
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={e => setFormData({ ...formData, description: e.target.value })}
                    placeholder="简要描述这个知识库的用途..."
                    rows={4}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all resize-none"
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={handleBackToList}
                    className="flex-1 px-6 py-3 border-2 border-gray-200 hover:bg-gray-50 text-gray-700 rounded-xl font-medium transition-all"
                  >
                    取消
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={submitting}
                    className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl font-medium transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {submitting ? (
                      <>
                        <Loader2 size={18} className="animate-spin" />
                        创建中...
                      </>
                    ) : (
                      <>
                        <Check size={18} />
                        创建知识库
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-100">
          <p className="text-xs text-gray-500 text-center">
            💡 提示：知识库创建后可以在详情页上传文档
          </p>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeManageModal;
