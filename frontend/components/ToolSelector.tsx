import React, { useState, useEffect } from 'react';
import { Check, ChevronDown, ChevronRight } from 'lucide-react';
import { AgentTool } from '../types';

interface ToolSelectorProps {
  availableTools: AgentTool[];
  selectedTools: string[];
  onSelectionChange: (tools: string[]) => void;
  disabled?: boolean;
}

// 工具分类
const TOOL_CATEGORIES = {
  calculation: { name: '计算', icon: '🧮', color: 'bg-blue-50 text-blue-600' },
  system: { name: '系统', icon: '⚙️', color: 'bg-gray-50 text-gray-600' },
  search: { name: '搜索', icon: '🔍', color: 'bg-green-50 text-green-600' },
  knowledge: { name: '知识库', icon: '📚', color: 'bg-purple-50 text-purple-600' },
};

const ToolSelector: React.FC<ToolSelectorProps> = ({
  availableTools,
  selectedTools,
  onSelectionChange,
  disabled = false
}) => {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(['calculation', 'system', 'search', 'knowledge'])
  );

  // 按分类分组工具
  const toolsByCategory = availableTools.reduce((acc, tool) => {
    if (!acc[tool.category]) {
      acc[tool.category] = [];
    }
    acc[tool.category].push(tool);
    return acc;
  }, {} as Record<string, AgentTool[]>);

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const toggleTool = (toolName: string) => {
    if (disabled) return;

    const newSelection = selectedTools.includes(toolName)
      ? selectedTools.filter(t => t !== toolName)
      : [...selectedTools, toolName];

    onSelectionChange(newSelection);
  };

  const isToolSelected = (toolName: string) => selectedTools.includes(toolName);

  return (
    <div className="space-y-4">
      {Object.entries(toolsByCategory).map(([category, tools]) => {
        const categoryInfo = TOOL_CATEGORIES[category] || {
          name: category,
          icon: '📦',
          color: 'bg-gray-50 text-gray-600'
        };
        const isExpanded = expandedCategories.has(category);

        return (
          <div key={category} className="border border-gray-200 rounded-lg overflow-hidden">
            {/* 分类标题 */}
            <button
              onClick={() => toggleCategory(category)}
              className={`w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors ${
                disabled ? 'cursor-not-allowed opacity-50' : ''
              }`}
              disabled={disabled}
            >
              <div className="flex items-center gap-2">
                <span className="text-lg">{categoryInfo.icon}</span>
                <span className={`text-sm font-bold ${categoryInfo.color}`}>
                  {categoryInfo.name}
                </span>
                <span className="text-xs text-gray-400">({tools.length})</span>
              </div>
              {isExpanded ? (
                <ChevronDown size={16} className="text-gray-400" />
              ) : (
                <ChevronRight size={16} className="text-gray-400" />
              )}
            </button>

            {/* 工具列表 */}
            {isExpanded && (
              <div className="border-t border-gray-200 p-2 space-y-1">
                {tools.map((tool) => {
                  const isSelected = isToolSelected(tool.name);

                  return (
                    <div
                      key={tool.name}
                      onClick={() => toggleTool(tool.name)}
                      className={`
                        flex items-start gap-3 px-3 py-2 rounded-lg cursor-pointer transition-all
                        ${isSelected
                          ? 'bg-blue-50 border border-blue-200'
                          : 'hover:bg-gray-50 border border-transparent'
                        }
                        ${disabled ? 'cursor-not-allowed opacity-50' : ''}
                      `}
                    >
                      {/* 选择框 */}
                      <div className={`
                        flex items-center justify-center w-5 h-5 rounded border-2 mt-0.5
                        ${isSelected
                          ? 'bg-blue-500 border-blue-500'
                          : 'border-gray-300'
                        }
                        ${disabled ? 'opacity-50' : ''}
                      `}>
                        {isSelected && (
                          <Check size={14} className="text-white" />
                        )}
                      </div>

                      {/* 工具信息 */}
                      <div className="flex-1 min-w-0">
                        <div className="font-bold text-sm text-gray-900">
                          {tool.display_name}
                        </div>
                        <div className="text-xs text-gray-500 mt-0.5">
                          {tool.description}
                        </div>
                        <div className="text-[10px] text-gray-400 mt-1">
                          {tool.name}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}

      {/* 已选择工具摘要 */}
      {selectedTools.length > 0 && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="text-sm font-bold text-blue-800 mb-2">
            已选择 {selectedTools.length} 个工具：
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedTools.map((toolName) => {
              const tool = availableTools.find(t => t.name === toolName);
              return tool ? (
                <span
                  key={toolName}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-white border border-blue-200 rounded-full text-xs text-blue-700"
                >
                  {tool.display_name}
                  {!disabled && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleTool(toolName);
                      }}
                      className="ml-1 hover:text-red-500"
                    >
                      ×
                    </button>
                  )}
                </span>
              ) : null;
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default ToolSelector;
