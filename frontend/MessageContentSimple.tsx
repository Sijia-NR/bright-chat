import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MessageContentProps {
  content: string;
  isUser?: boolean;
}

const MessageContent: React.FC<MessageContentProps> = ({ content, isUser = false }) => {
  // 检测代码块是否完整（用于流式输出）
  const hasIncompleteCodeBlock = (text: string) => {
    const codeBlocks = text.match(/```(\w*)\n/g);
    const closingBlocks = text.match(/\n```/g);
    return codeBlocks && closingBlocks && codeBlocks.length > closingBlocks.length;
  };

  // 对于流式输出中不完整的代码块，暂时用纯文本显示
  if (hasIncompleteCodeBlock(content)) {
    return (
      <div className="whitespace-pre-wrap break-words font-mono text-sm">
        {content}
      </div>
    );
  }

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        // 代码块渲染（简单版本，无需 react-syntax-highlighter）
        code({ node, inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '');
          const language = match ? match[1] : '';

          if (!inline && language) {
            return (
              <div className="my-3 rounded-lg overflow-hidden bg-[#1e1e1e]">
                <div className="flex items-center justify-between px-4 py-2 bg-[#2d2d2d] text-gray-400 text-xs">
                  <span className="font-medium">{language}</span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(String(children).replace(/\n$/, ''));
                    }}
                    className="hover:text-white transition-colors"
                  >
                    复制
                  </button>
                </div>
                <pre className="p-4 m-0 text-sm leading-relaxed overflow-x-auto">
                  <code className="text-gray-100 font-mono">{children}</code>
                </pre>
              </div>
            );
          }

          // 行内代码
          return (
            <code
              className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-800 font-mono text-sm"
              {...props}
            >
              {children}
            </code>
          );
        },

        // 段落渲染
        p({ children }) {
          return <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>;
        },

        // 列表渲染
        ul({ children }) {
          return <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>;
        },

        ol({ children }) {
          return <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>;
        },

        // 标题渲染
        h1({ children }) {
          return <h1 className="text-xl font-bold mb-3 mt-4">{children}</h1>;
        },

        h2({ children }) {
          return <h2 className="text-lg font-bold mb-3 mt-3">{children}</h2>;
        },

        h3({ children }) {
          return <h3 className="text-base font-bold mb-2 mt-2">{children}</h3>;
        },

        // 强调渲染
        strong({ children }) {
          return <strong className="font-bold">{children}</strong>;
        },

        // 链接渲染
        a({ href, children }) {
          return (
            <a
              href={href}
              className="text-blue-600 hover:text-blue-800 underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              {children}
            </a>
          );
        },

        // 换行渲染
        br() {
          return <br />;
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

export default MessageContent;
