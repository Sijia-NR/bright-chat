import React, { useState } from 'react';
import { MapPin, Wrench, Lightbulb, RefreshCw, ChevronDown, ChevronUp, Brain, CheckCircle, HelpCircle, ChevronRight, Clock, LucideIcon } from 'lucide-react';
import { TOOL_METADATA } from '../types';

interface ThinkingStep {
  step: number;
  type: 'analysis' | 'decision' | 'action' | 'observation';
  content: string;
  timestamp?: string;
  tool?: string;
  confidence?: number;
}

interface AgentExecutionProgressProps {
  toolCalls: Array<{
    tool: string;
    parameters: Record<string, any>;
    result: any;
    timestamp: number;
  }>;
  reasoning?: string;
  reasoningSteps?: Array<{
    reasoning: string;
    toolDecision?: any;
    step: number;
    timestamp: string;
  }>;
  toolDecision?: {
    tool: string | null;
    parameters: Record<string, any>;
    confidence: number;
  };
  currentStep?: number;
  totalSteps?: number;
}

export const AgentExecutionProgress: React.FC<AgentExecutionProgressProps> = ({
  toolCalls,
  reasoning,
  reasoningSteps = [],
  toolDecision,
  currentStep = 1,
  totalSteps = 5
}) => {
  // 默认展开思维链路
  const [showThinkingChain, setShowThinkingChain] = useState(true);
  const [showToolCalls, setShowToolCalls] = useState(false);

  // 确保 reasoningSteps 是数组
  const safeReasoningSteps = Array.isArray(reasoningSteps) ? reasoningSteps : [];

  if (toolCalls.length === 0 && !reasoning && safeReasoningSteps.length === 0) {
    return null;
  }

  // 构建思维步骤
  const buildThinkingSteps = (): ThinkingStep[] => {
    const steps: ThinkingStep[] = [];

    if (safeReasoningSteps.length > 0) {
      // 使用收集的推理步骤
      safeReasoningSteps.forEach((rs, index) => {
        steps.push({
          step: index + 1,
          type: 'analysis',
          content: rs.reasoning,
          timestamp: rs.timestamp
        });

        if (rs.toolDecision && typeof rs.toolDecision === 'object') {
          const { tool, confidence } = rs.toolDecision;
          if (tool) {
            steps.push({
              step: index + 1.1,
              type: 'decision',
              content: `决定使用工具：${tool} (置信度: ${(confidence * 100).toFixed(0)}%)`,
              tool,
              confidence,
              timestamp: rs.timestamp
            });

            // 添加参数准备步骤
            const parameters = rs.toolDecision?.parameters || {};
            if (Object.keys(parameters).length > 0) {
              const paramStr = Object.entries(parameters)
                .map(([k, v]) => `${k}=${JSON.stringify(v).slice(0, 40)}`)
                .join(', ');
              steps.push({
                step: index + 1.2,
              type: 'action',
              content: `准备参数：${paramStr}`,
              timestamp: rs.timestamp
            });
            }
          } else {
            steps.push({
              step: index + 1.1,
              type: 'decision',
              content: '决定直接回答（无需工具）',
              confidence,
              timestamp: rs.timestamp
            });
          }
        }
      });
    } else if (reasoning || toolDecision) {
      // 单次推理事件
      steps.push({
        step: 1,
        type: 'analysis',
        content: reasoning || '正在分析问题...',
        timestamp: new Date().toISOString()
      });

      if (toolDecision && typeof toolDecision === 'object') {
        const { tool, confidence } = toolDecision;
        if (tool) {
          steps.push({
            step: 2,
            type: 'decision',
            content: `决定使用工具：${tool} (置信度: ${(confidence * 100).toFixed(0)}%)`,
            tool,
            confidence,
            timestamp: new Date().toISOString()
          });

          const parameters = toolDecision.parameters || {};
          if (Object.keys(parameters).length > 0) {
            const paramStr = Object.entries(parameters)
              .map(([k, v]) => `${k}=${JSON.stringify(v).slice(0, 40)}`)
              .join(', ');
            steps.push({
              step: 3,
              type: 'action',
              content: `准备参数：${paramStr}`,
              timestamp: new Date().toISOString()
            });
          }
        } else {
          steps.push({
            step: 2,
            type: 'decision',
            content: '决定直接回答（无需工具）',
            confidence,
            timestamp: new Date().toISOString()
          });
        }
      }
    }

    return steps;
  };

  const thinkingSteps = buildThinkingSteps();

  const getStepIcon = (type: string) => {
    switch (type) {
      case 'analysis': return <Brain className="w-4 h-4 text-blue-500" />;
      case 'decision': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'action': return <HelpCircle className="w-4 h-4 text-orange-500" />;
      default: return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <div className="agent-execution-progress bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg shadow-md p-4 mb-4 border border-blue-200 animate-in slide-in-from-top-2 duration-300 max-w-[85%]">
      {/* 头部 */}
      <div
        className="flex items-center justify-between mb-4 pb-3 border-b border-blue-100 cursor-pointer hover:bg-white/50 rounded-lg px-2 py-1 transition-colors"
        onClick={() => setShowToolCalls(!showToolCalls)}
      >
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <h3 className="text-sm font-semibold text-gray-800">正在执行</h3>
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-600">
          <span className="flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5" />
            {currentStep}/{totalSteps}
          </span>
          <span className="text-gray-300">|</span>
          <span className="flex items-center gap-1">
            <Wrench className="w-3.5 h-3.5" />
            {toolCalls.length}
          </span>
          <span className="text-gray-300">|</span>
          <span className="flex items-center gap-1 text-blue-600">
            {showToolCalls ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </span>
        </div>
      </div>

      {/* 思维链路（默认展开） */}
      {thinkingSteps.length > 0 && (
        <div className="mb-4">
          {/* 思维链路标题 */}
          <div
            className="flex items-center justify-between mb-3 cursor-pointer hover:bg-white/50 rounded px-2 py-1 transition-colors"
            onClick={() => setShowThinkingChain(!showThinkingChain)}
          >
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-purple-600" />
              <h4 className="text-sm font-semibold text-gray-800">思维链路</h4>
              <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">
                {thinkingSteps.length} 个步骤
              </span>
            </div>
            <span className="flex items-center gap-1 text-blue-600">
              {showThinkingChain ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </span>
          </div>

          {/* 思维步骤 */}
          {showThinkingChain && (
            <div className="bg-white/80 rounded-lg border border-purple-200 p-3 space-y-2">
              {thinkingSteps.map((stepItem, index) => (
                <div key={index} className="flex items-start gap-3">
                  {/* 步骤指示器 */}
                  <div className="flex-shrink-0 mt-0.5">
                    {getStepIcon(stepItem.type)}
                  </div>

                  {/* 步骤内容 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-xs font-medium text-gray-700">
                        步骤 {Math.floor(stepItem.step)}
                      </span>
                      {stepItem.confidence !== undefined && stepItem.confidence > 0 && (
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          stepItem.confidence >= 0.8
                            ? 'bg-green-100 text-green-700'
                            : stepItem.confidence >= 0.5
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {(stepItem.confidence * 100).toFixed(0)}% 置信度
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {stepItem.content}
                    </p>
                  </div>

                  {/* 连接线（非最后一步） */}
                  {index < thinkingSteps.length - 1 && (
                    <div className="flex-shrink-0 w-6 flex justify-center">
                      <ChevronRight className="w-4 h-4 text-gray-300" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 工具调用列表（条件渲染） */}
      {showToolCalls && toolCalls.length > 0 && (
        <div className="space-y-2">
          {toolCalls.map((toolCall, index) => {
            const meta = TOOL_METADATA[toolCall.tool] || {
              displayName: toolCall.tool,
              icon: Wrench as LucideIcon,
              color: 'blue',
              description: '工具'
            };
            const IconComponent = meta.icon;

            // 简化参数显示
            const paramPreview = Object.keys(toolCall.parameters).length > 0
              ? Object.entries(toolCall.parameters)
                  .slice(0, 2)
                  .map(([k, v]) => `${k}=${typeof v === 'string' ? v.slice(0, 15) : JSON.stringify(v).slice(0, 15)}`)
                  .join(', ')
              : '';

            return (
              <div
                key={index}
                className="tool-call-item p-3 bg-white/80 rounded-lg border border-gray-200 hover:border-blue-300 transition-all shadow-sm"
              >
                <div className="flex items-start gap-3">
                  {/* 序号 */}
                  <div className="flex-shrink-0 w-6 h-6 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-lg flex items-center justify-center text-sm font-semibold text-blue-600">
                    {index + 1}
                  </div>

                  {/* 工具信息 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <IconComponent className="w-4 h-4 text-gray-700" />
                      <span className="text-sm font-medium text-gray-800">{meta.displayName}</span>
                      <span className="text-xs text-gray-500">{meta.description}</span>
                    </div>
                    {paramPreview && (
                      <div className="text-xs text-gray-500 truncate" title={paramPreview}>
                        {paramPreview}
                      </div>
                    )}
                  </div>

                  {/* 状态指示器 */}
                  <div className="flex-shrink-0">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 底部提示 */}
      <div className="mt-3 pt-3 border-t border-blue-100 text-xs text-gray-500 flex items-center gap-1.5">
        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
        <span>正在处理中，请稍候...</span>
      </div>
    </div>
  );
};
