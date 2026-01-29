import React, { useState, useEffect } from 'react';
import { ArrowLeft, Upload, FileText, Loader2, FileText as FileIcon, X, ChevronLeft, ChevronRight } from 'lucide-react';
import { knowledgeService } from '../services/knowledgeService';
import { useModal } from '../contexts/ModalContext';

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
  const { showToast, showConfirm } = useModal();
  const [base, setBase] = useState<any>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [loadingChunks, setLoadingChunks] = useState(false);

  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10); // 每页显示 10 个切片
  const [totalCount, setTotalCount] = useState(0);
  const [jumpToPage, setJumpToPage] = useState(''); // 跳转到指定页

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
  const loadChunks = async (docId: string, page: number = 1) => {
    setLoadingChunks(true);
    try {
      console.log('🔍 开始加载切片, docId:', docId, 'baseId:', baseId, 'page:', page);
      const offset = (page - 1) * pageSize;
      const data = await knowledgeService.getDocumentChunks(docId, baseId, offset, pageSize);

      console.log('📦 原始 API 响应:', data);
      console.log('📦 响应类型:', typeof data);
      console.log('📦 是否为数组:', Array.isArray(data));
      console.log('📦 是否有 chunks 字段:', 'chunks' in data);

      const chunksArray = data.chunks || [];

      console.log('📦 提取的 chunks 数组:', chunksArray);
      console.log('📦 Chunks 长度:', chunksArray.length);
      console.log('📦 Total count:', data.total_count);
      console.log('📦 Returned count:', data.returned_count);
      console.log('📦 Offset:', data.offset);
      console.log('📦 Limit:', data.limit);

      // 更新总数 - 重要：使用 data.total_count 而不是 chunksArray.length
      const totalCountValue = data.total_count ?? chunksArray.length;
      console.log('📊 最终设置的 totalCount:', totalCountValue);
      console.log('📊 当前 pageSize:', pageSize);
      console.log('📊 是否应该显示分页:', totalCountValue > pageSize);

      setTotalCount(totalCountValue);

      // 调试日志：查看实际数据
      if (process.env.NODE_ENV === 'development') {
        console.log('📦 Chunks loaded:', chunksArray.length);
        if (chunksArray.length > 0) {
          console.log('📦 First chunk:', chunksArray[0]);
          console.log('📦 Last chunk:', chunksArray[chunksArray.length - 1]);
        }
      }

      setChunks(chunksArray);
      setSelectedDocId(docId);
      setCurrentPage(page);
    } catch (e: any) {
      console.error('❌ Failed to load chunks:', e);
      showToast('加载切片失败: ' + e.message, 'error');
    } finally {
      setLoadingChunks(false);
    }
  };

  // 切换页面
  const handlePageChange = (newPage: number) => {
    if (selectedDocId && newPage >= 1 && newPage <= Math.ceil(totalCount / pageSize)) {
      loadChunks(selectedDocId, newPage);
    }
  };

  // 处理每页条数变化
  const handlePageSizeChange = (newSize: number) => {
    setPageSize(newSize);
    setCurrentPage(1); // 重置到第一页
    if (selectedDocId) {
      loadChunks(selectedDocId, 1);
    }
  };

  // 处理跳转到指定页
  const handleJumpToPage = () => {
    const pageNum = parseInt(jumpToPage);
    const totalPages = Math.ceil(totalCount / pageSize);
    if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= totalPages) {
      handlePageChange(pageNum);
      setJumpToPage('');
    } else {
      showToast(`请输入有效的页码 (1-${totalPages})`, 'error');
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
      showToast('文件上传成功！正在后台处理...', 'success');
      await loadDocuments();
      onSuccess?.();
    } catch (e: any) {
      showToast('文件上传失败: ' + e.message, 'error');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  // 删除文档
  const handleDeleteDocument = async (docId: string) => {
    const confirmed = await showConfirm({
      title: '删除文档',
      message: '确定删除这个文档吗？',
      type: 'danger',
      confirmText: '删除',
      cancelText: '取消'
    });

    if (!confirmed) return;

    try {
      await knowledgeService.deleteDocument(baseId, docId);
      await loadDocuments();
      if (selectedDocId === docId) {
        setSelectedDocId(null);
        setChunks([]);
        setCurrentPage(1);
        setTotalCount(0);
      }
      showToast('文档已删除', 'success');
      onSuccess?.();
    } catch (e: any) {
      showToast('删除失败: ' + e.message, 'error');
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
                  共 {totalCount} 个切片
                  {totalCount > pageSize && ` · 第 ${currentPage} 页`}
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
                  <>
                    <div className="space-y-4">
                      {chunks.map((chunk: any, index: number) => (
                        <div
                          key={chunk.id}
                          className="p-4 bg-white rounded-xl border border-gray-200 shadow-sm"
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-xs font-bold text-blue-600">
                              切片 #{chunk.chunk_index + 1}
                            </span>
                            {chunk.metadata && chunk.metadata.filename && (
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

                    {/* 分页组件 */}
                    {totalCount > 0 && (
                      <div className="mt-6 bg-white rounded-lg border border-gray-200 px-4 py-3">
                        <div className="flex flex-col gap-4">
                          {/* 第一行：翻页控制 */}
                          <div className="flex items-center justify-between">
                            <button
                              onClick={() => handlePageChange(currentPage - 1)}
                              disabled={currentPage === 1}
                              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                              <ChevronLeft size={16} />
                              上一页
                            </button>

                            <div className="flex items-center gap-3">
                              <span className="text-sm text-gray-600">
                                第 <span className="font-bold text-gray-900">{currentPage}</span> /
                                <span className="font-bold text-gray-900">{Math.ceil(totalCount / pageSize)}</span> 页
                              </span>
                              <span className="text-sm text-gray-500">
                                ({(currentPage - 1) * pageSize + 1}-{Math.min(currentPage * pageSize, totalCount)} / {totalCount})
                              </span>
                            </div>

                            <button
                              onClick={() => handlePageChange(currentPage + 1)}
                              disabled={currentPage >= Math.ceil(totalCount / pageSize)}
                              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                              下一页
                              <ChevronRight size={16} />
                            </button>
                          </div>

                          {/* 第二行：高级控制（每页条数 + 跳转） */}
                          <div className="flex items-center justify-between pt-3 border-t border-gray-200">
                            {/* 每页条数选择 */}
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-600">每页</span>
                              <select
                                value={pageSize}
                                onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                                className="px-2 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                              >
                                <option value={5}>5 条</option>
                                <option value={10}>10 条</option>
                                <option value={20}>20 条</option>
                                <option value={50}>50 条</option>
                                <option value={100}>100 条</option>
                              </select>
                              <span className="text-sm text-gray-600">条</span>
                            </div>

                            {/* 跳转到指定页 */}
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-600">跳转到</span>
                              <input
                                type="number"
                                min={1}
                                max={Math.ceil(totalCount / pageSize)}
                                value={jumpToPage}
                                onChange={(e) => setJumpToPage(e.target.value)}
                                onKeyPress={(e) => {
                                  if (e.key === 'Enter') {
                                    handleJumpToPage();
                                  }
                                }}
                                placeholder={`1-${Math.ceil(totalCount / pageSize)}`}
                                className="w-24 px-2 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                              />
                              <button
                                onClick={handleJumpToPage}
                                className="px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                              >
                                Go
                              </button>
                              <span className="text-sm text-gray-600">页</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </>
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
