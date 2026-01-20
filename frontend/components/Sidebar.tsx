
import React from 'react';
import { Plus, MessageSquare, Settings, Clock, Trash2, ShieldCheck, LogOut, Star } from 'lucide-react';
import { ChatSession, User, Agent } from '../types';

interface SidebarProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onNewChat: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  onOpenSettings: () => void;
  currentUser: User;
  onLogout: () => void;
  onOpenAdmin: () => void;
  onOpenFavorites: () => void;
  agents: Agent[];
}

const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  onOpenSettings,
  currentUser,
  onLogout,
  onOpenAdmin,
  onOpenFavorites,
  agents
}) => {
  return (
    <aside className="w-[260px] h-screen bg-white border-r border-gray-100 flex flex-col transition-all duration-300 z-50">
      <div className="p-4">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 py-3 bg-white border-2 border-gray-50 rounded-2xl shadow-sm hover:shadow-md transition-all font-bold text-gray-700 hover:bg-gray-50 group active:scale-[0.98]"
        >
          <Plus size={18} className="text-blue-500 group-hover:scale-125 transition-transform" />
          <span>新对话</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 space-y-1 py-2 custom-scrollbar">
        <div className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] px-3 mb-4 flex items-center gap-2 opacity-60">
          <Clock size={12} /> 最近对话
        </div>
        
        {sessions.length === 0 ? (
          <div className="px-4 py-10 text-center">
            <div className="w-10 h-10 bg-gray-50 rounded-xl flex items-center justify-center mx-auto mb-3">
               <MessageSquare size={16} className="text-gray-300" />
            </div>
            <p className="text-[11px] text-gray-400 font-medium">暂无对话记录</p>
          </div>
        ) : (
          sessions.map((session) => (
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
              </div>
              
              <button
                onClick={(e) => {
                  e.stopPropagation(); // 阻止冒泡到父级 div 的 onClick
                  onDeleteSession(session.id);
                }}
                className="absolute right-2 p-2 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all hover:bg-red-50 rounded-lg active:scale-90"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))
        )}

        {/* 收藏的消息入口 */}
        <div className="pt-4 mt-4 border-t border-gray-50">
          <button
            onClick={onOpenFavorites}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-yellow-50 text-gray-600 hover:text-yellow-600 transition-all text-sm font-bold group"
          >
            <Star size={18} className="group-hover:fill-yellow-400 transition-all" />
            <span>收藏的消息</span>
          </button>
        </div>

        {currentUser.role === 'admin' && (
          <div className="pt-6 mt-6 border-t border-gray-50">
            <div className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] px-3 mb-4 opacity-60">
              管理选项
            </div>
            <button
              onClick={onOpenAdmin}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-blue-50 text-gray-600 hover:text-blue-600 transition-all text-sm font-bold"
            >
              <ShieldCheck size={18} />
              <span>用户注册与管理</span>
            </button>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-gray-50 space-y-3 bg-white">
        <div 
          onClick={onOpenSettings}
          className="flex items-center gap-3 p-3 rounded-2xl hover:bg-gray-50 cursor-pointer transition-all group border border-transparent hover:border-gray-100"
        >
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-black shadow-sm ${
            currentUser.role === 'admin' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-white'
          }`}>
            {currentUser.username.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 overflow-hidden">
            <div className="text-sm font-bold text-gray-900 truncate">{currentUser.username}</div>
            <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{currentUser.role}</div>
          </div>
          <Settings size={18} className="text-gray-400 group-hover:rotate-90 transition-transform" />
        </div>

        <button 
          onClick={onLogout}
          className="w-full flex items-center justify-center gap-2 py-3 text-xs font-bold text-gray-400 hover:text-red-500 transition-all border-2 border-transparent hover:border-red-50 hover:bg-red-50/50 rounded-2xl"
        >
          <LogOut size={14} />
          <span>退出登录</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
