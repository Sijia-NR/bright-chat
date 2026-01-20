
export interface IASMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface IASChatRequest {
  model: string;
  messages: IASMessage[];
  stream?: boolean;
  temperature?: number;
}

export interface IASChoice {
  index: number;
  finish_reason: string | null;
  delta?: {
    role?: string | null;
    content?: string;
  };
  message?: {
    role: string;
    content: string;
  };
}

export interface IASChatResponse {
  id: string;
  appId: string;
  globalTraceId: string;
  object: string;
  created: number;
  choices: IASChoice[];
  usage: any;
}
