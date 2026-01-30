import React from 'react';
import { Clock, MessageSquare, Trash2, Bot } from 'lucide-react';
import { ChatSession, AgentAPI } from '../../types';

interface SessionTrailSectionProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  isExpanded: boolean;
  onToggle: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  agents: AgentAPI[];  // 新增：接收 Agent 列表
}

const SessionTrailSection: React.FC<SessionTrailSectionProps> = ({
  sessions,
  activeSessionId,
  isExpanded,
  onToggle,
  onSelectSession,
  onDeleteSession,
  agents  // 接收 agents
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
              // 根据 agentId 查找对应的 Agent
              const agent = session.agentId ? agents.find(a => a.id === session.agentId) : null;

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
                    {/* Agent 会话显示机器人图标，普通会话显示消息图标 */}
                    {agent ? (
                      <Bot size={16} className={activeSessionId === session.id ? 'text-blue-500' : 'text-gray-400'} />
                    ) : (
                      <MessageSquare size={16} className={activeSessionId === session.id ? 'text-blue-500' : 'text-gray-400'} />
                    )}

                    <span className="truncate flex-1">{session.title}</span>
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
