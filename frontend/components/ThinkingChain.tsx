import React from 'react';
import { Brain, ChevronRight, CheckCircle, XCircle, HelpCircle, Clock } from 'lucide-react';

interface ThinkingStep {
  step: number;
  type: 'analysis' | 'decision' | 'action' | 'observation';
  content: string;
  timestamp?: string;
  tool?: string;
  confidence?: number;
}

interface ThinkingChainProps {
  reasoning: string;
  toolDecision?: {
    tool: string | null;
    parameters: Record<string, any>;
    confidence: number;
  };
  step: number;
  timestamp: string;
}

export const ThinkingChain: React.FC<ThinkingChainProps> = ({
  reasoning,
  toolDecision,
  step,
  timestamp
}) => {
  // 解析 reasoning，提取关键信息
  const parseReasoning = (text: string): ThinkingStep[] => {
    const steps: ThinkingStep[] = [];

    // 步骤 1: 问题分析
    steps.push({
      step: 1,
      type: 'analysis',
      content: '问题分析：' + (text || '正在分析问题...'),
      timestamp
    });

    // 步骤 2: 工具决策
    if (toolDecision) {
      const { tool, parameters, confidence } = toolDecision;
      if (tool) {
        steps.push({
          step: 2,
          type: 'decision',
          content: `决定使用工具：${tool} (置信度: ${(confidence * 100).toFixed(0)}%)`,
          tool,
          confidence,
          timestamp
        });

        // 步骤 3: 参数准备
        if (parameters && Object.keys(parameters).length > 0) {
          const paramStr = Object.entries(parameters)
            .map(([k, v]) => `${k}=${JSON.stringify(v).slice(0, 50)}`)
            .join(', ');
          steps.push({
            step: 3,
            type: 'action',
            content: `准备参数：${paramStr}`,
            timestamp
          });
        }
      } else {
        steps.push({
          step: 2,
          type: 'decision',
          content: '决定直接回答（无需工具）',
          confidence,
          timestamp
        });
      }
    }

    return steps;
  };

  const steps = parseReasoning(reasoning);

  const getStepIcon = (type: string) => {
    switch (type) {
      case 'analysis': return <Brain className="w-4 h-4 text-blue-500" />;
      case 'decision': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'action': return <HelpCircle className="w-4 h-4 text-orange-500" />;
      default: return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <div className="thinking-chain bg-white rounded-lg border border-blue-200 p-4 mb-3">
      {/* 标题栏 */}
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-gray-100">
        <Brain className="w-5 h-5 text-purple-600" />
        <h4 className="text-sm font-semibold text-gray-800">思维链路</h4>
        <span className="text-xs text-gray-500 ml-auto">
          {new Date(timestamp).toLocaleTimeString()}
        </span>
      </div>

      {/* 思维步骤 */}
      <div className="space-y-2">
        {steps.map((stepItem, index) => (
          <div key={index} className="flex items-start gap-3">
            {/* 步骤指示器 */}
            <div className="flex-shrink-0 mt-0.5">
              {getStepIcon(stepItem.type)}
            </div>

            {/* 步骤内容 */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-xs font-medium text-gray-700">
                  步骤 {stepItem.step}
                </span>
                {stepItem.confidence !== undefined && (
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
            {index < steps.length - 1 && (
              <div className="flex-shrink-0 w-6 flex justify-center">
                <ChevronRight className="w-4 h-4 text-gray-300" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 原始推理（可折叠） */}
      {reasoning && (
        <details className="mt-3 pt-3 border-t border-gray-100">
          <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
            查看原始推理
          </summary>
          <div className="mt-2 p-2 bg-gray-50 rounded text-xs text-gray-600">
            {reasoning}
          </div>
        </details>
      )}
    </div>
  );
};
