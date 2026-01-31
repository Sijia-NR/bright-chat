import React from 'react';
import { Wrench, Timer, Clock, Brain, ChevronRight } from 'lucide-react';
import type { AgentExecution } from '../types';
import { TOOL_METADATA } from '../types';
import { ToolCallCard } from './ToolCallCard';

interface AgentExecutionDetailsProps {
  execution: AgentExecution;
}

export const AgentExecutionDetails: React.FC<AgentExecutionDetailsProps> = ({
  execution
}) => {
  const hasReasoningSteps = execution.reasoningSteps && execution.reasoningSteps.length > 0;
  const hasToolCalls = execution.toolCalls.length > 0;

  // 如果既没有推理步骤也没有工具调用，显示提示
  if (!hasReasoningSteps && !hasToolCalls) {
    return (
      <div className="agent-execution-details bg-white rounded-lg shadow-md p-4 mb-2 border border-gray-200 max-w-[85%]">
        <div className="text-center text-sm text-gray-500 py-4">
          暂无执行详情
        </div>
      </div>
    );
  }

  return (
    <div className="agent-execution-details bg-white rounded-lg shadow-md p-4 mb-2 border border-gray-200 animate-in slide-in-from-top-2 duration-300 max-w-[85%]">
      {/* 推理步骤 */}
      {hasReasoningSteps && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-3 pb-3 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-gradient-to-br from-purple-100 to-violet-100 rounded-lg">
                <Brain className="w-4 h-4 text-purple-600" />
              </div>
              <h4 className="text-sm font-semibold text-gray-800">思维链路</h4>
            </div>
            <div className="text-xs text-gray-500">
              共 {execution.reasoningSteps!.length} 个步骤
            </div>
          </div>

          {/* 推理步骤列表 */}
          <div className="space-y-2">
            {execution.reasoningSteps!.map((step, index) => {
              const hasToolDecision = step.toolDecision && step.toolDecision.tool;

              return (
                <div key={index} className="flex items-start gap-3">
                  {/* 步骤指示器 */}
                  <div className="flex-shrink-0 mt-0.5">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                      hasToolDecision
                        ? 'bg-blue-100 text-blue-600'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {step.step || index + 1}
                    </div>
                  </div>

                  {/* 步骤内容 */}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-gray-700 leading-relaxed bg-gray-50 rounded-lg p-3 break-words">
                      {step.reasoning}
                    </div>

                    {/* 工具决策标签 */}
                    {hasToolDecision && (
                      <div className="mt-2 flex items-center gap-2">
                        <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full font-medium">
                          决定使用: {step.toolDecision!.tool}
                        </span>
                        {step.toolDecision!.confidence && (
                          <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                            step.toolDecision!.confidence >= 0.8
                              ? 'bg-green-100 text-green-700'
                              : 'bg-yellow-100 text-yellow-700'
                          }`}>
                            {(step.toolDecision!.confidence * 100).toFixed(0)}% 置信度
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* 连接线（非最后一步） */}
                  {index < (execution.reasoningSteps!.length - 1) && (
                    <div className="flex-shrink-0 w-6 flex justify-center">
                      <ChevronRight className="w-4 h-4 text-gray-300" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 工具调用 */}
      {hasToolCalls && (
        <div className={hasReasoningSteps ? 'mt-4 pt-4 border-t border-gray-200' : ''}>
          <div className="flex items-center justify-between mb-3 pb-3 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-lg">
                <Wrench className="w-4 h-4 text-blue-600" />
              </div>
              <h4 className="text-sm font-semibold text-gray-800">工具调用详情</h4>
            </div>
            <div className="text-xs text-gray-500">
              共 {execution.toolCalls.length} 个工具
            </div>
          </div>

          {/* 工具卡片列表 */}
          <div className="space-y-3">
            {execution.toolCalls.map((toolCall, index) => {
              const meta = TOOL_METADATA[toolCall.tool] || {
                displayName: toolCall.tool,
                icon: Wrench,
                color: 'blue',
                description: '工具'
              };

              return (
                <ToolCallCard
                  key={`${execution.messageId}-tool-${index}`}
                  toolCall={toolCall}
                  meta={meta}
                  index={index + 1}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* 底部提示 */}
      <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500 flex items-center justify-between">
        <span className="flex items-center gap-1.5">
          <Timer className="w-3.5 h-3.5" />
          <span>总耗时: {(((execution.endTime || Date.now()) - execution.startTime) / 1000).toFixed(2)}s</span>
        </span>
        <span className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5" />
          <span>{new Date(execution.endTime || Date.now()).toLocaleTimeString()}</span>
        </span>
      </div>
    </div>
  );
};
