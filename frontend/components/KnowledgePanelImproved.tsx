/**
 * 改进的知识库管理面板
 * Improved Knowledge Base Management Panel
 *
 * 主要改进:
 * 1. 添加图标 (Database, Book, FileText, Upload, Trash2, Plus)
 * 2. 改进UI/UX，更好的视觉层次
 * 3. 更好的错误提示和加载状态
 * 4. 优化空状态显示
 */
import { useState, useEffect, useRef } from 'react';
import {
  Database,
  BookOpen,
  FileText,
  Trash2,
  Plus,
  Upload,
  Settings,
  Loader2,
  AlertCircle,
  ChevronRight
} from 'lucide-react';
import { knowledgeService } from '../services/knowledgeService';
import { KnowledgeGroupAPI, KnowledgeBaseAPI, DocumentAPI } from '../types';

interface KnowledgePanelProps {
  onClose?: () => void;
  userId?: string;
}

export function KnowledgePanelImproved({ onClose, userId }: KnowledgePanelProps) {
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
    loadData();
  }, [userId]);

  // 清理轮询定时器
  useEffect(() => {
    return () => {
      pollingIntervalsRef.current.forEach((interval) => clearInterval(interval));
      pollingIntervalsRef.current.clear();
    };
  }, []);

  const loadData = async () => {
    if (!userId) {
      setError('用户未登录');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [groupsData, basesData] = await Promise.all([
        knowledgeService.getGroups(userId),
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

  // 启动文档状态轮询
  const startPollingDocumentStatus = (kbId: string) => {
    const existingInterval = pollingIntervalsRef.current.get(kbId);
    if (existingInterval) {
      clearInterval(existingInterval);
    }

    const interval = setInterval(async () => {
      try {
        const docs = await knowledgeService.getDocuments(kbId);
        const processing = docs.filter((d: DocumentAPI) => d.upload_status === 'processing');

        if (processing.length === 0) {
          clearInterval(interval);
          pollingIntervalsRef.current.delete(kbId);
          setProcessingDocs(new Set());
          if (selectedBase?.id === kbId) {
            loadDocuments(selectedBase);
          }
        } else {
          setProcessingDocs(new Set(processing.map((d: DocumentAPI) => d.id)));
        }
      } catch (err) {
        console.error('轮询文档状态失败:', err);
      }
    }, 3000);

    pollingIntervalsRef.current.set(kbId, interval);
  };

  // 加载文档列表
  const loadDocuments = async (kb: KnowledgeBaseAPI) => {
    setSelectedBase(kb);
    setLoading(true);
    try {
      const docs = await knowledgeService.getDocuments(kb.id);
      setDocuments(docs);

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
    if (!userId) {
      alert('用户未登录');
      return;
    }

    const name = prompt('请输入分组名称:');
    if (!name?.trim()) return;

    try {
      await knowledgeService.createGroup(userId, name.trim());
      loadData();
    } catch (err: any) {
      alert('创建分组失败: ' + err.message);
    }
  };

  // 创建知识库
  const handleCreateBase = async () => {
    const name = prompt('请输入知识库名称:');
    if (!name?.trim()) return;

    const description = prompt('请输入知识库描述（可选）:');

    try {
      await knowledgeService.createKnowledgeBase({
        name: name.trim(),
        description: description?.trim() || '',
        user_id: userId!
      });
      loadData();
      alert('知识库创建成功！');
    } catch (err: any) {
      alert('创建知识库失败: ' + err.message);
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
        alert('文档上传成功，正在后台处理...');

        startPollingDocumentStatus(kb.id);

        if (selectedBase?.id === kb.id) {
          loadDocuments(kb);
        }
      } catch (err: any) {
        alert('文档上传失败: ' + err.message);
      }
    };
    input.click();
  };

  // 删除知识库
  const handleDeleteBase = async (kb: KnowledgeBaseAPI) => {
    if (!confirm(`确定要删除知识库 "${kb.name}" 吗？\n\n删除后无法恢复！`)) return;

    try {
      await knowledgeService.deleteKnowledgeBase(kb.id);
      if (selectedBase?.id === kb.id) {
        setSelectedBase(null);
        setDocuments([]);
      }
      loadData();
    } catch (err: any) {
      alert('删除知识库失败: ' + err.message);
    }
  };

  // 删除文档
  const handleDeleteDocument = async (doc: DocumentAPI) => {
    if (!confirm(`确定要删除文档 "${doc.filename}" 吗？`)) return;

    try {
      await knowledgeService.deleteDocument(selectedBase?.id || '', doc.id);
      if (selectedBase) {
        loadDocuments(selectedBase);
      }
    } catch (err: any) {
      alert('删除文档失败: ' + err.message);
    }
  };

  // 获取状态图标
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="px-2 py-0.5 text-xs font-medium bg-green-100 text-green-700 rounded-full">已完成</span>;
      case 'processing':
        return <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded-full flex items-center gap-1">
          <Loader2 size={10} className="animate-spin" />
          处理中
        </span>;
      case 'error':
        return <span className="px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700 rounded-full flex items-center gap-1">
          <AlertCircle size={10} />
          失败
        </span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded-full">待处理</span>;
    }
  };

  if (loading && groups.length === 0) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="flex flex-col items-center gap-3">
          <Loader2 size={32} className="text-blue-600 animate-spin" />
          <div className="text-gray-600">加载中...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full bg-gray-50">
      {/* 左侧：知识库列表 */}
      <div className="w-1/3 min-w-[320px] border-r border-gray-200 bg-white flex flex-col">
        {/* 标题栏 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <Database className="text-blue-600" size={20} />
            <h2 className="text-lg font-semibold text-gray-800">知识库</h2>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={handleCreateGroup}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="创建分组"
            >
              <FolderOpen size={18} className="text-gray-600" />
            </button>
            <button
              onClick={handleCreateBase}
              className="flex items-center gap-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
              title="创建知识库"
            >
              <Plus size={16} />
              新建
            </button>
          </div>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mx-4 mt-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm flex items-start gap-2">
            <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* 知识库列表 */}
        <div className="flex-1 overflow-y-auto p-4">
          {groups.length === 0 && bases.length === 0 ? (
            <div className="text-center py-12">
              <Database size={48} className="mx-auto text-gray-300 mb-4" />
              <div className="text-gray-500 text-sm mb-2">暂无知识库</div>
              <button
                onClick={handleCreateBase}
                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                创建第一个知识库 →
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {groups.map((group) => (
                <div key={group.id} className="border border-gray-200 rounded-lg overflow-hidden">
                  {/* 分组标题 */}
                  <div className="flex items-center gap-2 px-4 py-2 bg-gray-50 border-b border-gray-200">
                    <BookOpen size={14} className="text-gray-500" />
                    <span className="font-medium text-sm text-gray-700">{group.name}</span>
                  </div>

                  {/* 知识库列表 */}
                  <div className="p-2 space-y-1">
                    {bases
                      .filter((b) => b.group_id === group.id)
                      .map((kb) => (
                        <div
                          key={kb.id}
                          className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all ${
                            selectedBase?.id === kb.id
                              ? 'bg-blue-50 border border-blue-200'
                              : 'hover:bg-gray-50 border border-transparent'
                          }`}
                          onClick={() => loadDocuments(kb)}
                        >
                          <div className="flex items-center gap-2 flex-1 min-w-0">
                            <FileText
                              size={16}
                              className={selectedBase?.id === kb.id ? 'text-blue-600' : 'text-gray-400'}
                            />
                            <span className="font-medium text-sm text-gray-700 truncate">{kb.name}</span>
                            <span className="text-xs text-gray-400 flex-shrink-0">({kb.document_count || 0})</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleUploadDocument(kb);
                              }}
                              className="p-1.5 hover:bg-blue-100 text-gray-500 hover:text-blue-600 rounded-lg transition-colors"
                              title="上传文档"
                            >
                              <Upload size={14} />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteBase(kb);
                              }}
                              className="p-1.5 hover:bg-red-100 text-gray-500 hover:text-red-600 rounded-lg transition-colors"
                              title="删除知识库"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
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
      <div className="flex-1 flex flex-col bg-gray-50">
        {selectedBase ? (
          <>
            {/* 标题栏 */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-white">
              <div className="flex items-center gap-2">
                <FileText className="text-blue-600" size={20} />
                <div>
                  <h2 className="text-lg font-semibold text-gray-800">{selectedBase.name}</h2>
                  <p className="text-xs text-gray-500">文档管理</p>
                </div>
              </div>
              <button
                onClick={() => handleUploadDocument(selectedBase)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                <Upload size={16} />
                上传文档
              </button>
            </div>

            {/* 文档列表 */}
            <div className="flex-1 overflow-y-auto p-6">
              {documents.length === 0 ? (
                <div className="text-center py-16">
                  <FileText size={48} className="mx-auto text-gray-300 mb-4" />
                  <div className="text-gray-500 text-sm mb-2">暂无文档</div>
                  <p className="text-xs text-gray-400">点击"上传文档"按钮添加文件</p>
                </div>
              ) : (
                <div className="grid gap-3">
                  {documents.map((doc) => {
                    const isProcessing = processingDocs.has(doc.id);
                    return (
                      <div
                        key={doc.id}
                        className={`p-4 bg-white border rounded-lg hover:shadow-sm transition-all ${
                          isProcessing ? 'border-blue-300 ring-2 ring-blue-100' : 'border-gray-200'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              <FileText size={18} className="text-gray-400 flex-shrink-0" />
                              <span className="font-medium text-gray-800 truncate">{doc.filename}</span>
                              {getStatusBadge(doc.upload_status)}
                            </div>
                            <div className="flex items-center gap-4 text-xs text-gray-500">
                              <span>类型: {doc.file_type || '未知'}</span>
                              <span>大小: {(doc.file_size / 1024).toFixed(1)} KB</span>
                              <span>切片: {doc.chunk_count}</span>
                            </div>
                            {doc.error_message && (
                              <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-600">
                                错误: {doc.error_message}
                              </div>
                            )}
                          </div>
                          <button
                            onClick={() => handleDeleteDocument(doc)}
                            className="p-2 hover:bg-red-50 text-gray-400 hover:text-red-600 rounded-lg transition-colors"
                            title="删除文档"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <Database size={64} className="mx-auto text-gray-300 mb-4" />
              <div className="text-gray-500 text-lg mb-2">选择一个知识库</div>
              <p className="text-gray-400 text-sm">从左侧列表中选择知识库查看文档</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
