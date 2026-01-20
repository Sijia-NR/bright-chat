
import { CONFIG } from '../config';
import { mockStreamingResponse } from '../mock/chatMock';
import { IASChatRequest } from '../types/ias';

export const chatService = {
  async completions(req: IASChatRequest): Promise<Response> {
    if (CONFIG.USE_MOCK) {
      // 模拟返回 Fetch Response 对象
      const stream = mockStreamingResponse(req.messages[req.messages.length - 1].content);
      return new Response(stream, {
        headers: { 'Content-Type': 'text/event-stream' }
      });
    }

    // 生产环境：真实网络请求
    return fetch(`${CONFIG.API_BASE_URL}${CONFIG.IAS_URL}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify(req)
    });
  },

  // 非流式聊天调用
  async chat(req: IASChatRequest): Promise<any> {
    if (CONFIG.USE_MOCK) {
      // 返回模拟的非流式响应
      return {
        id: 'chatcmpl-mock',
        object: 'chat.completion',
        created: Date.now(),
        model: 'test-model',
        choices: [{
          index: 0,
          message: {
            role: 'assistant',
            content: '这是一个模拟的聊天回复。'
          },
          finish_reason: 'stop'
        }],
        usage: {
          prompt_tokens: 12,
          completion_tokens: 9,
          total_tokens: 21
        }
      };
    }

    const resp = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.IAS_URL}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({
        ...req,
        stream: false // 强制非流式响应
      })
    });

    if (!resp.ok) throw new Error('聊天请求失败');
    return resp.json();
  }
};
