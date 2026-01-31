import React, { useState } from 'react';
import { Download, Upload, Clock, ChevronDown, LucideIcon } from 'lucide-react';

interface ToolCallCardProps {
  toolCall: {
    tool: string;
    parameters: Record<string, any>;
    result: any;
    timestamp: number;
  };
  meta: {
    displayName: string;
    icon: LucideIcon;
    color: string;
    description: string;
  };
  index: number;
}

export const ToolCallCard: React.FC<ToolCallCardProps> = ({
  toolCall,
  meta,
  index
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const IconComponent = meta.icon;

  const formatResult = (result: any): string => {
    if (typeof result === 'string') {
      return result;
    }
    return JSON.stringify(result, null, 2);
  };

  const hasParameters = Object.keys(toolCall.parameters).length > 0;

  // 获取工具颜色
  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'from-blue-50 to-indigo-50 text-blue-600 border-blue-200',
      green: 'from-green-50 to-emerald-50 text-green-600 border-green-200',
      orange: 'from-orange-50 to-amber-50 text-orange-600 border-orange-200',
      purple: 'from-purple-50 to-violet-50 text-purple-600 border-purple-200',
      cyan: 'from-cyan-50 to-sky-50 text-cyan-600 border-cyan-200',
      yellow: 'from-yellow-50 to-amber-50 text-yellow-600 border-yellow-200',
      gray: 'from-gray-50 to-slate-50 text-gray-600 border-gray-200',
    };
    return colors[color as keyof typeof colors] || colors.gray;
  };

  const colorClasses = getColorClasses(meta.color);

  return (
    <div className="tool-call-card bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      {/* 卡片头部 */}
      <div
        className={`tool-call-header p-3 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors ${showDetails ? 'bg-gray-50' : ''}`}
        onClick={() => setShowDetails(!showDetails)}
      >
        <div className="flex items-center gap-3">
          {/* 序号 */}
          <div className={`flex-shrink-0 w-7 h-7 bg-gradient-to-br ${colorClasses} rounded-lg flex items-center justify-center text-sm font-bold`}>
            {index}
          </div>

          {/* 工具图标 */}
          <div className={`flex-shrink-0 w-10 h-10 bg-gradient-to-br ${colorClasses} rounded-xl flex items-center justify-center shadow-sm`}>
            <IconComponent className="w-5 h-5" />
          </div>

          {/* 工具信息 */}
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-gray-800">{meta.displayName}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full border ${colorClasses}`}>
                {meta.description}
              </span>
            </div>
            {hasParameters && (
              <span className="text-xs text-gray-500">
                {Object.keys(toolCall.parameters).length} 个参数
              </span>
            )}
          </div>
        </div>

        {/* 展开/折叠指示 */}
        <div className="flex items-center gap-2">
          {hasParameters && (
            <span className="text-xs text-gray-400">
              {showDetails ? '隐藏' : '详情'}
            </span>
          )}
          <ChevronDown
            className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${showDetails ? 'rotate-180' : ''}`}
          />
        </div>
      </div>

      {/* 详细内容（条件渲染） */}
      {showDetails && (
        <div className="tool-call-details p-3 bg-gray-50 border-t border-gray-200 space-y-3 animate-in slide-in-from-top-2 duration-200">
          {/* 参数 */}
          {hasParameters && (
            <div className="tool-parameters">
              <div className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-1.5">
                <Download className="w-3.5 h-3.5" />
                <span>输入参数</span>
              </div>
              <pre className="text-xs bg-white rounded-lg p-3 overflow-x-auto border border-gray-200 font-mono leading-relaxed">
                {JSON.stringify(toolCall.parameters, null, 2)}
              </pre>
            </div>
          )}

          {/* 结果 */}
          <div className="tool-result">
            <div className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-1.5">
              <Upload className="w-3.5 h-3.5" />
              <span>执行结果</span>
            </div>
            <pre className="text-xs bg-white rounded-lg p-3 overflow-x-auto max-h-60 overflow-y-auto border border-gray-200 font-mono leading-relaxed">
              {formatResult(toolCall.result)}
            </pre>
          </div>

          {/* 时间戳 */}
          <div className="text-xs text-gray-400 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            <span>{new Date(toolCall.timestamp).toLocaleTimeString()}</span>
          </div>
        </div>
      )}
    </div>
  );
};
