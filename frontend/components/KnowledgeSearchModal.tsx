import React, { useState } from 'react';
import { X, Search, FileText, ExternalLink, Loader2 } from 'lucide-react';
import { knowledgeService } from '../services/knowledgeService';

interface SearchResult {
  content: string;
  metadata: {
    document_id: string;
    knowledge_base_id: string;
    user_id: string;
    chunk_index: number;
    filename: string;
    file_type: string;
  };
  score: number;
}

interface KnowledgeSearchModalProps {
  onClose: () => void;
}

const KnowledgeSearchModal: React.FC<KnowledgeSearchModalProps> = ({ onClose }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const response = await knowledgeService.search(query, [], 5);
      setResults(response.results || []);
    } catch (err: any) {
      setError(err.message || '搜索失败');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-start justify-center pt-[20vh] z-50">
      <div className="bg-white rounded-[20px] shadow-2xl w-full max-w-3xl max-h-[70vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Search size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-800">知识库快速检索</h2>
              <p className="text-sm text-gray-500">搜索您的知识库内容</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full hover:bg-gray-200 flex items-center justify-center transition-colors"
          >
            <X size={18} className="text-gray-600" />
          </button>
        </div>

        {/* Search Input */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入搜索关键词，例如：人工智能、机器学习..."
              className="w-full px-4 py-3 pl-11 pr-24 bg-gray-50 border border-gray-200 rounded-xl text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
            <Search size={20} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <button
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 bg-gradient-to-r from-blue-500 to-purple-600 text-white text-sm font-medium rounded-lg hover:shadow-lg hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : '搜索'}
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
              {error}
            </div>
          )}

          {!loading && results.length === 0 && !error && (
            <div className="flex flex-col items-center justify-center py-16 text-gray-400">
              <Search size={48} className="mb-4 opacity-50" />
              <p className="text-lg font-medium">开始搜索知识库</p>
              <p className="text-sm mt-2">输入关键词并点击搜索按钮</p>
            </div>
          )}

          {loading && (
            <div className="flex flex-col items-center justify-center py-16">
              <Loader2 size={40} className="animate-spin text-blue-500 mb-4" />
              <p className="text-gray-600">正在搜索知识库...</p>
            </div>
          )}

          {!loading && results.length > 0 && (
            <div className="space-y-4">
              <div className="text-sm text-gray-500 mb-4">
                找到 <span className="font-semibold text-blue-600">{results.length}</span> 条相关结果
              </div>

              {results.map((result, idx) => (
                <div
                  key={idx}
                  className="bg-gradient-to-br from-gray-50 to-white border border-gray-200 rounded-xl p-4 hover:shadow-md hover:border-blue-300 transition-all"
                >
                  {/* Document Header */}
                  <div className="flex items-center gap-2 mb-2">
                    <FileText size={16} className="text-blue-500" />
                    <span className="text-sm font-medium text-gray-800">
                      {result.metadata.filename}
                    </span>
                    <span className="text-xs text-gray-400">
                      · 切片 #{result.metadata.chunk_index + 1}
                    </span>
                    <span className="ml-auto text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full font-medium">
                      相似度: {(result.score * 100).toFixed(1)}%
                    </span>
                  </div>

                  {/* Content */}
                  <div className="text-sm text-gray-700 leading-relaxed bg-white rounded-lg p-3 border border-gray-100">
                    {result.content}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeSearchModal;
