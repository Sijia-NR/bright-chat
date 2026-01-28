
import React, { useState } from 'react';
import { User as UserIcon, Lock, ArrowRight, ShieldCheck } from 'lucide-react';
import { authService } from '../services/authService';
import { User as UserType } from '../types';

interface LoginProps {
  onLoginSuccess: (user: UserType) => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 前端验证：检查空凭据
    if (!username.trim()) {
      setError('请输入用户名');
      return;
    }

    if (!password.trim()) {
      setError('请输入密码');
      return;
    }

    setError('');
    setLoading(true);

    try {
      // 切换到解耦的 authService
      const user = await authService.login(username, password);
      onLoginSuccess(user);
    } catch (err: any) {
      setError(err.message || '登录失败，请检查凭据');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#F7F7F8] flex items-center justify-center p-4">
      <div className="w-full max-w-md animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="bg-white rounded-[32px] shadow-[0_20px_60px_-15px_rgba(0,0,0,0.1)] border border-gray-100 overflow-hidden">
          <div className="p-8 pt-12 text-center">
            <div className="w-16 h-16 bg-gradient-to-tr from-blue-500 to-blue-700 rounded-2xl mx-auto flex items-center justify-center shadow-xl shadow-blue-100 mb-6">
              <span className="text-2xl font-bold text-white">AI</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">AI工作台</h1>
            <p className="text-gray-500 text-sm">请输入您的凭据以访问系统 (默认账号: admin / pwd123)</p>
          </div>

          <form onSubmit={handleSubmit} className="p-8 pt-0 space-y-5">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-gray-500 ml-1">用户名</label>
              <div className="relative group">
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors">
                  <UserIcon size={18} />
                </div>
                <input
                  data-testid="username-input"
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-100 rounded-2xl outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 focus:bg-white transition-all text-gray-800"
                  placeholder="admin"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-gray-500 ml-1">密码</label>
              <div className="relative group">
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors">
                  <Lock size={18} />
                </div>
                <input
                  data-testid="password-input"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-100 rounded-2xl outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 focus:bg-white transition-all text-gray-800"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {error && (
              <div className="text-red-500 text-xs text-center font-medium bg-red-50 py-2 rounded-lg">
                {error}
              </div>
            )}

            <button
              data-testid="login-button"
              type="submit"
              disabled={loading}
              className="w-full py-4 bg-gray-900 hover:bg-black text-white rounded-2xl font-bold flex items-center justify-center gap-2 transition-all active:scale-[0.98] disabled:opacity-50"
            >
              {loading ? '正在验证...' : '登录系统'}
              {!loading && <ArrowRight size={18} />}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
