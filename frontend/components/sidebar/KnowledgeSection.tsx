import React from 'react';
import { ChevronDown, ChevronUp, Plus, Settings, Database, Book } from 'lucide-react';
import { KnowledgeBase } from '../../types';

interface KnowledgeSectionProps {
  bases: KnowledgeBase[];
  isExpanded: boolean;
  onToggle: () => void;
  onOpenManage: () => void;
  onCreateBase: () => void;
  onSelectBase: (baseId: string) => void;
}

const KnowledgeSection: React.FC<KnowledgeSectionProps> = ({
  bases,
  isExpanded,
  onToggle,
  onOpenManage,
  onCreateBase,
  onSelectBase
}) => {
  return (
    <div className="border-b border-gray-50">
      <div className="flex items-center justify-between px-4 py-3">
        <button
          onClick={onToggle}
          className="flex items-center gap-2 text-xs font-bold text-gray-400 hover:text-gray-600 transition-colors"
        >
          <Database size={14} />
          <span className="text-[10px]">个人知识库</span>
          {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
        <button
          onClick={onOpenManage}
          className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
          title="管理知识库"
        >
          <Settings size={14} />
        </button>
      </div>

      {isExpanded && (
        <div className="px-3 pb-3 space-y-1">
          {/* 知识库列表 */}
          {bases.map((base: KnowledgeBase) => (
            <div
              key={base.id}
              onClick={() => onSelectBase(base.id)}
              className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-gray-50 transition-all cursor-pointer"
            >
              <Book size={14} className="text-blue-500 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-700 truncate">{base.name}</div>
                {base.description && (
                  <div className="text-xs text-gray-400 truncate">{base.description}</div>
                )}
              </div>
            </div>
          ))}

          {/* 新建知识库按钮 */}
          <button
            onClick={onCreateBase}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all"
          >
            <Plus size={14} />
            <span>新建知识库</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default KnowledgeSection;
