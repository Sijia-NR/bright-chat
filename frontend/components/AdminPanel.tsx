
import React, { useState, useEffect } from 'react';
import { UserPlus, Users, ArrowLeft, Trash2, Loader2, User as UserIcon, Shield, XCircle, CheckCircle } from 'lucide-react';
import { adminService } from '../services/adminService';
import { User, UserRole } from '../types';

interface AdminPanelProps {
  currentUser: User;
  onBack: () => void;
}

const AdminPanel: React.FC<AdminPanelProps> = ({ currentUser, onBack }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState<UserRole>('user');
  const [loading, setLoading] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  useEffect(() => { loadUsers(); }, []);

  const loadUsers = async () => {
    try {
      const list = await adminService.listUsers();
      setUsers([...list].sort((a, b) => b.createdAt - a.createdAt));
    } catch (e) {
      console.error("Load users failed", e);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      const user = await adminService.createUser({
        username: newUsername,
        password: newPassword,
        role: newRole
      });
      setMessage({ type: 'success', text: '用户创建成功' });
      setNewUsername('');
      setNewPassword('');
      await loadUsers();
    } catch (err) {
      setMessage({ type: 'error', text: '操作失败，请重试' });
    } finally { setLoading(false); }
  };

  const executeDelete = async (userId: string) => {
    setActionLoadingId(userId);
    try {
      await adminService.deleteUser(userId);
      setUsers(prev => prev.filter(u => u.id !== userId));
      setPendingDeleteId(null);
    } catch (err) {
      alert("删除失败");
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <div className="flex-1 bg-[#F7F7F8] overflow-y-auto p-4 md:p-12 animate-in fade-in duration-500">
      <div className="max-w-5xl mx-auto">
        <header className="flex items-center justify-between mb-10">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">系统管理中心</h1>
            <p className="text-sm text-gray-500 mt-1 tracking-tight">管理用户权限与模拟数据库状态</p>
          </div>
          <button 
            onClick={onBack} 
            className="flex items-center gap-2 px-5 py-2.5 bg-white border border-gray-200 rounded-2xl text-gray-600 hover:text-gray-900 hover:shadow-md transition-all active:scale-95"
          >
            <ArrowLeft size={18} />
            <span className="text-sm font-bold">返回对话</span>
          </button>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <section className="lg:col-span-5">
            <div className="bg-white rounded-[32px] p-8 border border-gray-100 shadow-sm sticky top-8">
              <div className="flex items-center gap-3 mb-8">
                <div className="p-3 bg-blue-50 text-blue-600 rounded-2xl">
                  <UserPlus size={24} />
                </div>
                <h2 className="text-lg font-bold text-gray-800">注册新用户</h2>
              </div>
              
              <form onSubmit={handleRegister} className="space-y-6">
                <div>
                  <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">登录账号</label>
                  <input
                    type="text" required value={newUsername} onChange={e => setNewUsername(e.target.value)}
                    placeholder="设置田户名"
                    className="w-full px-5 py-3.5 bg-gray-50 border-2 border-transparent rounded-2xl outline-none focus:border-blue-500 focus:bg-white transition-all text-sm"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">安全密码</label>
                  <input
                    type="password" required value={newPassword} onChange={e => setNewPassword(e.target.value)}
                    placeholder="设置初始密码"
                    className="w-full px-5 py-3.5 bg-gray-50 border-2 border-transparent rounded-2xl outline-none focus:border-blue-500 focus:bg-white transition-all text-sm"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2 block ml-1">分配角色</label>
                  <select 
                    value={newRole} onChange={e => setNewRole(e.target.value as UserRole)}
                    className="w-full px-5 py-3.5 bg-gray-50 border-2 border-transparent rounded-2xl outline-none focus:border-blue-500 focus:bg-white transition-all text-sm appearance-none"
                  >
                    <option value="user">标准用户 (User)</option>
                    <option value="admin">系统管理员 (Admin)</option>
                  </select>
                </div>
                <button 
                  type="submit" disabled={loading} 
                  className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-2xl font-bold shadow-xl shadow-blue-100 transition-all active:scale-[0.98] disabled:opacity-50"
                >
                  {loading ? <Loader2 className="animate-spin mx-auto" size={20} /> : '确认创建账号'}
                </button>
                {message && (
                  <div className={`text-sm p-4 rounded-2xl flex items-center justify-between ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-100' : 'bg-red-50 text-red-700 border border-red-100'}`}>
                    <span className="font-bold">{message.text}</span>
                    <button onClick={() => setMessage(null)}><XCircle size={16} /></button>
                  </div>
                )}
              </form>
            </div>
          </section>

          <section className="lg:col-span-7">
            <div className="bg-white rounded-[32px] p-8 border border-gray-100 shadow-sm min-h-[500px]">
              <div className="flex items-center gap-3 mb-8">
                <div className="p-3 bg-gray-50 text-gray-500 rounded-2xl">
                  <Users size={24} />
                </div>
                <h2 className="text-lg font-bold text-gray-800">用户管理列表</h2>
              </div>
              
              <div className="space-y-4">
                {users.map(user => (
                  <div key={user.id} className="group p-5 border border-gray-50 rounded-2xl flex items-center justify-between hover:bg-gray-50/50 transition-all">
                    <div className="flex items-center gap-4">
                      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-bold text-lg ${user.role === 'admin' ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-400'}`}>
                        {user.username.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-gray-900">{user.username}</span>
                          {user.role === 'admin' && <span className="px-2 py-0.5 bg-blue-600 text-[10px] text-white rounded-lg font-black uppercase">Admin</span>}
                        </div>
                        <div className="text-[11px] text-gray-400 mt-0.5">创建于 {new Date(user.createdAt).toLocaleDateString()}</div>
                      </div>
                    </div>
                    
                    {user.id !== currentUser.id && (
                      <div className="relative">
                        {pendingDeleteId === user.id ? (
                          <div className="flex items-center gap-2 animate-in slide-in-from-right-2">
                             <button onClick={() => setPendingDeleteId(null)} className="text-xs font-bold text-gray-400 hover:text-gray-600">取消</button>
                             <button 
                               onClick={() => executeDelete(user.id)}
                               disabled={actionLoadingId === user.id}
                               className="px-3 py-1.5 bg-red-600 text-white text-xs font-bold rounded-lg hover:bg-red-700 shadow-lg shadow-red-100"
                             >
                               {actionLoadingId === user.id ? <Loader2 size={12} className="animate-spin" /> : '确认删除'}
                             </button>
                          </div>
                        ) : (
                          <button 
                            onClick={() => setPendingDeleteId(user.id)}
                            className="p-2 text-gray-300 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all opacity-0 group-hover:opacity-100"
                          >
                            <Trash2 size={20} />
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;
