
import React, { useState } from 'react';
import { X, Palette, Info, ShieldCheck, Sliders, Trash2, RefreshCw, AlertTriangle } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: any;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose, currentUser }) => {
  const [activeTab, setActiveTab] = useState<'general' | 'about'>('general');
  const [resetStep, setResetStep] = useState<0 | 1 | 2>(0); // 0: 初始, 1: 确认中, 2: 已执行

  if (!isOpen) return null;

  const handleResetData = () => {
    if (resetStep === 0) {
      setResetStep(1);
    } else if (resetStep === 1) {
      setResetStep(2);
      setTimeout(() => {
        localStorage.clear();
        window.location.reload();
      }, 800);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white w-full max-w-2xl rounded-[32px] shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-300">
        <div className="flex items-center justify-between px-8 py-6 border-b border-gray-100">
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Sliders size={20} className="text-blue-600" />
            系统设置
          </h2>
          <button 
            onClick={() => { onClose(); setResetStep(0); }} 
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X size={20} className="text-gray-400" />
          </button>
        </div>

        <div className="flex-1 flex overflow-hidden min-h-[400px]">
          {/* 左侧导航 - 仅保留 2 个选项卡 */}
          <nav className="w-48 bg-gray-50/50 border-r border-gray-100 p-4 space-y-1">
            {[
              { id: 'general', icon: <Palette size={18} />, label: '常规设置' },
              { id: 'about', icon: <Info size={18} />, label: '关于系统' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => { setActiveTab(tab.id as any); setResetStep(0); }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  activeTab === tab.id ? 'bg-white text-blue-600 shadow-sm border border-gray-100' : 'text-gray-500 hover:bg-gray-100'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </nav>

          {/* 右侧内容 */}
          <div className="flex-1 p-8 overflow-y-auto bg-white">
            {activeTab === 'general' && (
              <div className="space-y-8 animate-in slide-in-from-right-4 duration-300">
                <section>
                  <label className="text-xs font-black text-gray-400 uppercase tracking-[0.2em] block mb-5">系统维护</label>
                  <div className={`p-6 rounded-[24px] border transition-all ${
                    resetStep === 1 ? 'bg-red-50 border-red-100' : 'bg-gray-50 border-gray-100'
                  }`}>
                    <div className="flex items-start gap-4 mb-4">
                      <div className={`p-3 rounded-2xl ${resetStep === 1 ? 'bg-white text-red-500 shadow-sm' : 'bg-white text-gray-400 shadow-sm'}`}>
                        {resetStep === 1 ? <AlertTriangle size={20} /> : <Trash2 size={20} />}
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-gray-900">重置本地数据</h4>
                        <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                          这将永久清除您在此浏览器中的所有聊天记录、用户名单和登录状态。
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <button 
                        onClick={handleResetData}
                        disabled={resetStep === 2}
                        className={`px-5 py-2.5 rounded-xl text-xs font-bold transition-all active:scale-95 flex items-center gap-2 ${
                          resetStep === 0 ? 'bg-white border border-gray-200 text-gray-600 hover:border-red-200 hover:text-red-500' :
                          resetStep === 1 ? 'bg-red-600 text-white shadow-lg shadow-red-100 hover:bg-red-700' :
                          'bg-gray-100 text-gray-400 cursor-not-allowed'
                        }`}
                      >
                        {resetStep === 2 ? <RefreshCw size={14} className="animate-spin" /> : null}
                        {resetStep === 0 ? '立即重置' : resetStep === 1 ? '确定要重置吗？' : '正在重启系统...'}
                      </button>
                      
                      {resetStep === 1 && (
                        <button 
                          onClick={() => setResetStep(0)}
                          className="px-4 py-2.5 text-xs font-bold text-gray-500 hover:text-gray-800 transition-colors"
                        >
                          取消
                        </button>
                      )}
                    </div>
                  </div>
                </section>

                <section>
                  <label className="text-xs font-black text-gray-400 uppercase tracking-[0.2em] block mb-5">界面交互</label>
                  <div className="flex items-center justify-between p-5 bg-white border border-gray-100 rounded-[24px]">
                    <div>
                      <div className="text-sm font-bold text-gray-800">流式响应输出</div>
                      <div className="text-xs text-gray-400 mt-0.5">实时查看模型生成的每一个字</div>
                    </div>
                    <div className="w-12 h-6 bg-blue-600 rounded-full relative shadow-inner">
                      <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm"></div>
                    </div>
                  </div>
                </section>
              </div>
            )}

            {activeTab === 'about' && (
              <div className="flex flex-col items-center justify-center h-full text-center animate-in slide-in-from-right-4 duration-300">
                <div className="w-20 h-20 bg-blue-50 text-blue-600 rounded-[28px] flex items-center justify-center mb-6 shadow-sm">
                  <ShieldCheck size={40} />
                </div>
                <h3 className="text-xl font-bold text-gray-900 tracking-tight">BrightChat Next-Gen</h3>
                <p className="text-sm text-gray-400 mt-3 max-w-xs leading-relaxed">
                  企业级 AI 交互门户。采用 IAS 规范与三层解耦架构，版本 v2.6.5-stable。
                </p>
                <div className="mt-10 flex gap-3">
                  <button className="px-6 py-2.5 bg-gray-900 text-white rounded-xl text-xs font-bold hover:bg-black transition-all active:scale-95 shadow-lg">检查更新</button>
                  <button className="px-6 py-2.5 border border-gray-200 text-gray-600 rounded-xl text-xs font-bold hover:bg-gray-50 transition-all active:scale-95">技术支持</button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
