
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
import KnowledgeBaseDetail from './components/KnowledgeBaseDetail';
import { Message, ChatSession, User, LLMModel, Agent, AgentAPI, AgentType, KnowledgeGroup, KnowledgeBase } from './types';
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
  const [view, setView] = useState<'chat' | 'admin' | 'knowledge'>('chat');
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
  const [agents, setAgents] = useState<AgentAPI[]>([]);  // AgentAPI 用于管理面板
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);  // Agent 用于聊天
  const [agentRefreshTrigger, setAgentRefreshTrigger] = useState(0);
  const [isAgentLoading, setIsAgentLoading] = useState(false);  // Agent 加载状态
  const [agentReady, setAgentReady] = useState(false);  // Agent 就绪状态
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);  // ✅ 只需要知识库列表
  const [selectedKnowledgeBaseId, setSelectedKnowledgeBaseId] = useState<string | null>(null);  // ✅ 选中的知识库

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

  // 加载 Agents（监听 refreshTrigger 以实现同步刷新）
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
  }, [agentRefreshTrigger]);

  // 加载知识库
  useEffect(() => {
    const loadKnowledge = async () => {
      if (!currentUser) return;
      try {
        // ✅ 直接加载所有知识库，不需要分组
        const bases = await knowledgeService.getKnowledgeBases();
        setKnowledgeBases(bases);
      } catch (e) {
        console.error('Failed to load knowledge bases', e);
      }
    };
    loadKnowledge();
  }, [currentUser]);

  const handleSendMessage = useCallback(async (text: string) => {
    let currentSessionId = activeSessionId;
    let assistantMsgId: string | null = null;

    // ✅ 检查 Agent 是否加载完成
    if (selectedAgent && !agentReady) {
      const errorMsg = 'Agent 正在加载，请稍候...';
      setErrorMessage(errorMsg);
      setTimeout(() => setErrorMessage(null), 2000);
      return;
    }

    // 清除之前的错误消息
    setErrorMessage(null);

    // 如果没有会话，创建新会话（延迟创建会话策略）
    if (!currentSessionId && currentUser) {
      let sessionTitle = text;
      let agentId = selectedAgent?.id;

      // 如果是 Agent 对话，使用 Agent 名称作为标题
      if (selectedAgent) {
        sessionTitle = `${selectedAgent.displayName} 对话`;
      }

      const newSession = await sessionService.createSession(
        sessionTitle,
        currentUser.id,
        agentId  // 传入 agentId 以区分 Agent 会话和普通会话
      );
      currentSessionId = newSession.id;
      setActiveSessionId(currentSessionId);
      const updatedList = await sessionService.getSessions(currentUser.id);
      setSessions(updatedList);
      console.log('[Session] 创建新会话:', { sessionTitle, agentId, sessionId: currentSessionId });
    }

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: text, timestamp: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setIsTyping(true);

    try {
      // 判断使用Agent对话还是普通模型对话
      if (selectedAgent) {
        console.log('[Chat] 使用 Agent 对话模式:', selectedAgent.name);

        // 使用Agent对话
        assistantMsgId = `assistant-${Date.now()}`;
        setMessages(prev => [...prev, { id: assistantMsgId, role: 'assistant', content: '', timestamp: Date.now() }]);

        let fullContent = "";
        const eventGenerator = await agentService.agentChat(selectedAgent.id, {
          query: text,  // 关键：使用query字段
          session_id: currentSessionId || undefined,
          stream: true
        });

        for await (const event of eventGenerator) {
          console.log('[Chat] Agent 事件:', event);

          // 处理后端实际发送的事件类型
          if (event.type === 'start') {
            console.log('[Chat] Agent 开始执行:', event.execution_id);
          } else if (event.type === 'step') {
            // 步骤事件：显示执行进度
            const node = event.node || 'unknown';
            const step = event.step || 0;
            const state = event.state || {};

            console.log('[Chat] Agent 步骤:', { node, step, state });

            // 如果状态有输出，显示临时内容
            if (state.output) {
              fullContent = state.output;
              setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, content: fullContent } : m));
            }
          } else if (event.type === 'tool_call') {
            // 工具调用事件：显示工具执行结果
            const tool = event.tool || 'unknown';
            const result = event.result;

            console.log('[Chat] Agent 工具调用:', { tool, result });

            // 将工具结果显示在聊天中
            if (result) {
              const toolOutput = typeof result === 'string' ? result : JSON.stringify(result, null, 2);
              fullContent += `\n\n🔧 工具 [${tool}] 执行结果:\n${toolOutput}`;
              setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, content: fullContent } : m));
            }
          } else if (event.type === 'complete' && event.output) {
            // 完成事件：显示最终输出
            fullContent = event.output;
            setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, content: fullContent } : m));
            console.log('[Chat] Agent 执行完成, 输出长度:', fullContent.length);
          } else if (event.type === 'error') {
            // 错误事件
            const errorMsg = event.error || 'Agent 执行出错';
            fullContent = `❌ 错误: ${errorMsg}`;
            setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, content: fullContent } : m));
            console.error('[Chat] Agent 错误:', errorMsg);
            throw new Error(errorMsg);
          }
        }

        // 保存到后端
        const finalAssistantMsg: Message = { id: assistantMsgId, role: 'assistant', content: fullContent, timestamp: Date.now() };
        await sessionService.saveMessages(currentSessionId, [userMsg, finalAssistantMsg]);

        return;
      }

      // 普通模型对话
      console.log('[Chat] 使用普通模型对话模式, 模型:', selectedModelId);
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
  }, [messages, activeSessionId, currentUser, selectedModelId, selectedAgent, agentReady]);  // ✅ 添加 agentReady

  const onSelectSession = async (id: string) => {
    console.log('[Session] onSelectSession 开始:', { sessionId: id, currentAgentsCount: agents.length });
    setView('chat');
    if (activeSessionId === id) return;
    setActiveSessionId(id);

    // ✅ 开始加载 Agent 时设置状态
    setIsAgentLoading(false);  // 先重置
    setAgentReady(false);  // ✅ 标记为未就绪

    // 查找会话以获取关联的 Agent
    const session = sessions.find(s => s.id === id);
    console.log('[Session] 找到的会话:', session);

    if (session?.agentId) {
      console.log('[Session] 会话关联的 Agent ID:', session.agentId);
      setIsAgentLoading(true);  // ✅ 开始加载

      // 先尝试从已加载的 agents 中查找
      let agentApi = agents.find(a => a.id === session.agentId);

      // 如果找不到，重新加载 agents 列表后再查找
      if (!agentApi) {
        console.warn('[Session] Agent 未在缓存中找到，重新加载...');
        try {
          const agentList = await agentService.getAgents();
          setAgents(agentList);
          agentApi = agentList.find(a => a.id === session.agentId);
          console.log('[Session] 重新加载后找到的 Agent:', agentApi);
        } catch (e) {
          console.error('[Session] 加载 Agent 列表失败:', e);
        }
      }

      if (agentApi) {
        console.log('[Session] ✅ 恢复 Agent 会话:', agentApi.display_name || agentApi.name);
        // 将 AgentAPI 转换为 Agent
        const agent: Agent = {
          id: agentApi.id,
          name: agentApi.name,
          displayName: agentApi.display_name || agentApi.name,
          description: agentApi.description || '',
          type: agentApi.agent_type as AgentType,
          systemPrompt: agentApi.system_prompt || undefined,
          isActive: agentApi.is_active,
          createdAt: new Date(agentApi.created_at).getTime(),
          order: 0
        };
        setSelectedAgent(agent);
        setAgentReady(true);  // ✅ 标记为就绪
      } else {
        console.warn('[Session] ❌ Agent 未找到:', session.agentId);
        setSelectedAgent(null);
        setAgentReady(true);  // ✅ 即使失败也标记为就绪（允许普通对话）
      }
      setIsAgentLoading(false);  // ✅ 加载完成
    } else {
      // 普通会话，清除 Agent 状态
      console.log('[Session] 普通会话，清除 Agent 状态');
      setSelectedAgent(null);
      setAgentReady(true);  // ✅ 普通会话不需要加载，直接就绪
    }

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
    setSavedMessageCount(0);
    setSelectedAgent(null);  // ✅ 清除智能体状态，进入模型服务对话模式
    setAgentReady(true);  // ✅ 新对话不需要加载 Agent
    setIsAgentLoading(false);
    setView('chat');
  };

  // 处理 Agent 点击（从 Sidebar 传递 AgentAPI）
  const handleAgentClick = async (agentApi: AgentAPI) => {
    // 将 AgentAPI 转换为 Agent（用于聊天）
    const agent: Agent = {
      id: agentApi.id,
      name: agentApi.name,
      displayName: agentApi.display_name || agentApi.name,
      description: agentApi.description || '',
      type: agentApi.agent_type as AgentType,
      systemPrompt: agentApi.system_prompt || undefined,
      isActive: agentApi.is_active,
      createdAt: new Date(agentApi.created_at).getTime(),
      order: 0
    };

    setSelectedAgent(agent);
    setAgentReady(true);  // ✅ 从侧边栏选择的 Agent 立即可用
    setIsAgentLoading(false);
    setView('chat');
    setActiveSessionId(null);
    setMessages([]);
    setSavedMessageCount(0);
    // ✅ 不立即创建会话，等发送第一条消息时再创建
  };

  // 处理知识库刷新
  const refreshKnowledge = async () => {
    if (!currentUser) return;
    try {
      // ✅ 直接加载所有知识库
      const bases = await knowledgeService.getKnowledgeBases();
      setKnowledgeBases(bases);
    } catch (e) {
      console.error('Failed to refresh knowledge', e);
    }
  };

  // ✅ 处理创建知识库
  const handleCreateKnowledgeBase = async () => {
    if (!currentUser) return;
    try {
      // 弹出输入框
      const name = prompt('请输入知识库名称:');
      if (!name || !name.trim()) return;

      const description = prompt('请输入知识库描述（可选）:');

      // ✅ 调用创建接口（不需要 group_id）
      await knowledgeService.createKnowledgeBase({
        name: name.trim(),
        description: description?.trim() || '',
        user_id: currentUser.id
      });

      // 刷新列表
      await refreshKnowledge();
      alert('知识库创建成功！');
    } catch (e: any) {
      alert('创建知识库失败: ' + e.message);
    }
  };

  // ✅ 处理选择知识库 - 切换到知识库页面视图
  const handleSelectKnowledgeBase = (baseId: string) => {
    setSelectedKnowledgeBaseId(baseId);
    setView('knowledge');  // 切换到知识库页面视图
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
        knowledgeBases={knowledgeBases}
        onKnowledgeRefresh={refreshKnowledge}
        onCreateKnowledgeBase={handleCreateKnowledgeBase}
        onSelectKnowledgeBase={handleSelectKnowledgeBase}
      />
      <main className="flex-1 flex flex-col relative overflow-hidden bg-white md:bg-[#F7F7F8]">
        {view === 'admin' ? (
          <AdminPanel
            currentUser={currentUser}
            onBack={() => setView('chat')}
            onModelsChange={refreshModels}
            onAgentChange={() => setAgentRefreshTrigger(prev => prev + 1)}
          />
        ) : view === 'knowledge' ? (
          <KnowledgeBaseDetail
            baseId={selectedKnowledgeBaseId || ''}
            onClose={() => {
              setSelectedKnowledgeBaseId(null);
              setView('chat');  // 返回聊天视图
            }}
            onSuccess={() => {
              refreshKnowledge();
            }}
          />
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
              selectedAgent={selectedAgent}
            />
            <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 md:px-0">
              <div className="max-w-3xl mx-auto py-10 min-h-full flex flex-col">
                {messages.length === 0 ? (
                  <>
                    {/* Agent 对话的空状态 */}
                    {selectedAgent ? (
                      <div className="flex-1 flex flex-col items-center justify-center animate-in fade-in zoom-in-95 duration-1000">
                        <div className="w-24 h-24 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-[32px] mb-8 shadow-2xl flex items-center justify-center">
                          <span className="text-4xl font-black text-white italic">{selectedAgent.displayName.substring(0, 2)}</span>
                        </div>
                        <h1 className="text-3xl font-bold text-gray-900 mb-2">{selectedAgent.displayName}</h1>
                        <p className="text-gray-400 font-medium mb-4">{selectedAgent.description}</p>
                        <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-full text-sm font-medium">
                          <span>数字员工已就绪</span>
                        </div>
                      </div>
                    ) : models.length === 0 ? (
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
                        <h1 className="text-3xl font-bold text-gray-900 mb-2">新对话</h1>
                        <p className="text-gray-400 font-medium">选择模型开始对话</p>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="space-y-8 mb-24" data-testid="messages-container">
                    {messages.map(m => (
                      <div key={m.id} data-testid={`message-${m.id}`} data-message-role={m.role} className={`flex gap-4 md:gap-6 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
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
                      <div className="flex gap-4 md:gap-6 animate-in slide-in-from-bottom-2" data-testid="error-message">
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
            <ChatInput
              onSend={handleSendMessage}
              disabled={isTyping || isAgentLoading || (selectedAgent ? false : (models.length === 0 || !selectedModelId))}
            />
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
