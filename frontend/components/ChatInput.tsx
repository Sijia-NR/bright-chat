
import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Send, Brain, Search, Code, Image as ImageIcon, Mic, Presentation, Video, FileText, Database, ChevronUp, Check, X, Info } from 'lucide-react';
import KnowledgeSearchModal from './KnowledgeSearchModal';
import { Agent, KnowledgeBase } from '../types';

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  selectedAgent?: Agent | null;
  knowledgeBases?: KnowledgeBase[];
  selectedKnowledgeBaseIds?: string[];
  onKnowledgeBaseChange?: (ids: string[]) => void;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  disabled,
  selectedAgent,
  knowledgeBases = [],
  selectedKnowledgeBaseIds = [],
  onKnowledgeBaseChange
}) => {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const kbButtonRef = useRef<HTMLButtonElement>(null);
  const kbDropdownRef = useRef<HTMLDivElement>(null);  // ✅ 添加弹出框容器 ref
  const [kbDropdownPosition, setKbDropdownPosition] = useState<{ top: number; left: number } | null>(null);
  const [showKnowledgeSearch, setShowKnowledgeSearch] = useState(false);
  const [showKBDropdown, setShowKBDropdown] = useState(false);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [text]);

  // 计算弹出框位置
  useEffect(() => {
    if (showKBDropdown && kbButtonRef.current) {
      const rect = kbButtonRef.current.getBoundingClientRect();
      setKbDropdownPosition({
        top: rect.top,
        left: rect.left
      });
    } else {
      setKbDropdownPosition(null);
    }
  }, [showKBDropdown]);

  // 点击外部关闭弹出框
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showKBDropdown) {
        const target = event.target as Node;

        // 检查点击是否在按钮内
        const inButton = kbButtonRef.current?.contains(target);

        // 检查点击是否在弹出框内
        const inDropdown = kbDropdownRef.current?.contains(target);

        // 如果既不在按钮也不在弹出框内，则关闭
        if (!inButton && !inDropdown) {
          console.log('[ChatInput] 点击外部，关闭弹出框');
          setShowKBDropdown(false);
        }
      }
    };

    if (showKBDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [showKBDropdown]);

  const handleSend = () => {
    if (text.trim()) {
      onSend(text);
      setText('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 知识库切换逻辑
  const toggleKnowledgeBase = (kbId: string) => {
    console.log('[ChatInput] toggleKnowledgeBase 被调用:', {
      kbId,
      selectedKnowledgeBaseIds,
      hasCallback: !!onKnowledgeBaseChange
    });

    if (!onKnowledgeBaseChange) {
      console.warn('[ChatInput] onKnowledgeBaseChange 回调不存在');
      return;
    }

    const isSelected = selectedKnowledgeBaseIds.includes(kbId);
    let newIds: string[];

    if (isSelected) {
      newIds = selectedKnowledgeBaseIds.filter(id => id !== kbId);
      console.log('[ChatInput] 取消选择知识库:', { kbId, newIds });
    } else {
      newIds = [...selectedKnowledgeBaseIds, kbId];
      console.log('[ChatInput] 选择知识库:', { kbId, newIds });
    }

    onKnowledgeBaseChange(newIds);
    console.log('[ChatInput] 已调用 onKnowledgeBaseChange');
  };

  // 标签配置
  const baseTags = [
    { icon: <Brain size={14} />, label: '深度思考', color: 'hover:text-purple-600 hover:bg-purple-50' },
    { icon: <Search size={14} />, label: '深度研究', color: 'hover:text-blue-600 hover:bg-blue-50' },
    { icon: <Code size={14} />, label: '代码辅助', color: 'hover:text-emerald-600 hover:bg-emerald-50' },
    { icon: <ImageIcon size={14} />, label: '图像理解', color: 'hover:text-amber-600 hover:bg-amber-50' },
  ];

  const shortcuts = [
    { icon: <Mic size={18} />, label: '语音对话' },
    { icon: <Presentation size={18} />, label: '生成PPT' },
    { icon: <Video size={18} />, label: '创作视频' },
    { icon: <FileText size={18} />, label: '阅读文档' },
    { icon: <Database size={18} />, label: '知识库搜索', action: () => setShowKnowledgeSearch(true) },
  ];

  return (
    <div className="w-full max-w-[840px] mx-auto px-4 pb-10 sticky bottom-0 bg-transparent">
      {/* The main input card */}
      <div className="bg-white rounded-[24px] shadow-[0_8px_40px_rgb(0,0,0,0.08)] border border-gray-200 overflow-hidden flex flex-col p-2 transition-shadow hover:shadow-[0_8px_50px_rgb(0,0,0,0,0.12)]">
        {/* Added bg-white and text-gray-800 explicitly here to prevent dark mode issues */}
        <textarea
          ref={textareaRef}
          data-testid="chat-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="向AI助手提问，开始工作..."
          className="w-full resize-none border-none focus:ring-0 p-4 pb-0 text-gray-800 placeholder-gray-400 text-[16px] leading-relaxed max-h-[200px] min-h-[56px] outline-none bg-white"
          disabled={disabled}
        />

        <div className="flex items-center justify-between px-3 py-2 mt-2">
          {/* Tags Row */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {/* 知识库选择器（第一个标签） */}
            {selectedAgent && onKnowledgeBaseChange && (
              <div className="relative">
                <button
                  ref={kbButtonRef}
                  onClick={() => setShowKBDropdown(!showKBDropdown)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[13px] font-medium transition-all border ${
                    selectedKnowledgeBaseIds.length > 0
                      ? 'bg-blue-600 text-white border-blue-600 hover:bg-blue-700 shadow-sm shadow-blue-200'
                      : 'text-gray-500 border-transparent hover:bg-gray-50 hover:border-gray-300'
                  }`}
                >
                  <Database size={14} />
                  <span>
                    {selectedKnowledgeBaseIds.length === 0
                      ? '知识库'
                      : selectedKnowledgeBaseIds.length === 1
                      ? knowledgeBases.find(kb => kb.id === selectedKnowledgeBaseIds[0])?.name || '知识库'
                      : `${selectedKnowledgeBaseIds.length}个知识库`}
                  </span>
                  {/* 选中数量徽章 */}
                  {selectedKnowledgeBaseIds.length > 1 && (
                    <span className="ml-0.5 px-1.5 py-0.5 bg-white/20 rounded-full text-xs font-bold">
                      {selectedKnowledgeBaseIds.length}
                    </span>
                  )}
                  <ChevronUp
                    size={12}
                    className={`transition-transform duration-200 ${
                      showKBDropdown ? 'rotate-180' : ''
                    }`}
                  />
                </button>
              </div>
            )}

            {/* 其他功能标签 */}
            {baseTags.map((tag, idx) => (
              <button
                key={`base-${idx}`}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[13px] font-medium text-gray-500 transition-all border border-transparent ${tag.color} hover:border-current/10`}
              >
                {tag.icon}
                <span>{tag.label}</span>
              </button>
            ))}
          </div>

          {/* Send Button */}
          <button
            data-testid="send-button"
            onClick={handleSend}
            disabled={!text.trim() || disabled}
            className={`flex items-center justify-center w-9 h-9 rounded-full transition-all duration-300 ${
              text.trim()
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-200 hover:bg-blue-700 scale-100'
                : 'bg-gray-50 text-gray-300 scale-95 cursor-not-allowed'
            }`}
          >
            <Send size={18} className={text.trim() ? "translate-x-[0.5px] -translate-y-[0.5px]" : ""} />
          </button>
        </div>
      </div>

      {/* Quick shortcuts below input - 已隐藏 */}
      <div className="hidden">
        {shortcuts.map((item, idx) => (
          <button
            key={idx}
            onClick={(item as any).action ? (item as any).action : undefined}
            className="flex flex-col items-center gap-2.5 group outline-none"
          >
            <div className="w-11 h-11 bg-white rounded-2xl shadow-sm border border-gray-100 flex items-center justify-center text-gray-500 group-hover:text-blue-600 group-hover:border-blue-200 group-hover:bg-blue-50 group-hover:shadow-md transition-all duration-300">
              {item.icon}
            </div>
            <span className="text-[12px] font-medium text-gray-500 group-hover:text-gray-800 transition-colors">{item.label}</span>
          </button>
        ))}
      </div>

      {/* Knowledge Search Modal */}
      {showKnowledgeSearch && (
        <KnowledgeSearchModal onClose={() => setShowKnowledgeSearch(false)} />
      )}

      {/* Knowledge Base Dropdown - 极简主义设计 */}
      {showKBDropdown && kbDropdownPosition && createPortal(
        <div
          ref={kbDropdownRef}  // ✅ 添加 ref
          className="fixed bg-white rounded-xl shadow-lg z-[9999] overflow-hidden animate-in fade-in duration-150"
          style={{
            width: '320px',
            maxHeight: '280px',
            top: `${kbDropdownPosition.top - 8}px`,
            left: `${kbDropdownPosition.left}px`,
            transform: 'translateY(-100%)',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
          }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <h3 className="text-sm font-medium text-gray-600">关联知识库检索</h3>
            <button
              onClick={() => setShowKBDropdown(false)}
              className="w-5 h-5 flex items-center justify-center text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X size={16} strokeWidth={2} />
            </button>
          </div>

          {/* Knowledge Base List */}
          <div className="py-2">
            {knowledgeBases.length === 0 ? (
              <div className="px-4 py-8 text-center">
                <div className="text-sm text-gray-500 mb-1">暂无知识库</div>
                <div className="text-xs text-gray-400">请先创建知识库</div>
              </div>
            ) : (
              <>
                {knowledgeBases.map((kb, index) => {
                  const isSelected = selectedKnowledgeBaseIds.includes(kb.id);
                  // 根据索引分配颜色：蓝、蓝、紫、绿
                  const colorMap = ['blue', 'blue', 'purple', 'green'] as const;
                  const colorIndex = index % 4;
                  const color = colorMap[colorIndex];
                  const colorClasses = {
                    blue: 'bg-blue-500',
                    purple: 'bg-purple-500',
                    green: 'bg-green-500'
                  };

                  return (
                    <button
                      key={kb.id}
                      onClick={() => toggleKnowledgeBase(kb.id)}
                      className={`w-full flex items-center gap-3 px-4 py-3 transition-all duration-200 relative ${
                        isSelected ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'
                      }`}
                    >
                      {/* 选中时的左侧蓝色竖条 */}
                      {isSelected && (
                        <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500"></div>
                      )}

                      {/* Color Indicator */}
                      <div className={`w-2 h-2 rounded-full ${colorClasses[color]} flex-shrink-0`}></div>

                      {/* Content */}
                      <div className="flex-1 min-w-0 text-left">
                        <div className={`text-sm font-medium transition-colors ${
                          isSelected ? 'text-blue-700' : 'text-gray-700'
                        }`}>
                          {kb.name}
                        </div>
                        <div className="text-xs text-gray-400 mt-0.5">
                          {kb.description || `${kb.documentCount || 0} 个相关文档`}
                        </div>
                      </div>

                      {/* Selection Check - 选中时显示蓝色勾选 */}
                      {isSelected && (
                        <div className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center">
                          <Check size={12} className="text-white" strokeWidth={3} />
                        </div>
                      )}
                    </button>
                  );
                })}

                {/* 底部清空按钮 */}
                {selectedKnowledgeBaseIds.length > 0 && (
                  <div className="px-4 py-2 border-t border-gray-100 mt-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onKnowledgeBaseChange([]);
                        setShowKBDropdown(false);
                      }}
                      className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <X size={14} strokeWidth={2} />
                      清空已选知识库
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};

export default ChatInput;
