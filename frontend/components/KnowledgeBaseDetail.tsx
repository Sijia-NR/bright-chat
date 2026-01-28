import React, { useState, useEffect, useCallback } from 'react';
import { ArrowLeft, Upload, File, Trash2, RefreshCw, Search, FileText, Image, Archive, FolderOpen } from 'lucide-react';
import { KnowledgeGroup, DocumentAPI } from '../types';
import { knowledgeService } from '../services/knowledgeService';

interface KnowledgeBaseDetailProps {
  knowledgeGroup: KnowledgeGroup;
  onBack: () => void;
  onRefresh: () => void;
  onDocumentClick?: (docId: string, filename: string, chunkCount: number) => void;
}

const KnowledgeBaseDetail: React.FC<KnowledgeBaseDetailProps> = ({
  knowledgeGroup,
  onBack,
  onRefresh,
  onDocumentClick
}) => {
  const [documents, setDocuments] = useState<DocumentAPI[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  console.log('[KnowledgeBaseDetail] Rendering for group:', knowledgeGroup);

  // 加载文档列表
  const loadDocuments = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // 获取该分组下的所有知识库
      const bases = await knowledgeService.getKnowledgeBases(knowledgeGroup.id);
      console.log('[KnowledgeBaseDetail] Bases for group:', bases);

      // 获取每个知识库的文档
      const allDocs: DocumentAPI[] = [];
      for (const base of bases) {
        const docs = await knowledgeService.getDocuments(base.id);
        allDocs.push(...docs);
      }

      console.log('[KnowledgeBaseDetail] Total documents loaded:', allDocs.length);
      setDocuments(allDocs);
    } catch (err: any) {
      console.error('Failed to load documents:', err);
      setError(err.message || '加载文档列表失败');
    } finally {
      setIsLoading(false);
    }
  }, [knowledgeGroup.id]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  // 上传文档 - 上传到该分组的默认知识库
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    setIsUploading(true);
    setError(null);

    try {
      // 获取该分组下的第一个知识库，如果没有则创建
      let bases = await knowledgeService.getKnowledgeBases(knowledgeGroup.id);
      let targetBase = bases[0];

      if (!targetBase) {
        console.log('[KnowledgeBaseDetail] No base found, creating new one');
        targetBase = await knowledgeService.createKnowledgeBase({
          name: knowledgeGroup.name,
          description: knowledgeGroup.description,
          group_id: knowledgeGroup.id
        });
      }

      console.log('[KnowledgeBaseDetail] Uploading to base:', targetBase.id);
      await knowledgeService.uploadDocument(targetBase.id, file);
      await loadDocuments();
      onRefresh();
    } catch (err: any) {
      console.error('Failed to upload document:', err);
      setError(err.message || '文档上传失败');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  // 删除文档
  const handleDelete = async (docId: string) => {
    if (!confirm('确定要删除这个文档吗？此操作无法撤销。')) return;

    try {
      await knowledgeService.deleteDocument(docId);
      await loadDocuments();
      onRefresh();
    } catch (err: any) {
      console.error('Failed to delete document:', err);
      setError(err.message || '删除文档失败');
    }
  };

  // 获取文件图标
  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '')) {
      return <Image size={18} />;
    }
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext || '')) {
      return <Archive size={18} />;
    }
    return <FileText size={18} />;
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return '-';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  // 过滤文档
  const filteredDocuments = documents.filter(doc =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col bg-white">
      {/* 头部 */}
      <div className="border-b border-gray-100 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-4">
          {/* 返回按钮 */}
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors mb-4"
          >
            <ArrowLeft size={16} />
            <span>返回</span>
          </button>

          {/* 知识库信息 */}
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-blue-50 text-blue-600 rounded-xl">
                  <FolderOpen size={20} />
                </div>
                <h1 className="text-2xl font-bold text-gray-900">{knowledgeGroup.name}</h1>
              </div>
              {knowledgeGroup.description && (
                <p className="text-sm text-gray-500 ml-11">{knowledgeGroup.description}</p>
              )}
              <div className="flex items-center gap-3 text-xs text-gray-400 ml-11 mt-2">
                <span>{documents.length} 个文件</span>
              </div>
            </div>

            {/* 上传按钮 */}
            <div>
              <input
                type="file"
                id="file-upload"
                className="hidden"
                onChange={handleUpload}
                disabled={isUploading}
              />
              <label
                htmlFor="file-upload"
                className={`
                  flex items-center gap-2 px-4 py-2
                  bg-blue-600 text-white
                  rounded-xl text-sm font-medium
                  hover:bg-blue-700
                  transition-all
                  cursor-pointer
                  ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              >
                {isUploading ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    <span>上传中...</span>
                  </>
                ) : (
                  <>
                    <Upload size={16} />
                    <span>上传文件</span>
                  </>
                )}
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        <div className="max-w-6xl mx-auto px-6 py-6">
          {/* 错误提示 */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600">
              {error}
            </div>
          )}

          {/* 搜索框 */}
          <div className="mb-6">
            <div className="relative">
              <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="搜索文件..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* 文件列表 */}
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw size={24} className="text-gray-400 animate-spin" />
            </div>
          ) : filteredDocuments.length === 0 ? (
            <div className="text-center py-12">
              <File size={48} className="text-gray-300 mx-auto mb-4" />
              <p className="text-sm text-gray-500 font-medium">
                {searchQuery ? '没有找到匹配的文件' : '还没有上传任何文件'}
              </p>
              {!searchQuery && (
                <p className="text-xs text-gray-400 mt-2">
                  点击右上角的"上传文件"按钮开始添加文件
                </p>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredDocuments.map((doc) => (
                <div
                  key={doc.id}
                  onClick={() => onDocumentClick && onDocumentClick(doc.id, doc.filename, doc.chunk_count)}
                  className="flex items-center gap-4 p-4 bg-white border border-gray-100 rounded-xl hover:border-blue-200 hover:bg-blue-50/30 cursor-pointer transition-all group"
                >
                  {/* 图标 */}
                  <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                    {getFileIcon(doc.filename)}
                  </div>

                  {/* 信息 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-gray-900 truncate">
                        {doc.filename}
                      </span>
                      {doc.upload_status !== 'completed' && (
                        <span className="px-2 py-0.5 text-[10px] font-medium bg-yellow-100 text-yellow-700 rounded-full">
                          {doc.upload_status === 'processing' ? '处理中' : doc.upload_status}
                        </span>
                      )}
                      {doc.error_message && (
                        <span className="px-2 py-0.5 text-[10px] font-medium bg-red-100 text-red-700 rounded-full" title={doc.error_message}>
                          错误
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-400">
                      <span>{doc.chunk_count} 个分块</span>
                      <span>•</span>
                      <span>{formatFileSize(doc.file_size)}</span>
                      {doc.processed_at && (
                        <>
                          <span>•</span>
                          <span>{new Date(doc.processed_at).toLocaleDateString()}</span>
                        </>
                      )}
                    </div>
                  </div>

                  {/* 删除按钮 */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();  // 阻止触发文档点击
                      handleDelete(doc.id);
                    }}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                    title="删除文件"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeBaseDetail;
