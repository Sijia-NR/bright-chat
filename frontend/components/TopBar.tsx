
import React from 'react';
import { ChevronDown, Share2, MoreHorizontal, LayoutGrid, Search, Bot } from 'lucide-react';
import { Agent } from '../types';

interface TopBarProps {
  models: any[];
  selectedModelId: string;
  onModelChange: (id: string) => void;
  selectedAgent: Agent | null;  // 新增：当前选中的 Agent
}

const TopBar: React.FC<TopBarProps> = ({ models, selectedModelId, onModelChange, selectedAgent }) => {
  // 如果是 Agent 对话，显示 Agent 信息
  if (selectedAgent) {
    return (
      <header className="h-14 border-b border-gray-100 bg-white/80 backdrop-blur-md sticky top-0 z-10 flex items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-600 rounded-lg">
            <Bot size={16} />
            <span className="text-sm font-bold">{selectedAgent.displayName}</span>
          </div>
          <span className="text-xs text-gray-400">数字员工</span>
        </div>

        <div className="flex items-center gap-2">
          <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"><Search size={18} /></button>
          <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"><Share2 size={18} /></button>
          <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"><LayoutGrid size={18} /></button>
          <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"><MoreHorizontal size={18} /></button>
        </div>
      </header>
    );
  }

  // 普通模型对话：显示模型选择器
  const currentModel = selectedModelId
    ? models.find(m => m.id === selectedModelId)
    : null;

  const displayText = currentModel
    ? currentModel.name
    : (models.length === 0 ? '请先配置模型' : '选择模型');

  return (
    <header className="h-14 border-b border-gray-100 bg-white/80 backdrop-blur-md sticky top-0 z-10 flex items-center justify-between px-6">
      <div className="relative group">
        <button
          data-testid="model-selector-button"
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors text-sm font-semibold ${
            models.length === 0 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white hover:bg-gray-100 text-gray-800'
          }`}
          disabled={models.length === 0}
        >
          <span data-testid="selected-model-name">{displayText}</span>
          {models.length > 0 && <ChevronDown size={14} className="text-gray-400" />}
        </button>

        {models.length > 0 && (
          <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all transform origin-top-left scale-95 group-hover:scale-100 z-20">
          <div className="p-1.5 space-y-0.5" data-testid="model-dropdown-list">
            {models.map((model) => (
              <button
                key={model.id}
                data-testid={`model-option-${model.id}`}
                onClick={() => onModelChange(model.id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                  selectedModelId === model.id ? 'bg-blue-50 text-blue-600 font-bold' : 'hover:bg-gray-50 text-gray-600'
                }`}
              >
                <div className="flex flex-col">
                  <span>{model.name}</span>
                  <span className="text-[10px] opacity-60 font-normal">{model.version}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"><Search size={18} /></button>
        <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"><Share2 size={18} /></button>
        <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"><LayoutGrid size={18} /></button>
        <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"><MoreHorizontal size={18} /></button>
      </div>
    </header>
  );
};

export default TopBar;
