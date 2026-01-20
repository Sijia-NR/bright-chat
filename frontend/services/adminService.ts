
import { CONFIG } from '../config';
import { User } from '../types';

const STORAGE_KEY = 'mock_users_list';

const getInitialUsers = (): User[] => {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) return JSON.parse(stored);
  const defaultUsers: User[] = [
    { id: 'mock-admin-id', username: 'admin', role: 'admin', createdAt: Date.now() },
    { id: 'mock-user-1', username: 'test_user', role: 'user', createdAt: Date.now() - 86400000 }
  ];
  localStorage.setItem(STORAGE_KEY, JSON.stringify(defaultUsers));
  return defaultUsers;
};

export const adminService = {
  async listUsers(): Promise<User[]> {
    if (CONFIG.USE_MOCK) {
      return getInitialUsers();
    }
    const resp = await fetch(`${CONFIG.API_BASE_URL}/admin/users`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });
    if (!resp.ok) throw new Error('获取用户列表失败');
    return resp.json();
  },

  async createUser(userData: { username: string; password: string; role: 'admin' | 'user' }): Promise<User> {
    if (CONFIG.USE_MOCK) {
      const users = getInitialUsers();
      const newUser: User = {
        id: `mock-${Date.now()}`,
        username: userData.username,
        role: userData.role,
        createdAt: Date.now()
      };
      const updated = [newUser, ...users];
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return newUser;
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}/admin/users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify(userData)
    });
    if (!resp.ok) throw new Error('创建用户失败');
    const data = await resp.json();
    return {
      id: data.id,
      username: data.username,
      role: data.role,
      createdAt: new Date(data.created_at).getTime()
    };
  },

  async updateUser(userId: string, userData: { username: string; password: string; role: 'admin' | 'user' }): Promise<User> {
    if (CONFIG.USE_MOCK) {
      const users = getInitialUsers();
      const userIndex = users.findIndex(u => u.id === userId);
      if (userIndex === -1) throw new Error('用户不存在');

      users[userIndex] = {
        ...users[userIndex],
        username: userData.username,
        role: userData.role
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(users));
      return users[userIndex];
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}/admin/users/${userId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify(userData)
    });
    if (!resp.ok) throw new Error('更新用户失败');
    const data = await resp.json();
    return {
      id: data.id,
      username: data.username,
      role: data.role,
      createdAt: new Date(data.created_at).getTime()
    };
  },

  async deleteUser(userId: string): Promise<{ message: string }> {
    if (CONFIG.USE_MOCK) {
      const users = getInitialUsers();
      const updated = users.filter(u => u.id !== userId);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return { message: '用户已删除 (MOCK)' };
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}/admin/users/${userId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });
    if (!resp.ok) throw new Error('删除用户失败');
    return resp.json();
  }
};
