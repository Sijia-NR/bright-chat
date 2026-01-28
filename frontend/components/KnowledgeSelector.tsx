/**
 * 知识库选择器
 * Knowledge Base Selector
 *
 * 允许用户选择一个或多个知识库进行 RAG 对话
 * Allows users to select one or more knowledge bases for RAG chat
 */
import { useState, useEffect } from 'react';
import { Database, Check } from 'lucide-react';
import { knowledgeService } from '../services/knowledgeService';
import { KnowledgeBaseAPI } from '../types';

interface KnowledgeSelectorProps {
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  disabled?: boolean;
}

export function KnowledgeSelector({ selectedIds, onChange, disabled }: KnowledgeSelectorProps) {
  const [bases, setBases] = useState<KnowledgeBaseAPI[]>([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    loadKnowledgeBases();
  }, []);

  const loadKnowledgeBases = async () => {
    setLoading(true);
    try {
      const data = await knowledgeService.getKnowledgeBases();
      setBases(data.filter((b) => b.is_active));
    } catch (err) {
      console.error('加载知识库列表失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSelection = (id: string) => {
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter((sid) => sid !== id));
    } else {
      onChange([...selectedIds, id]);
    }
  };

  const selectedBases = bases.filter((b) => selectedIds.includes(b.id));

  return (
    <div className="relative">
      {/* 触发按钮 */}
      <button
        onClick={() => !disabled && setShowDropdown(!showDropdown)}
        disabled={disabled}
        className={`
          flex items-center gap-2 px-3 py-2 border rounded-lg text-left w-full
          ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white hover:border-gray-400'}
        `}
      >
        <Database size={18} className="text-gray-500" />
        <div className="flex-1 truncate">
          {selectedBases.length === 0 ? (
            <span className="text-gray-500">选择知识库...</span>
          ) : selectedBases.length === 1 ? (
            <span>{selectedBases[0].name}</span>
          ) : (
            <span>已选择 {selectedBases.length} 个知识库</span>
          )}
        </div>
      </button>

      {/* 下拉列表 */}
      {showDropdown && !disabled && (
        <>
          {/* 遮罩层 */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowDropdown(false)}
          />

          {/* 下拉内容 */}
          <div className="absolute z-20 mt-1 w-full bg-white border rounded-lg shadow-lg max-h-60 overflow-y-auto">
            {loading ? (
              <div className="p-3 text-center text-gray-500">加载中...</div>
            ) : bases.length === 0 ? (
              <div className="p-3 text-center text-gray-500">暂无可用知识库</div>
            ) : (
              <div className="py-1">
                {bases.map((base) => (
                  <div
                    key={base.id}
                    onClick={() => toggleSelection(base.id)}
                    className={`
                      flex items-center justify-between px-3 py-2 cursor-pointer
                      hover:bg-gray-100
                      ${selectedIds.includes(base.id) ? 'bg-blue-50' : ''}
                    `}
                  >
                    <div className="flex items-center gap-2">
                      <Database size={16} className="text-gray-400" />
                      <div>
                        <div className="font-medium text-sm">{base.name}</div>
                        {base.description && (
                          <div className="text-xs text-gray-500">{base.description}</div>
                        )}
                      </div>
                    </div>
                    {selectedIds.includes(base.id) && (
                      <Check size={16} className="text-blue-600" />
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* 底部提示 */}
            {selectedIds.length > 0 && (
              <div className="border-t p-2 text-xs text-gray-500 bg-gray-50">
                已选择 {selectedIds.length} 个知识库
              </div>
            )}
          </div>
        </>
      )}

      {/* 已选择的标签 */}
      {selectedIds.length > 1 && !showDropdown && (
        <div className="flex flex-wrap gap-1 mt-2">
          {selectedBases.map((base) => (
            <span
              key={base.id}
              className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
            >
              <Database size={12} />
              {base.name}
              <button
                onClick={() => toggleSelection(base.id)}
                className="hover:text-blue-600"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
