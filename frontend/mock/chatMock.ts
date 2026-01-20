
import { IASChatResponse } from '../types/ias';

export const mockStreamingResponse = (query: string) => {
  const encoder = new TextEncoder();
  const text = `你好！我是 **BrightChat** 智能助手。

我已成功接收到您的消息：
> "${query}"

当前系统运行在 **完全解耦的前端架构** 下：
1. **展示层 (UI)**：采用 Tailwind CSS 高级定制。
2. **交互层 (Services)**：统一抽象 API 出口。
3. **模拟层 (Mock)**：完美复刻 IAS 规范流式输出。

您可以尝试点击左侧的“用户注册与管理”进入管理后台测试 Mock 数据的 CRUD 逻辑。`;
  
  return new ReadableStream({
    async start(controller) {
      const chunks = text.split('');
      for (let i = 0; i < chunks.length; i++) {
        const payload: IASChatResponse = {
          id: `mock-${Date.now()}`,
          appId: "564866165928038400",
          globalTraceId: `trace-${Math.random().toString(36).substr(2)}`,
          object: "chat.completion.chunk",
          created: Math.floor(Date.now() / 1000),
          choices: [{
            index: 0,
            finish_reason: i === chunks.length - 1 ? "stop" : null,
            delta: { content: chunks[i] }
          }],
          usage: null
        };
        
        const sseData = encoder.encode(`data:${JSON.stringify(payload)}\n\n`);
        controller.enqueue(sseData);
        await new Promise(r => setTimeout(r, 15)); // 稍微加快流式输出速度
      }
      controller.enqueue(encoder.encode('data:[DONE]\n\n'));
      controller.close();
    }
  });
};
