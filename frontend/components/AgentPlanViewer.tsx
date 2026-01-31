import React from 'react';
import { AgentPlanEvent, AgentSubTask } from '../types';
import { ClipboardList, Timer, BarChart3, FileText, CheckCircle, RefreshCw, Clock } from 'lucide-react';

interface AgentPlanViewerProps {
  plan: AgentPlanEvent;
  currentSubtaskIndex: number;
}

export const AgentPlanViewer: React.FC<AgentPlanViewerProps> = ({
  plan,
  currentSubtaskIndex
}) => {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low':
        return 'text-green-600 bg-green-50 border-green-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getPriorityLabel = (priority: string) => {
    const labels = {
      high: '高',
      medium: '中',
      low: '低'
    };
    return labels[priority as keyof typeof labels] || priority;
  };

  return (
    <div className="agent-plan-viewer bg-white rounded-lg shadow-md p-4 mb-4 border border-gray-200 max-w-[85%]">
      {/* 计划头部 */}
      <div className="plan-header flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <ClipboardList className="w-5 h-5 text-gray-700" />
          <h3 className="text-lg font-semibold text-gray-800">执行计划</h3>
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            plan.complexity === 'simple'
              ? 'text-green-600 bg-green-100'
              : 'text-blue-600 bg-blue-100'
          }`}>
            {plan.complexity === 'simple' ? '简单' : '复杂'}
          </span>
        </div>

        <div className="plan-meta flex items-center gap-4 text-sm text-gray-600">
          <span className="flex items-center gap-1">
            <Timer className="w-3.5 h-3.5" />
            预计 {plan.estimated_duration}秒
          </span>
          <span className="flex items-center gap-1">
            <BarChart3 className="w-3.5 h-3.5" />
            置信度 {(plan.confidence * 100).toFixed(0)}%
          </span>
          <span className="flex items-center gap-1">
            <FileText className="w-3.5 h-3.5" />
            {plan.subtasks.length} 个任务
          </span>
        </div>
      </div>

      {/* 子任务列表 */}
      <div className="subtasks-list space-y-2">
        {plan.subtasks.map((subtask, index) => {
          const isCurrent = index === currentSubtaskIndex;
          const isCompleted = index < currentSubtaskIndex;

          return (
            <div
              key={subtask.id}
              className={`subtask-item p-3 rounded-lg border transition-all ${
                isCurrent
                  ? 'active bg-blue-50 border-blue-300 shadow-sm'
                  : isCompleted
                    ? 'completed bg-green-50 border-green-200 opacity-60'
                    : 'pending bg-white border-gray-200 hover:border-gray-300'
              }`}
            >
              {/* 子任务头部 */}
              <div className="subtask-header flex items-center gap-3 mb-2">
                {/* 任务编号 */}
                <div className={`subtask-number flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                  isCurrent
                    ? 'bg-blue-500 text-white'
                    : isCompleted
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-300 text-gray-600'
                }`}>
                  {index + 1}
                </div>

                {/* 任务描述 */}
                <span className="subtask-description flex-1 font-medium text-gray-800">
                  {subtask.description}
                </span>

                {/* 优先级标签 */}
                <span className={`px-2 py-0.5 rounded text-xs font-medium border ${getPriorityColor(subtask.priority)}`}>
                  {getPriorityLabel(subtask.priority)}
                </span>

                {/* 状态图标 */}
                <span className="text-sm">
                  {isCompleted ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : isCurrent ? (
                    <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />
                  ) : (
                    <Clock className="w-5 h-5 text-gray-400" />
                  )}
                </span>
              </div>

              {/* 子任务详情 */}
              <div className="subtask-details pl-9 space-y-1 text-sm text-gray-600">
                <p>
                  <span className="font-medium">目标:</span> {subtask.objective}
                </p>
                <p className="text-xs text-gray-500">
                  预计步骤: {subtask.estimated_steps}
                </p>
              </div>

              {/* 进行中进度条 */}
              {isCurrent && (
                <div className="subtask-progress mt-2 pl-9">
                  <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300 animate-pulse"
                      style={{ width: '50%' }}
                    ></div>
                  </div>
                  <span className="text-xs text-blue-600 mt-1 block">进行中...</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 底部进度总结 */}
      <div className="plan-footer mt-4 pt-3 border-t border-gray-200 text-sm text-gray-600 flex items-center justify-between">
        <span>
          进度: {currentSubtaskIndex + 1} / {plan.subtasks.length}
        </span>
        <div className="w-1/3 bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${((currentSubtaskIndex + 1) / plan.subtasks.length) * 100}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
};
