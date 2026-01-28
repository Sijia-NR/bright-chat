import React, { useState, useEffect } from 'react';
import { Plus, Star, LogOut, Settings } from 'lucide-react';
import { ChatSession, User, Agent, KnowledgeGroup, KnowledgeBase } from '../types';
import AgentSection from './sidebar/AgentSection';
import KnowledgeSection from './sidebar/KnowledgeSection';
import SessionTrailSection from './sidebar/SessionTrailSection';
import KnowledgeModal from './sidebar/KnowledgeModal';

interface SidebarSectionState {
  agents: boolean;
  knowledge: boolean;
  sessions: boolean;
}

interface SidebarProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onNewChat: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  currentUser: User;
  onLogout: () => void;
  onOpenAdmin: () => void;
  onOpenFavorites: () => void;
  // 新增 props
  agents: Agent[];
  selectedAgent: Agent | null;
  onAgentClick: (agent: Agent) => void;
  knowledgeGroups: KnowledgeGroup[];
  knowledgeBases: KnowledgeBase[];
  onKnowledgeRefresh: () => void;
  onCreateKnowledgeGroup: (name: string, description?: string) => Promise<void>;
  onUpdateKnowledgeGroup: (id: string, name: string, description?: string) => Promise<void>;
  onDeleteKnowledgeGroup: (id: string) => Promise<void>;
}

const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  currentUser,
  onLogout,
  onOpenAdmin,
  onOpenFavorites,
  agents,
  selectedAgent,
  onAgentClick,
  knowledgeGroups,
  knowledgeBases,
  onKnowledgeRefresh,
  onCreateKnowledgeGroup,
  onUpdateKnowledgeGroup,
  onDeleteKnowledgeGroup
}) => {
  const [sections, setSections] = useState<SidebarSectionState>({
    agents: true,
    knowledge: true,
    sessions: true
  });

  const [isKnowledgeModalOpen, setIsKnowledgeModalOpen] = useState(false);

  // 从 localStorage 恢复折叠状态
  useEffect(() => {
    const saved = localStorage.getItem('sidebar_sections');
    if (saved) {
      try {
        setSections(JSON.parse(saved));
      } catch (e) {
        // Ignore parse errors
      }
    }
  }, []);

  // 保存折叠状态
  const toggleSection = (section: keyof SidebarSectionState) => {
    const newSections = { ...sections, [section]: !sections[section] };
    setSections(newSections);
    localStorage.setItem('sidebar_sections', JSON.stringify(newSections));
  };

  return (
    <aside className="w-[260px] h-screen bg-white border-r border-gray-100 flex flex-col transition-all duration-300 z-50">
      {/* 新建对话按钮 */}
      <div className="p-4">
        <button
          data-testid="new-chat-button"
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 py-3 bg-white border-2 border-gray-50 rounded-2xl shadow-sm hover:shadow-md transition-all font-bold text-gray-700 hover:bg-gray-50 group active:scale-[0.98]"
        >
          <Plus size={18} className="text-blue-500 group-hover:scale-125 transition-transform" />
          <span>新对话</span>
        </button>
      </div>

      {/* 数字员工模块 */}
      <AgentSection
        agents={agents}
        isExpanded={sections.agents}
        onToggle={() => toggleSection('agents')}
        onAgentClick={onAgentClick}
      />

      {/* 个人知识库模块 */}
      <KnowledgeSection
        groups={knowledgeGroups}
        bases={knowledgeBases}
        isExpanded={sections.knowledge}
        onToggle={() => toggleSection('knowledge')}
        onOpenManage={() => setIsKnowledgeModalOpen(true)}
      />

      {/* 会话轨迹模块 */}
      <SessionTrailSection
        sessions={sessions}
        activeSessionId={activeSessionId}
        isExpanded={sections.sessions}
        onToggle={() => toggleSection('sessions')}
        onSelectSession={onSelectSession}
        onDeleteSession={onDeleteSession}
      />

      {/* 收藏的消息入口 */}
      <div className="p-4 border-t border-gray-50">
        <button
          onClick={onOpenFavorites}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-yellow-50 text-gray-600 hover:text-yellow-600 transition-all text-sm font-bold group"
        >
          <Star size={18} className="group-hover:fill-yellow-400 transition-all" />
          <span>收藏的消息</span>
        </button>
      </div>

      {/* 用户信息区域 */}
      <div className="p-4 border-t border-gray-50 space-y-3 bg-white" data-testid="user-info-section">
        <div className="flex items-center gap-3 p-2">
          <div className={`w-11 h-11 rounded-xl flex items-center justify-center font-black shadow-sm text-base ${
            currentUser.role === 'admin' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-white'
          }`}>
            {currentUser.username.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 overflow-hidden">
            <div className="text-sm font-bold text-gray-900 truncate" data-testid="current-username">{currentUser.username}</div>
            <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{currentUser.role}</div>
          </div>

          {currentUser.role === 'admin' && (
            <button
              data-testid="admin-panel-button"
              onClick={onOpenAdmin}
              className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all"
              title="系统管理"
            >
              <Settings size={18} />
            </button>
          )}
        </div>

        <button
          data-testid="logout-button"
          onClick={onLogout}
          className="w-full flex items-center justify-center gap-2 py-3 text-xs font-bold text-gray-400 hover:text-red-500 transition-all border-2 border-transparent hover:border-red-50 hover:bg-red-50/50 rounded-2xl"
        >
          <LogOut size={14} />
          <span>退出登录</span>
        </button>
      </div>

      {/* 知识库管理弹窗 */}
      <KnowledgeModal
        isOpen={isKnowledgeModalOpen}
        onClose={() => {
          setIsKnowledgeModalOpen(false);
          onKnowledgeRefresh();
        }}
        groups={knowledgeGroups}
        bases={knowledgeBases}
        onCreateGroup={onCreateKnowledgeGroup}
        onUpdateGroup={onUpdateKnowledgeGroup}
        onDeleteGroup={onDeleteKnowledgeGroup}
      />
    </aside>
  );
};

export default Sidebar;
