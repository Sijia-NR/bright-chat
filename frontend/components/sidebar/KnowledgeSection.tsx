import React from 'react';
import { ChevronDown, ChevronUp, Folder, Plus, Settings } from 'lucide-react';
import { KnowledgeGroup, KnowledgeBase } from '../../types';

interface KnowledgeSectionProps {
  groups: KnowledgeGroup[];
  bases: KnowledgeBase[];
  isExpanded: boolean;
  onToggle: () => void;
  onOpenManage: () => void;
}

const KnowledgeSection: React.FC<KnowledgeSectionProps> = ({
  groups,
  bases,
  isExpanded,
  onToggle,
  onOpenManage
}) => {
  const getBasesByGroup = (groupId: string): KnowledgeBase[] => {
    return bases.filter((b: KnowledgeBase) => b.groupId === groupId);
  };

  return (
    <div className="border-b border-gray-50">
      <div className="flex items-center justify-between px-4 py-3">
        <button
          onClick={onToggle}
          className="flex items-center gap-2 text-xs font-bold text-gray-400 hover:text-gray-600 transition-colors"
        >
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
          {groups.map((group: KnowledgeGroup) => {
            const groupBases = getBasesByGroup(group.id);

            return (
              <div key={group.id} className="px-3 py-2 rounded-xl hover:bg-gray-50 transition-all">
                <div className="flex items-center gap-2 mb-1.5">
                  <Folder size={14} className="text-gray-400" />
                  <span className="text-sm font-medium text-gray-700">{group.name}</span>
                  <span className="text-[10px] text-gray-400">({groupBases.length})</span>
                </div>

                {groupBases.length > 0 && (
                  <div className="pl-5 space-y-0.5">
                    {groupBases.map((base: KnowledgeBase) => (
                      <div key={base.id} className="text-xs text-gray-500 truncate">
                        • {base.name}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all">
            <Plus size={14} />
            <span>新建分组</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default KnowledgeSection;
