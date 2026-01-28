
import React from 'react';
import { ChevronDown, Share2, MoreHorizontal, LayoutGrid, Search } from 'lucide-react';

interface TopBarProps {
  models: any[];
  selectedModelId: string;
  onModelChange: (id: string) => void;
}

const TopBar: React.FC<TopBarProps> = ({ models, selectedModelId, onModelChange }) => {
  // 当没有选中模型或模型列表为空时，显示提示
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
