import React, { useState } from 'react';
import { X, Plus, Edit2, Trash2 } from 'lucide-react';
import { KnowledgeGroup, KnowledgeBase } from '../../types';

interface KnowledgeModalProps {
  isOpen: boolean;
  onClose: () => void;
  groups: KnowledgeGroup[];
  bases: KnowledgeBase[];
  onCreateGroup: (name: string, description?: string) => Promise<void>;
  onUpdateGroup: (id: string, name: string, description?: string) => Promise<void>;
  onDeleteGroup: (id: string) => Promise<void>;
}

const KnowledgeModal: React.FC<KnowledgeModalProps> = ({
  isOpen,
  onClose,
  groups,
  bases,
  onCreateGroup,
  onUpdateGroup,
  onDeleteGroup
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newGroupName, setNewGroupName] = useState('');
  const [showNewGroupInput, setShowNewGroupInput] = useState(false);

  // 调试日志
  console.log('🔍 KnowledgeModal 渲染状态:', { isOpen, groupsCount: groups.length, basesCount: bases.length });

  if (!isOpen) return null;

  const getBasesByGroup = (groupId: string): KnowledgeBase[] => {
    return bases.filter((b: KnowledgeBase) => b.groupId === groupId);
  };

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) return;
    await onCreateGroup(newGroupName.trim());
    setNewGroupName('');
    setShowNewGroupInput(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[80vh] overflow-hidden" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-bold text-gray-900">知识库管理</h2>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh] space-y-3">
          {groups.map((group: KnowledgeGroup) => {
            const groupBases = getBasesByGroup(group.id);
            const isEditing = editingId === group.id;

            return (
              <div key={group.id} className="border border-gray-200 rounded-xl p-4">
                {isEditing ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      defaultValue={group.name}
                      className="flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      autoFocus
                      onKeyDown={(e: React.KeyboardEvent) => {
                        if (e.key === 'Enter') {
                          const target = e.target as HTMLInputElement;
                          onUpdateGroup(group.id, target.value);
                          setEditingId(null);
                        }
                      }}
                    />
                    <button
                      onClick={() => setEditingId(null)}
                      className="px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
                    >
                      取消
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900">{group.name}</h3>
                      <p className="text-xs text-gray-500">{groupBases.length} 个知识库</p>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => setEditingId(group.id)}
                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                      >
                        <Edit2 size={14} />
                      </button>
                      <button
                        onClick={() => {
                          if (confirm(`确定删除分组"${group.name}"吗？`)) {
                            onDeleteGroup(group.id);
                          }
                        }}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                )}

                {groupBases.length > 0 && (
                  <div className="mt-3 pl-3 space-y-1 border-l-2 border-gray-100">
                    {groupBases.map((base: KnowledgeBase) => (
                      <div key={base.id} className="text-sm text-gray-600 truncate">
                        • {base.name}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          {/* New Group Input */}
          {showNewGroupInput ? (
            <div className="border border-dashed border-gray-300 rounded-xl p-4">
              <input
                type="text"
                value={newGroupName}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewGroupName(e.target.value)}
                placeholder="输入分组名称..."
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2"
                autoFocus
                onKeyDown={e => e.key === 'Enter' && handleCreateGroup()}
              />
              <div className="flex gap-2">
                <button
                  onClick={handleCreateGroup}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
                >
                  创建
                </button>
                <button
                  onClick={() => {
                    setShowNewGroupInput(false);
                    setNewGroupName('');
                  }}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  取消
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setShowNewGroupInput(true)}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-gray-300 rounded-xl text-gray-500 hover:border-blue-400 hover:text-blue-600 transition-all"
            >
              <Plus size={16} />
              <span>新建分组</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeModal;
