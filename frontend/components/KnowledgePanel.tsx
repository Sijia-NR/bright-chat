/**
 * 知识库管理面板
 * Knowledge Base Management Panel
 *
 * 提供知识库和文档的管理功能
 * Provides knowledge base and document management features
 */
import { useState, useEffect, useRef } from 'react';
import { FolderOpen, FileText, Trash2, Plus, Upload, ArrowLeft, Loader2 } from 'lucide-react';
import { knowledgeService } from '../services/knowledgeService';
import { useModal } from '../contexts/ModalContext';
import { KnowledgeGroupAPI, KnowledgeBaseAPI, DocumentAPI } from '../types';

interface KnowledgePanelProps {
  onClose: () => void;
  onRefresh: () => void;
}

export function KnowledgePanel({ onClose, onRefresh }: KnowledgePanelProps) {
  const { showToast, showConfirm, showInput } = useModal();
  const [userId, setUserId] = useState<string | null>(null);
  const [groups, setGroups] = useState<KnowledgeGroupAPI[]>([]);
  const [bases, setBases] = useState<KnowledgeBaseAPI[]>([]);
  const [selectedBase, setSelectedBase] = useState<KnowledgeBaseAPI | null>(null);
  const [documents, setDocuments] = useState<DocumentAPI[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processingDocs, setProcessingDocs] = useState<Set<string>>(new Set());
  const pollingIntervalsRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  // 加载知识库分组和列表
  useEffect(() => {
    // 从 localStorage 获取用户信息
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const user = JSON.parse(userStr);
      setUserId(user.id);
    }
    loadData();
  }, []);

  // 清理轮询定时器
  useEffect(() => {
    return () => {
      // 组件卸载时清理所有轮询
      pollingIntervalsRef.current.forEach((interval) => clearInterval(interval));
      pollingIntervalsRef.current.clear();
    };
  }, []);

  // 启动文档状态轮询
  const startPollingDocumentStatus = (kbId: string) => {
    // 如果已有该知识库的轮询，先清除
    const existingInterval = pollingIntervalsRef.current.get(kbId);
    if (existingInterval) {
      clearInterval(existingInterval);
    }

    const interval = setInterval(async () => {
      try {
        const docs = await knowledgeService.getDocuments(kbId);
        const processing = docs.filter((d: DocumentAPI) => d.upload_status === 'processing');

        if (processing.length === 0) {
          // 所有文档处理完成，停止轮询
          clearInterval(interval);
          pollingIntervalsRef.current.delete(kbId);
          setProcessingDocs(new Set());
          // 重新加载文档列表以显示最新状态
          if (selectedBase?.id === kbId) {
            loadDocuments(selectedBase);
          }
        } else {
          // 更新处理中的文档集合
          setProcessingDocs(new Set(processing.map((d: DocumentAPI) => d.id)));
        }
      } catch (err) {
        console.error('轮询文档状态失败:', err);
        // 轮询失败时不停止，继续尝试
      }
    }, 3000); // 每3秒轮询一次

    pollingIntervalsRef.current.set(kbId, interval);
  };

  const loadData = async () => {
    const currentUserId = userId || localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user') || '{}').id : null;
    if (!currentUserId) {
      showToast('用户未登录', 'error');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [groupsData, basesData] = await Promise.all([
        knowledgeService.getGroups(currentUserId),
        knowledgeService.getKnowledgeBases(),
      ]);
      setGroups(groupsData);
      setBases(basesData);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 加载文档列表
  const loadDocuments = async (kb: KnowledgeBaseAPI) => {
    setSelectedBase(kb);
    setLoading(true);
    try {
      const docs = await knowledgeService.getDocuments(kb.id);
      setDocuments(docs);

      // 检查是否有处理中的文档，如果有则启动轮询
      const processing = docs.filter((d: DocumentAPI) => d.upload_status === 'processing');
      if (processing.length > 0) {
        setProcessingDocs(new Set(processing.map((d: DocumentAPI) => d.id)));
        startPollingDocumentStatus(kb.id);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 创建知识库分组
  const handleCreateGroup = async () => {
    const currentUserId = userId || localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user') || '{}').id : null;
    if (!currentUserId) {
      showToast('用户未登录', 'error');
      return;
    }

    try {
      const name = await showInput({
        title: '创建分组',
        placeholder: '请输入分组名称',
        confirmText: '创建',
        cancelText: '取消'
      });
      if (!name) return;

      await knowledgeService.createGroup(currentUserId, name);
      loadData();
      showToast('分组创建成功', 'success');
    } catch (err: any) {
      showToast('创建分组失败: ' + err.message, 'error');
    }
  };

  // 创建知识库
  const handleCreateBase = async () => {
    try {
      const name = await showInput({
        title: '创建知识库',
        placeholder: '请输入知识库名称',
        confirmText: '下一步',
        cancelText: '取消'
      });
      if (!name) return;

      const description = await showInput({
        title: '知识库描述',
        placeholder: '请输入知识库描述（可选）',
        multiline: true,
        rows: 3,
        confirmText: '创建',
        cancelText: '跳过'
      });

      await knowledgeService.createKnowledgeBase({
        name,
        description: description || '',
      });
      loadData();
      showToast('知识库创建成功', 'success');
    } catch (err: any) {
      showToast('创建知识库失败: ' + err.message, 'error');
    }
  };

  // 上传文档
  const handleUploadDocument = async (kb: KnowledgeBaseAPI) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.doc,.docx,.txt,.md,.html';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      try {
        await knowledgeService.uploadDocument(kb.id, file);
        showToast('文档上传成功，正在后台处理...', 'success');

        // 启动状态轮询
        startPollingDocumentStatus(kb.id);

        // 立即刷新一次文档列表
        if (selectedBase?.id === kb.id) {
          loadDocuments(kb);
        }
        onRefresh();
      } catch (err: any) {
        showToast('文档上传失败: ' + err.message, 'error');
      }
    };
    input.click();
  };

  // 删除知识库
  const handleDeleteBase = async (kb: KnowledgeBaseAPI) => {
    const confirmed = await showConfirm({
      title: '删除知识库',
      message: `确定要删除知识库 "${kb.name}" 吗？此操作无法撤销。`,
      type: 'danger',
      confirmText: '删除',
      cancelText: '取消'
    });

    if (!confirmed) return;

    try {
      await knowledgeService.deleteKnowledgeBase(kb.id);
      if (selectedBase?.id === kb.id) {
        setSelectedBase(null);
        setDocuments([]);
      }
      loadData();
      showToast('知识库已删除', 'success');
    } catch (err: any) {
      showToast('删除知识库失败: ' + err.message, 'error');
    }
  };

  // 删除文档
  const handleDeleteDocument = async (doc: DocumentAPI) => {
    const confirmed = await showConfirm({
      title: '删除文档',
      message: `确定要删除文档 "${doc.filename}" 吗？`,
      type: 'danger',
      confirmText: '删除',
      cancelText: '取消'
    });

    if (!confirmed) return;

    try {
      await knowledgeService.deleteDocument(selectedBase?.id || '', doc.id);
      if (selectedBase) {
        loadDocuments(selectedBase);
      }
      showToast('文档已删除', 'success');
      onRefresh();
    } catch (err: any) {
      showToast('删除文档失败: ' + err.message, 'error');
    }
  };

  if (loading && groups.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-blue-600 mx-auto mb-4" size={40} />
        <p className="text-gray-600">加载中...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* 顶部导航栏 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-4">
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="返回聊天"
          >
            <ArrowLeft size={20} className="text-gray-600" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-900">知识库管理</h1>
            <p className="text-sm text-gray-500">管理您的知识库和文档</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCreateGroup}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors"
          >
            <FolderOpen size={16} />
            <span>新建分组</span>
          </button>
          <button
            onClick={handleCreateBase}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            <Plus size={16} />
            <span>新建知识库</span>
          </button>
        </div>
      </div>

      {/* 主内容区域 */}
      <div className="flex flex-1 overflow-hidden">
      {/* 左侧：知识库列表 */}
      <div className="w-1/3 border-r border-gray-200 bg-white overflow-y-auto">
        <div className="p-4">
          <h2 className="text-lg font-semibold mb-4">知识库列表</h2>

        {error && (
          <div className="bg-red-50 text-red-600 p-2 rounded mb-4 text-sm">
            {error}
          </div>
        )}

        {groups.length === 0 ? (
          <div className="text-gray-500 text-sm text-center py-8">
            暂无知识库分组
            <br />
            <button onClick={handleCreateGroup} className="text-blue-600 underline">
              创建第一个分组
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {groups.map((group) => (
              <div key={group.id} className="border rounded p-2">
                <div className="font-medium text-sm">{group.name}</div>
                <div className="mt-1 space-y-1">
                  {bases
                    .filter((b) => b.group_id === group.id)
                    .map((kb) => (
                      <div
                        key={kb.id}
                        className={`flex items-center justify-between p-2 rounded cursor-pointer text-sm ${
                          selectedBase?.id === kb.id ? 'bg-blue-100' : 'hover:bg-gray-100'
                        }`}
                        onClick={() => loadDocuments(kb)}
                      >
                        <div className="flex items-center gap-2">
                          <FileText size={14} />
                          <span>{kb.name}</span>
                          <span className="text-xs text-gray-500">({kb.document_count})</span>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleUploadDocument(kb);
                          }}
                          className="p-1 hover:bg-gray-200 rounded"
                          title="上传文档"
                        >
                          <Upload size={12} />
                        </button>
                      </div>
                    ))}
                </div>
              </div>
            ))}
          </div>
        )}
        </div>
      </div>

      {/* 右侧：文档列表 */}
      <div className="flex-1 p-4 overflow-y-auto">
        {selectedBase ? (
          <>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{selectedBase.name} - 文档</h2>
              <button
                onClick={() => handleUploadDocument(selectedBase)}
                className="flex items-center gap-1 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
              >
                <Upload size={14} />
                上传文档
              </button>
            </div>

            {documents.length === 0 ? (
              <div className="text-gray-500 text-center py-8">
                暂无文档
              </div>
            ) : (
              <div className="space-y-2">
                {documents.map((doc) => {
                  const isProcessing = processingDocs.has(doc.id);
                  return (
                    <div
                      key={doc.id}
                      className={`flex items-center justify-between p-3 bg-white border rounded ${isProcessing ? 'border-blue-300 bg-blue-50' : ''}`}
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <FileText size={16} className="text-gray-400" />
                          <span className="font-medium">{doc.filename}</span>
                          {isProcessing && (
                            <span className="text-xs text-blue-600 animate-pulse">
                              处理中...
                            </span>
                          )}
                        </div>
                        <div className="mt-1 text-xs text-gray-500">
                          状态: {doc.upload_status} | 块数: {doc.chunk_count}
                          {doc.error_message && (
                            <span className="text-red-600 ml-2">错误: {doc.error_message}</span>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => handleDeleteDocument(doc)}
                        className="p-1 hover:bg-red-100 text-red-600 rounded"
                        title="删除文档"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            请从左侧选择一个知识库查看文档
          </div>
        )}
      </div>
      </div>
    </div>
  );
}

export default KnowledgePanel;
