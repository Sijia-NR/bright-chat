/**
 * 知识库管理面板
 * Knowledge Base Management Panel
 *
 * 提供知识库和文档的管理功能
 * Provides knowledge base and document management features
 */
import { useState, useEffect } from 'react';
import { FolderOpen, FileText, Trash2, Plus, Upload } from 'lucide-react';
import { knowledgeService } from '../services/knowledgeService';
import { KnowledgeGroupAPI, KnowledgeBaseAPI, DocumentAPI } from '../types';

interface KnowledgePanelProps {
  onClose?: () => void;
}

export function KnowledgePanel({ onClose }: KnowledgePanelProps) {
  const [groups, setGroups] = useState<KnowledgeGroupAPI[]>([]);
  const [bases, setBases] = useState<KnowledgeBaseAPI[]>([]);
  const [selectedBase, setSelectedBase] = useState<KnowledgeBaseAPI | null>(null);
  const [documents, setDocuments] = useState<DocumentAPI[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 加载知识库分组和列表
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [groupsData, basesData] = await Promise.all([
        knowledgeService.getGroups(),
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
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 创建知识库分组
  const handleCreateGroup = async () => {
    const name = prompt('请输入分组名称:');
    if (!name) return;

    try {
      await knowledgeService.createGroup(name);
      loadData();
    } catch (err: any) {
      alert('创建分组失败: ' + err.message);
    }
  };

  // 创建知识库
  const handleCreateBase = async () => {
    const name = prompt('请输入知识库名称:');
    if (!name) return;

    try {
      await knowledgeService.createKnowledgeBase({
        name,
        description: '',
      });
      loadData();
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
    if (!confirm(`确定要删除知识库 "${kb.name}" 吗？`)) return;

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
      await knowledgeService.deleteDocument(doc.id);
      if (selectedBase) {
        loadDocuments(selectedBase);
      }
    } catch (err: any) {
      alert('删除文档失败: ' + err.message);
    }
  };

  if (loading && groups.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="flex h-full bg-gray-50">
      {/* 左侧：知识库列表 */}
      <div className="w-1/3 border-r border-gray-200 p-4 overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">知识库</h2>
          <div className="flex gap-2">
            <button
              onClick={handleCreateGroup}
              className="p-1 hover:bg-gray-200 rounded"
              title="创建分组"
            >
              <FolderOpen size={16} />
            </button>
            <button
              onClick={handleCreateBase}
              className="p-1 hover:bg-gray-200 rounded"
              title="创建知识库"
            >
              <Plus size={16} />
            </button>
          </div>
        </div>

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
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between p-3 bg-white border rounded"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <FileText size={16} className="text-gray-400" />
                        <span className="font-medium">{doc.filename}</span>
                      </div>
                      <div className="mt-1 text-xs text-gray-500">
                        状态: {doc.upload_status} | 块数: {doc.chunk_count}
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
                ))}
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
  );
}
