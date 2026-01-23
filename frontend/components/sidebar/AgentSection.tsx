import React from 'react';
import { ChevronDown, ChevronUp, Crown, BarChart3, PenTool } from 'lucide-react';
import { Agent, AgentType } from '../../types';

interface AgentSectionProps {
  agents: Agent[];
  isExpanded: boolean;
  onToggle: () => void;
  onAgentClick: (agent: Agent) => void;
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
          {agents.map((agent: Agent) => {
            const IconComponent = AGENT_ICONS[agent.type];
            const colorClass = AGENT_COLORS[agent.type];

            return (
              <button
                key={agent.id}
                onClick={() => onAgentClick(agent)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-sm font-medium ${colorClass}`}
              >
                {IconComponent && <IconComponent size={18} />}
                <span>{agent.displayName}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default AgentSection;
