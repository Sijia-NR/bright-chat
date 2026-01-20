
import React, { useState, useRef, useEffect } from 'react';
import { Send, Brain, Search, Code, Image as ImageIcon, Mic, Presentation, Video, FileText } from 'lucide-react';

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSend, disabled }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [text]);

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

  const tags = [
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
  ];

  return (
    <div className="w-full max-w-[840px] mx-auto px-4 pb-10 sticky bottom-0 bg-transparent">
      {/* The main input card */}
      <div className="bg-white rounded-[24px] shadow-[0_8px_40px_rgb(0,0,0,0.08)] border border-gray-200 overflow-hidden flex flex-col p-2 transition-shadow hover:shadow-[0_8px_50px_rgb(0,0,0,0.12)]">
        {/* Added bg-white and text-gray-800 explicitly here to prevent dark mode issues */}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="问问 BrightChat，或者输入 / 触发指令..."
          className="w-full resize-none border-none focus:ring-0 p-4 pb-0 text-gray-800 placeholder-gray-400 text-[16px] leading-relaxed max-h-[200px] min-h-[56px] outline-none bg-white"
          disabled={disabled}
        />
        
        <div className="flex items-center justify-between px-3 py-2 mt-2">
          {/* Functional Tags */}
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar">
            {tags.map((tag, idx) => (
              <button
                key={idx}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[13px] font-medium text-gray-500 transition-all border border-transparent ${tag.color} hover:border-current/10`}
              >
                {tag.icon}
                <span>{tag.label}</span>
              </button>
            ))}
          </div>

          {/* Send Button */}
          <button
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

      {/* Quick shortcuts below input */}
      <div className="flex items-center justify-center gap-10 mt-8 overflow-x-auto py-2">
        {shortcuts.map((item, idx) => (
          <button
            key={idx}
            className="flex flex-col items-center gap-2.5 group outline-none"
          >
            <div className="w-11 h-11 bg-white rounded-2xl shadow-sm border border-gray-100 flex items-center justify-center text-gray-500 group-hover:text-blue-600 group-hover:border-blue-200 group-hover:bg-blue-50 group-hover:shadow-md transition-all duration-300">
              {item.icon}
            </div>
            <span className="text-[12px] font-medium text-gray-500 group-hover:text-gray-800 transition-colors">{item.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default ChatInput;
