import React from 'react';
import { Clock, MessageSquare, Trash2 } from 'lucide-react';
import { ChatSession, AgentType } from '../../types';

interface SessionTrailSectionProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  isExpanded: boolean;
  onToggle: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
}

const AGENT_TYPE_LABELS: Record<AgentType, { text: string; color: string }> = {
  [AgentType.TEAM_LEADER]: { text: '数字组长', color: 'bg-purple-100 text-purple-700' },
  [AgentType.DATA_ANALYST]: { text: '问数员工', color: 'bg-blue-100 text-blue-700' },
  [AgentType.WRITING_ASSISTANT]: { text: '写作助手', color: 'bg-green-100 text-green-700' }
};

const SessionTrailSection: React.FC<SessionTrailSectionProps> = ({
  sessions,
  activeSessionId,
  isExpanded,
  onToggle,
  onSelectSession,
  onDeleteSession
}) => {
  return (
    <div className="flex-1 overflow-y-auto px-3 space-y-1 py-2 custom-scrollbar border-b border-gray-50">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-1 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-4 opacity-60 hover:opacity-100 transition-opacity"
      >
        <span className="flex items-center gap-2">
          <Clock size={12} /> 会话轨迹
        </span>
        {isExpanded ? <span>▼</span> : <span>▶</span>}
      </button>

      {isExpanded && (
        <>
          {sessions.length === 0 ? (
            <div className="px-4 py-10 text-center">
              <div className="w-10 h-10 bg-gray-50 rounded-xl flex items-center justify-center mx-auto mb-3">
                <MessageSquare size={16} className="text-gray-300" />
              </div>
              <p className="text-[11px] text-gray-400 font-medium">暂无对话记录</p>
            </div>
          ) : (
            sessions.map((session: ChatSession) => {
              const agentLabel = session.agentType ? AGENT_TYPE_LABELS[session.agentType] : null;

              return (
                <div
                  key={session.id}
                  className={`group relative w-full flex items-center rounded-xl transition-all mb-0.5 cursor-pointer ${
                    activeSessionId === session.id ? 'bg-blue-50/80 shadow-sm' : 'hover:bg-gray-50'
                  }`}
                  onClick={() => onSelectSession(session.id)}
                >
                  <div className={`flex-1 px-4 py-3 flex items-center gap-3 text-sm truncate ${
                    activeSessionId === session.id ? 'text-blue-600 font-bold' : 'text-gray-600'
                  }`}>
                    <MessageSquare size={16} className={activeSessionId === session.id ? 'text-blue-500' : 'text-gray-400'} />
                    <span className="truncate pr-6">{session.title}</span>

                    {agentLabel && (
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium shrink-0 ${agentLabel.color}`}>
                        {agentLabel.text}
                      </span>
                    )}
                  </div>

                  <button
                    onClick={(e: React.MouseEvent) => {
                      e.stopPropagation();
                      onDeleteSession(session.id);
                    }}
                    className="absolute right-2 p-2 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all hover:bg-red-50 rounded-lg active:scale-90"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              );
            })
          )}
        </>
      )}
    </div>
  );
};

export default SessionTrailSection;
