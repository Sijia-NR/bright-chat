
import { CONFIG } from '../config';
import { User } from '../types';

export const authService = {
  async login(username: string, password: string): Promise<User> {
    if (CONFIG.USE_MOCK) {
      await new Promise(r => setTimeout(r, 800));
      if (username === 'admin' && password === 'admin123') {
        const user: User = {
          id: 'mock-admin-id',
          username: 'admin',
          role: 'admin',
          createdAt: Date.now()
        };
        localStorage.setItem('auth_token', 'mock-token-123');
        return user;
      }
      throw new Error('用户名或密码错误');
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    if (!resp.ok) throw new Error('登录失败');

    const data = await resp.json();
    // 后端返回的结构包含 token，我们需要存储 token 并返回用户信息
    if (data.token) {
      localStorage.setItem('auth_token', data.token);
    }
    // 后端返回的结构：{ id, username, role, created_at, token }
    return {
      id: data.id,
      username: data.username,
      role: data.role,
      createdAt: new Date(data.created_at).getTime()
    };
  },

  async logout(): Promise<void> {
    if (CONFIG.USE_MOCK) {
      await new Promise(r => setTimeout(r, 300));
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      return;
    }

    try {
      await fetch(`${CONFIG.API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
    } catch (e) {
      console.warn("Logout API call failed, proceeding with local cleanup");
    } finally {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
    }
  }
};
