
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
  agentId?: string;              // 关联的 Agent ID
  agentType?: AgentType;         // Agent 类型（用于显示）
}

export interface Agent {
  id: string;
  name: string;
  displayName: string;           // 显示名称（中文）
  description: string;
  type: AgentType;               // Agent 类型
  icon?: string;                 // 图标名称（lucide-react）
  systemPrompt?: string;         // 系统提示词
  isActive: boolean;             // 是否激活
  createdAt: number;
  order: number;                 // 排序顺序
}

// Agent 类型枚举
export enum AgentType {
  TEAM_LEADER = 'team_leader',      // 数字组长
  DATA_ANALYST = 'data_analyst',    // 问数员工
  WRITING_ASSISTANT = 'writing_assistant'  // 写作助手
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

// 知识库分组
export interface KnowledgeGroup {
  id: string;
  userId: string;                // 所属用户
  name: string;
  description?: string;
  order: number;
  createdAt: number;
  updatedAt: number;
  knowledgeBaseCount?: number;   // 该分组下的知识库数量
}

// 知识库项
export interface KnowledgeBase {
  id: string;
  groupId: string;               // 所属分组
  name: string;
  description?: string;
  type: 'file' | 'url' | 'text';
  size?: number;                 // 文件大小（字节）
  url?: string;
  createdAt: number;
  updatedAt: number;
}

// 后端响应类型 - Agent
export interface AgentResponse {
  id: string;
  name: string;
  display_name: string;
  description: string;
  type: string;
  icon: string | null;
  system_prompt: string | null;
  is_active: boolean;
  created_at: string;
  order: number;
}

// 后端响应类型 - 知识库分组
export interface KnowledgeGroupResponse {
  id: string;
  name: string;
  description: string | null;
  order: number;
  created_at: string;
  updated_at: string;
}

// 后端响应类型 - 知识库项
export interface KnowledgeBaseResponse {
  id: string;
  group_id: string;
  name: string;
  description: string | null;
  type: string;
  size: number | null;
  url: string | null;
  created_at: string;
  updated_at: string;
}
