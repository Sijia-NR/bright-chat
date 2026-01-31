import React from 'react';
import { Wrench, MapPin, Timer, ChevronDown, CheckCircle2 } from 'lucide-react';
import type { AgentExecution } from '../types';

interface AgentExecutionSummaryProps {
  execution: AgentExecution;
  onToggle: () => void;
}

export const AgentExecutionSummary: React.FC<AgentExecutionSummaryProps> = ({
  execution,
  onToggle
}) => {
  const duration = execution.endTime
    ? ((execution.endTime - execution.startTime) / 1000).toFixed(1)
    : ((Date.now() - execution.startTime) / 1000).toFixed(1);

  const toolCount = execution.toolCalls.length;
  const stepCount = execution.events.filter(e => e.type === 'step').length;

  return (
    <div
      className="agent-execution-summary bg-gradient-to-r from-slate-50 to-gray-50 rounded-lg shadow-sm p-2.5 px-3 mt-2 mb-2 cursor-pointer hover:from-slate-100 hover:to-gray-100 transition-all border border-slate-200 max-w-[85%]"
      onClick={onToggle}
    >
      <div className="flex items-center justify-between gap-2">
        {/* 左侧：成功图标和统计 */}
        <div className="flex items-center gap-2">
          {/* 成功图标 */}
          <div className="flex-shrink-0 w-6 h-6 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-full flex items-center justify-center text-white shadow-sm">
            <CheckCircle2 className="w-3.5 h-3.5" />
          </div>

          {/* 统计信息 - 带图标版 */}
          <div className="flex items-center gap-1.5 text-xs text-gray-600">
            {/* 工具数 */}
            <div className="flex items-center gap-0.5">
              <Wrench className="w-3 h-3 text-gray-400 flex-shrink-0" />
              <span className="font-medium text-gray-700">{toolCount}</span>
            </div>

            {/* 圆点分隔符 */}
            <span className="text-gray-300">•</span>

            {/* 步骤数 */}
            <div className="flex items-center gap-0.5">
              <MapPin className="w-3 h-3 text-gray-400 flex-shrink-0" />
              <span className="font-medium text-gray-700">{stepCount}</span>
            </div>

            {/* 圆点分隔符 */}
            <span className="text-gray-300">•</span>

            {/* 耗时 */}
            <div className="flex items-center gap-0.5">
              <Timer className="w-3 h-3 text-gray-400 flex-shrink-0" />
              <span className="font-medium text-gray-700">{duration}s</span>
            </div>
          </div>
        </div>

        {/* 右侧：展开/折叠指示 */}
        <div className="flex-shrink-0">
          <ChevronDown
            className={`w-4 h-4 text-gray-500 transition-transform duration-200 ${execution.showDetails ? 'rotate-180' : ''}`}
          />
        </div>
      </div>
    </div>
  );
};
