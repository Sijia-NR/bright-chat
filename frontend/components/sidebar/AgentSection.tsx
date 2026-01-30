import React from 'react';
import { ChevronDown, ChevronUp, Crown, BarChart3, PenTool, Bot } from 'lucide-react';
import { Agent, AgentAPI, AgentType } from '../../types';

interface AgentSectionProps {
  agents: AgentAPI[];  // 修改为 AgentAPI
  isExpanded: boolean;
  onToggle: () => void;
  onAgentClick: (agent: AgentAPI) => void;  // 修改为接收 AgentAPI
}

const AGENT_ICONS: Record<AgentType, typeof Crown> = {
  [AgentType.TEAM_LEADER]: Crown,
  [AgentType.DATA_ANALYST]: BarChart3,
  [AgentType.WRITING_ASSISTANT]: PenTool
};

const AGENT_COLORS: Record<AgentType, string> = {
  [AgentType.TEAM_LEADER]: 'text-purple-600 bg-purple-50 hover:bg-purple-100',
  [AgentType.DATA_ANALYST]: 'text-blue-600 bg-blue-50 hover:bg-blue-100',
  [AgentType.WRITING_ASSISTANT]: 'text-green-600 bg-green-50 hover:bg-green-100'
};

const AgentSection: React.FC<AgentSectionProps> = ({
  agents,
  isExpanded,
  onToggle,
  onAgentClick
}) => {
  return (
    <div className="border-b border-gray-50">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 text-xs font-bold text-gray-400 hover:text-gray-600 transition-colors"
      >
        <span className="flex items-center gap-2">
          <span className="text-[10px]">数字员工</span>
        </span>
        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {isExpanded && (
        <div className="px-3 pb-3 space-y-1">
          {agents.map((agent: AgentAPI) => {
            const IconComponent = AGENT_ICONS[agent.agent_type as AgentType];
            const colorClass = AGENT_COLORS[agent.agent_type as AgentType];

            return (
              <button
                key={agent.id}
                onClick={() => onAgentClick(agent)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-sm font-medium ${colorClass}`}
              >
                <Bot size={18} />
                <span className="flex-1 text-left">{agent.display_name || agent.name}</span>
                {IconComponent && <IconComponent size={14} className="opacity-60" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default AgentSection;
