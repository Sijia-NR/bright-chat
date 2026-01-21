
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

// LLM 模型相关类型定义
export type LLMModelType = 'openai' | 'anthropic' | 'custom' | 'ias';

export interface LLMModel {
  id: string;
  name: string;
  display_name: string;
  model_type: LLMModelType;
  api_url: string;
  api_key: string;  // admin 用户可见
  api_version?: string;
  description?: string;
  is_active: boolean;
  max_tokens: number;
  temperature: number;
  stream_supported: boolean;
  created_at: string;
}

export interface LLMModelCreate {
  name: string;
  display_name: string;
  model_type: LLMModelType;
  api_url: string;
  api_key: string;
  api_version?: string;
  description?: string;
  is_active?: boolean;
  max_tokens?: number;
  temperature?: number;
  stream_supported?: boolean;
  custom_headers?: Record<string, string>;
}

export interface LLMModelUpdate {
  display_name?: string;
  api_url?: string;
  api_key?: string;
  api_version?: string;
  description?: string;
  is_active?: boolean;
  max_tokens?: number;
  temperature?: number;
  stream_supported?: boolean;
  custom_headers?: Record<string, string>;
}

export interface LLMModelListResponse {
  models: LLMModel[];
  total: number;
}
