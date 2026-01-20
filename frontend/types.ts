
export type Role = 'user' | 'assistant' | 'system';
export type UserRole = 'admin' | 'user';

export interface User {
  id: string;
  username: string;
  role: UserRole;
  createdAt: number; // 前端使用的时间戳格式
}

export interface Message {
  id: string;
  role: Role;
  content: string;
  timestamp: number; // 前端使用的时间戳格式
}

export interface ChatSession {
  id: string;
  title: string;
  lastUpdated: number; // 前端使用的时间戳格式
  userId: string;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  icon?: string;
}

export enum ModelType {
  BRIGHT_GENERAL = 'BrightChat General',
  BRIGHT_PRO = 'BrightChat Pro',
  BRIGHT_CODE = 'BrightChat Code',
}

// 后端响应的额外类型定义
export interface LoginResponse {
  id: string;
  username: string;
  role: string;
  created_at: string; // 后端返回的时间字符串格式
  token: string;
}

export interface SessionResponse {
  id: string;
  title: string;
  last_updated: string; // 后端返回的时间字符串格式
  user_id: string;
}

export interface MessageResponse {
  id: string;
  role: string;
  content: string;
  timestamp: string; // 后端返回的时间字符串格式
}

// Favorite 相关类型定义
export interface Favorite {
  id: string;
  message: MessageResponse;
  session: SessionResponse;
  note?: string;
  createdAt: string;
}

export interface FavoriteListResponse {
  favorites: Favorite[];
  total: number;
}

export interface FavoriteStatusResponse {
  is_favorited: boolean;
  favorite_id?: string;
}

export interface FavoriteCreateRequest {
  note?: string;
}

export interface FavoriteResponse {
  id: string;
  messageId: string;
  createdAt: string;
}
