import React, { useState, useEffect } from 'react';
import { ArrowLeft, Upload, FileText, Loader2, FileText as FileIcon, X } from 'lucide-react';
import { knowledgeService } from '../services/knowledgeService';

interface KnowledgeBaseDetailProps {
  baseId: string;
  onClose: () => void;
  onSuccess?: () => void;
}

interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size?: number;
  chunk_count: number;
  upload_status: 'processing' | 'completed' | 'failed';
  error_message?: string;
  processed_at?: string;
}

interface Chunk {
  id: string;
  chunk_index: number;
  content: string;
  metadata?: {
    filename: string;
    file_type: string;
  };
}

const KnowledgeBaseDetail: React.FC<KnowledgeBaseDetailProps> = ({ baseId, onClose, onSuccess }) => {
  const [base, setBase] = useState<any>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [loadingChunks, setLoadingChunks] = useState(false);

  // 加载知识库详情
  const loadKnowledgeBase = async () => {
    try {
      const data = await knowledgeService.getKnowledgeBase(baseId);
      setBase(data);
    } catch (e: any) {
      console.error('Failed to load knowledge base:', e);
    }
  };

  // 加载文档列表
  const loadDocuments = async () => {
    setLoading(true);
    try {
      const docs = await knowledgeService.getDocuments(baseId);
      setDocuments(docs);
    } catch (e: any) {
      console.error('Failed to load documents:', e);
    } finally {
      setLoading(false);
    }
  };

  // 加载文档切片
  const loadChunks = async (docId: string) => {
    setLoadingChunks(true);
    try {
      const data = await knowledgeService.getDocumentChunks(docId, baseId);
      setChunks(data.chunks || []);
      setSelectedDocId(docId);
    } catch (e: any) {
      console.error('Failed to load chunks:', e);
      alert('加载切片失败: ' + e.message);
    } finally {
      setLoadingChunks(false);
    }
  };

  useEffect(() => {
    loadKnowledgeBase();
    loadDocuments();
  }, [baseId]);

  // 上传文件
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      await knowledgeService.uploadDocument(baseId, file);
      alert('文件上传成功！正在后台处理...');
      await loadDocuments();
      onSuccess?.();
    } catch (e: any) {
      alert('文件上传失败: ' + e.message);
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  // 删除文档
  const handleDeleteDocument = async (docId: string) => {
    if (!confirm('确定删除这个文档吗？')) return;

    try {
      await knowledgeService.deleteDocument(baseId, docId);
      await loadDocuments();
      if (selectedDocId === docId) {
        setSelectedDocId(null);
        setChunks([]);
      }
      alert('文档已删除');
      onSuccess?.();
    } catch (e: any) {
      alert('删除失败: ' + e.message);
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return '-';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  // 获取状态文本
  const getStatusText = (status: string) => {
    switch (status) {
      case 'processing': return '处理中...';
      case 'completed': return '已完成';
      case 'failed': return '失败';
      default: return status;
    }
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processing': return 'text-orange-600 bg-orange-50';
      case 'completed': return 'text-green-600 bg-green-50';
      case 'failed': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="animate-spin text-blue-600 mx-auto mb-4" size={40} />
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-gray-50 h-full">
      {/* 顶部导航栏 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="返回聊天"
          >
            <ArrowLeft size={20} className="text-gray-600" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-900">{base?.name || '知识库'}</h1>
            {base?.description && (
              <p className="text-sm text-gray-500 mt-1">{base.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <FileText size={16} />
          <span>{documents.length} 个文档</span>
        </div>
      </div>

      {/* 主内容区域 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧：文档列表 */}
        <div className="w-2/5 border-r border-gray-200 bg-white flex flex-col">

          {/* 上传区域 */}
          <div className="p-6 border-b border-gray-200">
            <label className="flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-gray-300 rounded-xl hover:border-blue-400 hover:bg-blue-50 transition-all cursor-pointer">
              <Upload size={18} className="text-gray-400" />
              <span className="text-sm text-gray-600">
                {uploading ? '上传中...' : '点击上传文件'}
              </span>
              <input
                type="file"
                accept=".pdf,.doc,.docx,.txt,.md,.html"
                onChange={handleFileUpload}
                disabled={uploading}
                className="hidden"
              />
              {uploading && <Loader2 size={16} className="animate-spin text-blue-600" />}
            </label>
            <p className="text-xs text-gray-400 mt-2 text-center">
              支持 PDF, DOCX, TXT, MD, HTML 等格式
            </p>
          </div>

          {/* 文档列表 */}
          <div className="flex-1 overflow-y-auto p-6">
            <h3 className="text-sm font-bold text-gray-700 mb-3">
              文档列表 ({documents.length})
            </h3>
            <div className="space-y-2">
              {documents.length === 0 ? (
                <div className="text-center py-8 text-gray-400 text-sm">
                  暂无文档，请上传文件
                </div>
              ) : (
                documents.map((doc: Document) => (
                  <div
                    key={doc.id}
                    onClick={() => loadChunks(doc.id)}
                    className={`p-3 rounded-xl border cursor-pointer transition-all ${
                      selectedDocId === doc.id
                        ? 'bg-blue-50 border-blue-500'
                        : 'border-gray-200 hover:bg-gray-50 hover:border-blue-300'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                        <FileText size={16} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900 truncate mb-1">
                          {doc.filename}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <span>{doc.chunk_count} 个切片</span>
                          <span>•</span>
                          <span>{formatFileSize(doc.file_size)}</span>
                          <span>•</span>
                          <span className={getStatusColor(doc.upload_status)}>
                            {getStatusText(doc.upload_status)}
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteDocument(doc.id);
                        }}
                        className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                        title="删除文档"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* 右侧：切片详情 */}
        <div className="flex-1 flex flex-col bg-gray-50">
          {selectedDocId ? (
            <>
              <div className="bg-white border-b border-gray-200 px-6 py-4">
                <h3 className="text-lg font-bold text-gray-900 mb-1">文档切片</h3>
                <p className="text-sm text-gray-500">
                  共 {chunks.length} 个切片
                  {loadingChunks && ' (加载中...)'}
                </p>
              </div>

              <div className="flex-1 overflow-y-auto p-6">
                {loadingChunks ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="animate-spin text-blue-600 mr-2" size={24} />
                    <span className="text-gray-600">加载切片中...</span>
                  </div>
                ) : chunks.length === 0 ? (
                  <div className="text-center py-12 text-gray-400">
                    <FileIcon size={48} className="mx-auto mb-4 opacity-50" />
                    <p>暂无切片数据</p>
                    <p className="text-xs mt-2">文档可能还在处理中，请稍后刷新</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {chunks.map((chunk: Chunk, index: number) => (
                      <div
                        key={chunk.id}
                        className="p-4 bg-white rounded-xl border border-gray-200 shadow-sm"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-bold text-blue-600">
                            切片 #{chunk.chunk_index + 1}
                          </span>
                          {chunk.metadata && (
                            <span className="text-xs text-gray-400">
                              {chunk.metadata.filename}
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                          {chunk.content}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <FileText size={64} className="mx-auto mb-4 opacity-30 text-gray-400" />
                <p className="text-lg font-medium text-gray-500">选择文档查看切片</p>
                <p className="text-sm mt-2 text-gray-400">点击左侧文档列表中的文档</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeBaseDetail;
