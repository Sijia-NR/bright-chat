
import React, { useState, useCallback, useRef, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import ChatInput from './components/ChatInput';
import Login from './components/Login';
import AdminPanel from './components/AdminPanel';
import SettingsModal from './components/SettingsModal';
import ConfirmDialog from './components/ConfirmDialog';
import { FavoriteModal } from './components/FavoriteModal';
import { FavoriteButton } from './components/FavoriteButton';
import MessageContent from './MessageContent';
import { Message, ChatSession, User } from './types';
import { chatService } from './services/chatService';
import { authService } from './services/authService';
import { sessionService } from './services/sessionService';
import { CONFIG } from './config';

const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('user');
    return saved ? JSON.parse(saved) : null;
  });
  const [view, setView] = useState<'chat' | 'admin'>('chat');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isFavoritesOpen, setIsFavoritesOpen] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>(CONFIG.DEFAULT_MODEL);
  const [isTyping, setIsTyping] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const [savedMessageCount, setSavedMessageCount] = useState(0);
  
  const scrollRef = useRef<HTMLDivElement>(null);

  const refreshSessions = useCallback(async () => {
    if (currentUser) {
      const list = await sessionService.getSessions(currentUser.id);
      setSessions(list);
    }
  }, [currentUser]);

  useEffect(() => { refreshSessions(); }, [refreshSessions]);

  useEffect(() => {
    if (activeSessionId && messages.length > savedMessageCount) {
      const timer = setTimeout(() => {
        // 只保存新增的消息
        const newMessages = messages.slice(savedMessageCount);
        sessionService.saveMessages(activeSessionId, newMessages);
        setSavedMessageCount(messages.length);
      }, 1000); // 1秒防抖

      return () => clearTimeout(timer);
    }
  }, [messages, activeSessionId, savedMessageCount]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages, isTyping]);

  const handleSendMessage = useCallback(async (text: string) => {
    let currentSessionId = activeSessionId;

    if (!currentSessionId && currentUser) {
      const newSession = await sessionService.createSession(text, currentUser.id);
      currentSessionId = newSession.id;
      setActiveSessionId(currentSessionId);
      const updatedList = await sessionService.getSessions(currentUser.id);
      setSessions(updatedList);
    }

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: text, timestamp: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const response = await chatService.completions({
        model: selectedModelId,
        messages: [...messages, userMsg].map(m => ({ role: m.role as any, content: m.content })),
        stream: true
      });

      if (response.body) {
        const assistantMsgId = `assistant-${Date.now()}`;
        setMessages(prev => [...prev, { id: assistantMsgId, role: 'assistant', content: '', timestamp: Date.now() }]);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('data:')) {
              const dataStr = trimmed.replace('data:', '').trim();
              if (dataStr === '[DONE]') break;
              try {
                const data = JSON.parse(dataStr);
                fullContent += data.choices[0]?.delta?.content || "";
                // 更新消息内容
                setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, content: fullContent } : m));
              } catch (e) {}
            }
          }
        }

        // 流式响应完成后，将最终结果保存到后端
        // 即使用户已切换会话，也要保存到原来的会话
        const finalAssistantMsg: Message = { id: assistantMsgId, role: 'assistant', content: fullContent, timestamp: Date.now() };
        await sessionService.saveMessages(currentSessionId, [userMsg, finalAssistantMsg]);
        console.log('[Chat] 流式响应完成，已保存到会话', currentSessionId);
      }
    } catch (error) {
      console.error("Chat Error:", error);
    } finally {
      // 只在用户还在当前会话时更新typing状态
      if (activeSessionId === currentSessionId) {
        setIsTyping(false);
      }
    }
  }, [messages, activeSessionId, currentUser, selectedModelId]);

  const onSelectSession = async (id: string) => {
    setView('chat');
    if (activeSessionId === id) return;
    setIsLoadingMessages(true);
    setActiveSessionId(id);
    try {
      const history = await sessionService.getMessages(id);
      setMessages(history);
      setSavedMessageCount(history.length);  // 重置已保存消息计数
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const confirmDeleteSession = async () => {
    if (!pendingDeleteId) return;
    await sessionService.deleteSession(pendingDeleteId);
    setSessions(prev => prev.filter(s => s.id !== pendingDeleteId));
    if (activeSessionId === pendingDeleteId) {
      setActiveSessionId(null);
      setMessages([]);
    }
    setPendingDeleteId(null);
  };

  const onLogin = (user: User) => {
    setCurrentUser(user);
    localStorage.setItem('user', JSON.stringify(user));
  };

  const handleLogout = async () => {
    await authService.logout();
    setCurrentUser(null);
    setActiveSessionId(null);
    setMessages([]);
    setSessions([]);
    setSavedMessageCount(0);  // 重置已保存消息计数
  };

  const handleNewChat = () => {
    setActiveSessionId(null);
    setMessages([]);
    setSavedMessageCount(0);  // 重置已保存消息计数
    setView('chat');
  };

  if (!currentUser) return <Login onLoginSuccess={onLogin} />;

  return (
    <div className="flex h-screen w-full bg-[#F7F7F8] overflow-hidden text-gray-900">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onNewChat={handleNewChat}
        onSelectSession={onSelectSession}
        onDeleteSession={(id) => setPendingDeleteId(id)}
        currentUser={currentUser}
        onLogout={handleLogout}
        onOpenAdmin={() => setView('admin')}
        onOpenFavorites={() => setIsFavoritesOpen(true)}
        agents={[]}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />
      <main className="flex-1 flex flex-col relative overflow-hidden bg-white md:bg-[#F7F7F8]">
        {view === 'admin' ? (
          <AdminPanel currentUser={currentUser} onBack={() => setView('chat')} />
        ) : (
          <>
            <TopBar
              models={[{id: CONFIG.DEFAULT_MODEL, name: 'BrightChat General', version: 'v2.0'}]}
              selectedModelId={selectedModelId}
              onModelChange={setSelectedModelId}
            />
            <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 md:px-0">
              <div className="max-w-3xl mx-auto py-10 min-h-full flex flex-col">
                {isLoadingMessages ? (
                  <div className="flex-1 flex flex-col items-center justify-center gap-4">
                    <div className="w-12 h-12 border-4 border-blue-50 border-t-blue-600 rounded-full animate-spin"></div>
                    <span className="text-sm font-medium text-gray-400">同步云端历史...</span>
                  </div>
                ) : messages.length === 0 ? (
                  <div className="flex-1 flex flex-col items-center justify-center animate-in fade-in zoom-in-95 duration-1000">
                    <div className="w-24 h-24 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-[32px] mb-8 shadow-2xl flex items-center justify-center">
                      <span className="text-4xl font-black text-white italic">B</span>
                    </div>
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">BrightChat Next-Gen</h1>
                    <p className="text-gray-400 font-medium">高效解耦架构 · 智能交互体验</p>
                  </div>
                ) : (
                  <div className="space-y-8 mb-24">
                    {messages.map(m => (
                      <div key={m.id} className={`flex gap-4 md:gap-6 ${m.role === 'user' ? 'flex-row-reverse' : ''} animate-in slide-in-from-bottom-2 duration-300`}>
                        <div className={`w-9 h-9 rounded-xl shrink-0 flex items-center justify-center text-white font-bold shadow-sm ${m.role === 'user' ? 'bg-gray-800' : 'bg-blue-600'}`}>
                          {m.role === 'user' ? 'U' : 'B'}
                        </div>
                        <div className={`p-4 md:p-5 rounded-2xl max-w-[85%] text-[15px] shadow-sm border ${
                          m.role === 'user' ? 'bg-blue-600 text-white border-blue-500' : 'bg-white border-gray-100 text-gray-800'
                        }`}>
                          {m.role === 'user' ? (
                            <div className="whitespace-pre-wrap break-words">{m.content}</div>
                          ) : (
                            <>
                              <MessageContent content={m.content} />
                              {/* 只为 assistant 消息显示收藏按钮 */}
                              <div className="mt-3">
                                <FavoriteButton messageId={m.id} />
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                    {isTyping && (
                      <div className="flex gap-4 md:gap-6 animate-in slide-in-from-bottom-2">
                        <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold animate-pulse">B</div>
                        <div className="flex items-center gap-1.5 bg-white border border-gray-100 px-6 py-4 rounded-2xl shadow-sm">
                          <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                          <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                          <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce"></span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
            <ChatInput onSend={handleSendMessage} disabled={isTyping} />
          </>
        )}
      </main>

      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} currentUser={currentUser} />
      
      <ConfirmDialog
        isOpen={!!pendingDeleteId}
        title="删除对话"
        message="确定要彻底删除这段对话吗？此操作无法撤销。"
        onConfirm={confirmDeleteSession}
        onCancel={() => setPendingDeleteId(null)}
      />

      <FavoriteModal
        isOpen={isFavoritesOpen}
        onClose={() => setIsFavoritesOpen(false)}
      />
    </div>
  );
};

export default App;
