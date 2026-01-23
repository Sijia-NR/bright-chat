
import React, { useState, useCallback, useRef, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import ChatInput from './components/ChatInput';
import Login from './components/Login';
import AdminPanel from './components/AdminPanel';
import ConfirmDialog from './components/ConfirmDialog';
import { FavoriteModal } from './components/FavoriteModal';
import { FavoriteButton } from './components/FavoriteButton';
import MessageContent from './MessageContent';
import { Message, ChatSession, User, LLMModel, Agent, AgentType, KnowledgeGroup, KnowledgeBase } from './types';
import { chatService } from './services/chatService';
import { authService } from './services/authService';
import { sessionService } from './services/sessionService';
import { modelService } from './services/modelService';
import { agentService } from './services/agentService';
import { knowledgeService } from './services/knowledgeService';

const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('user');
    return saved ? JSON.parse(saved) : null;
  });
  const [view, setView] = useState<'chat' | 'admin'>('chat');
  const [isFavoritesOpen, setIsFavoritesOpen] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [models, setModels] = useState<LLMModel[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const [savedMessageCount, setSavedMessageCount] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const modelsLoadedRef = useRef(false);

  // 新增状态：Agent 和知识库
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [knowledgeGroups, setKnowledgeGroups] = useState<KnowledgeGroup[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);

  // 刷新模型列表的方法
  const refreshModels = useCallback(async () => {
    try {
      const activeModels = await modelService.getActiveModels();
      setModels(activeModels);

      // 如果当前选中的模型不再活跃列表中，选择第一个
      if (activeModels.length > 0) {
        if (!selectedModelId || !activeModels.find(m => m.name === selectedModelId)) {
          setSelectedModelId(activeModels[0].name);
        }
      }
    } catch (e) {
      console.error("Failed to refresh models", e);
    }
  }, [selectedModelId]);

  const scrollRef = useRef<HTMLDivElement>(null);

  // 加载模型列表（只执行一次）
  useEffect(() => {
    if (modelsLoadedRef.current) return;

    const loadModels = async () => {
      try {
        const activeModels = await modelService.getActiveModels();
        setModels(activeModels);

        // 自动选择第一个可用模型
        if (activeModels.length > 0 && !selectedModelId) {
          setSelectedModelId(activeModels[0].name);
        }
      } catch (e) {
        console.error("Failed to load models", e);
        setModels([]);
      }
    };

    loadModels();
    modelsLoadedRef.current = true;
  }, []);

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
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'auto' });
    }
  }, [messages, isTyping]);

  // 加载 Agents
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const agentList = await agentService.getAgents();
        setAgents(agentList);
      } catch (e) {
        console.error('Failed to load agents', e);
      }
    };
    loadAgents();
  }, []);

  // 加载知识库
  useEffect(() => {
    const loadKnowledge = async () => {
      if (!currentUser) return;
      try {
        const groups = await knowledgeService.getGroups(currentUser.id);
        setKnowledgeGroups(groups);

        const allBases: KnowledgeBase[] = [];
        for (const group of groups) {
          const bases = await knowledgeService.getKnowledgeBases(group.id);
          allBases.push(...bases);
        }
        setKnowledgeBases(allBases);
      } catch (e) {
        console.error('Failed to load knowledge bases', e);
      }
    };
    loadKnowledge();
  }, [currentUser]);

  const handleSendMessage = useCallback(async (text: string) => {
    let currentSessionId = activeSessionId;
    let assistantMsgId: string | null = null;

    // 清除之前的错误消息
    setErrorMessage(null);

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
        assistantMsgId = `assistant-${Date.now()}`;
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
            if (trimmed.startsWith('data:') || trimmed.startsWith('event:data')) {
              // 处理 event:data 格式
              let dataStr = trimmed.replace(/^event:data\s*/i, '').replace('data:', '').trim();
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

        // 检查是否收到了有效内容
        if (!fullContent || fullContent.trim() === '') {
          throw new Error('未收到有效的响应内容');
        }

        // 流式响应完成后，将最终结果保存到后端
        // 即使用户已切换会话，也要保存到原来的会话
        const finalAssistantMsg: Message = { id: assistantMsgId, role: 'assistant', content: fullContent, timestamp: Date.now() };
        await sessionService.saveMessages(currentSessionId, [userMsg, finalAssistantMsg]);
        console.log('[Chat] 流式响应完成，已保存到会话', currentSessionId);
      } else {
        throw new Error('响应体为空，请检查后端服务');
      }
    } catch (error: any) {
      console.error("Chat Error:", error);

      // 立即删除已创建的空 assistant 消息
      if (assistantMsgId) {
        setMessages(prev => prev.filter(m => m.id !== assistantMsgId));
      }

      // 显示错误提示
      const errorMsg = error?.message || '请求失败，请稍后重试';
      setErrorMessage(errorMsg);

      // 3秒后自动隐藏错误提示
      setTimeout(() => setErrorMessage(null), 3000);
    } finally {
      // 确保 isTyping 状态总是被更新
      setIsTyping(false);
    }
  }, [messages, activeSessionId, currentUser, selectedModelId]);

  const onSelectSession = async (id: string) => {
    setView('chat');
    if (activeSessionId === id) return;
    setActiveSessionId(id);
    try {
      const history = await sessionService.getMessages(id);
      setMessages(history);
      setSavedMessageCount(history.length);  // 重置已保存消息计数
    } catch (e) {
      console.error("Failed to load messages", e);
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
    setView('chat');  // 登录后总是进入聊天页面
  };

  const handleLogout = async () => {
    await authService.logout();
    setCurrentUser(null);
    setActiveSessionId(null);
    setMessages([]);
    setSessions([]);
    setSavedMessageCount(0);  // 重置已保存消息计数
    setView('chat');  // 退出后重置视图状态
  };

  const handleNewChat = () => {
    setActiveSessionId(null);
    setMessages([]);
    setSavedMessageCount(0);  // 重置已保存消息计数
    setView('chat');
  };

  // 处理 Agent 点击
  const handleAgentClick = async (agent: Agent) => {
    setSelectedAgent(agent);
    setView('chat');
    setActiveSessionId(null);
    setMessages([]);
    setSavedMessageCount(0);

    if (currentUser) {
      const newSession = await sessionService.createSession(
        `${agent.displayName} 对话`,
        currentUser.id,
        agent.id
      );
      setActiveSessionId(newSession.id);
      const updatedList = await sessionService.getSessions(currentUser.id);
      setSessions(updatedList);
    }
  };

  // 处理知识库刷新
  const refreshKnowledge = async () => {
    if (!currentUser) return;
    try {
      const groups = await knowledgeService.getGroups(currentUser.id);
      setKnowledgeGroups(groups);

      const allBases: KnowledgeBase[] = [];
      for (const group of groups) {
        const bases = await knowledgeService.getKnowledgeBases(group.id);
        allBases.push(...bases);
      }
      setKnowledgeBases(allBases);
    } catch (e) {
      console.error('Failed to refresh knowledge', e);
    }
  };

  // 处理知识库分组操作
  const handleCreateKnowledgeGroup = async (name: string, description?: string) => {
    if (!currentUser) return;
    await knowledgeService.createGroup(currentUser.id, name, description);
    await refreshKnowledge();
  };

  const handleUpdateKnowledgeGroup = async (id: string, name: string, description?: string) => {
    await knowledgeService.updateGroup(id, name, description);
    await refreshKnowledge();
  };

  const handleDeleteKnowledgeGroup = async (id: string) => {
    await knowledgeService.deleteGroup(id);
    await refreshKnowledge();
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
        agents={agents}
        selectedAgent={selectedAgent}
        onAgentClick={handleAgentClick}
        knowledgeGroups={knowledgeGroups}
        knowledgeBases={knowledgeBases}
        onKnowledgeRefresh={refreshKnowledge}
        onCreateKnowledgeGroup={handleCreateKnowledgeGroup}
        onUpdateKnowledgeGroup={handleUpdateKnowledgeGroup}
        onDeleteKnowledgeGroup={handleDeleteKnowledgeGroup}
      />
      <main className="flex-1 flex flex-col relative overflow-hidden bg-white md:bg-[#F7F7F8]">
        {view === 'admin' ? (
          <AdminPanel currentUser={currentUser} onBack={() => setView('chat')} onModelsChange={refreshModels} />
        ) : (
          <>
            <TopBar
              models={models.map(m => ({
                id: m.name,
                name: m.display_name,
                version: m.model_type
              }))}
              selectedModelId={selectedModelId ?? ''}
              onModelChange={setSelectedModelId}
            />
            <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 md:px-0">
              <div className="max-w-3xl mx-auto py-10 min-h-full flex flex-col">
                {messages.length === 0 ? (
                  <>
                    {models.length === 0 ? (
                      <div className="flex-1 flex flex-col items-center justify-center animate-in fade-in zoom-in-95 duration-1000">
                        <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-6">
                          <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                          </svg>
                        </div>
                        <h2 className="text-2xl font-bold text-gray-700 mb-2">还未配置任何模型</h2>
                        <p className="text-gray-400 mb-6">请联系管理员在系统管理中配置 LLM 模型</p>
                        {currentUser.role === 'admin' && (
                          <button
                            onClick={() => setView('admin')}
                            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold transition-all"
                          >
                            前往配置模型
                          </button>
                        )}
                      </div>
                    ) : (
                      <div className="flex-1 flex flex-col items-center justify-center animate-in fade-in zoom-in-95 duration-1000">
                        <div className="w-24 h-24 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-[32px] mb-8 shadow-2xl flex items-center justify-center">
                          <span className="text-4xl font-black text-white italic">AI</span>
                        </div>
                        <h1 className="text-3xl font-bold text-gray-900 mb-2">AI工作台</h1>
                        <p className="text-gray-400 font-medium">智能协作 · 高效办公</p>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="space-y-8 mb-24">
                    {messages.map(m => (
                      <div key={m.id} className={`flex gap-4 md:gap-6 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
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
                    {/* 错误提示 */}
                    {errorMessage && (
                      <div className="flex gap-4 md:gap-6 animate-in slide-in-from-bottom-2">
                        <div className="w-9 h-9 rounded-xl bg-red-500 flex items-center justify-center text-white font-bold">!</div>
                        <div className="bg-red-50 border border-red-200 px-6 py-4 rounded-2xl shadow-sm max-w-[85%]">
                          <p className="text-red-700 text-[15px]">{errorMessage}</p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
            <ChatInput onSend={handleSendMessage} disabled={isTyping || models.length === 0 || !selectedModelId} />
          </>
        )}
      </main>

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
