
import { CONFIG } from '../config';
import {
  Favorite,
  FavoriteListResponse,
  FavoriteStatusResponse,
  FavoriteCreateRequest,
  FavoriteResponse
} from '../types';

const getToken = () => localStorage.getItem('auth_token');

export const favoriteService = {
  /**
   * 收藏消息
   */
  async addFavorite(messageId: string, note?: string): Promise<FavoriteResponse> {
    const token = getToken();
    if (!token) throw new Error('未登录');

    const body: FavoriteCreateRequest = {};
    if (note) body.note = note;

    const resp = await fetch(`${CONFIG.API_BASE_URL}/messages/${messageId}/favorite`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(body)
    });

    if (!resp.ok) {
      if (resp.status === 404) throw new Error('消息不存在');
      if (resp.status === 400) throw new Error('已经收藏过该消息');
      if (resp.status === 401) throw new Error('未登录');
      throw new Error('收藏失败');
    }

    return await resp.json();
  },

  /**
   * 取消收藏
   */
  async removeFavorite(messageId: string): Promise<{ message: string }> {
    const token = getToken();
    if (!token) throw new Error('未登录');

    const resp = await fetch(`${CONFIG.API_BASE_URL}/messages/${messageId}/favorite`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!resp.ok) {
      if (resp.status === 404) throw new Error('收藏不存在');
      if (resp.status === 401) throw new Error('未登录');
      throw new Error('取消收藏失败');
    }

    return await resp.json();
  },

  /**
   * 获取收藏列表
   */
  async getFavorites(limit = 20, offset = 0): Promise<FavoriteListResponse> {
    const token = getToken();
    if (!token) throw new Error('未登录');

    const resp = await fetch(
      `${CONFIG.API_BASE_URL}/favorites?limit=${limit}&offset=${offset}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );

    if (!resp.ok) {
      if (resp.status === 401) throw new Error('未登录');
      throw new Error('获取收藏列表失败');
    }

    return await resp.json();
  },

  /**
   * 检查消息收藏状态
   */
  async getFavoriteStatus(messageId: string): Promise<FavoriteStatusResponse> {
    const token = getToken();
    if (!token) return { is_favorited: false };

    try {
      const resp = await fetch(
        `${CONFIG.API_BASE_URL}/messages/${messageId}/favorite-status`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!resp.ok) {
        return { is_favorited: false };
      }

      return await resp.json();
    } catch {
      return { is_favorited: false };
    }
  }
};
