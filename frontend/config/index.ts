
export const CONFIG = {
  USE_MOCK: false, // 核心开关：true 使用模拟数据，false 连接真实后端
  API_BASE_URL: '/api/v1',  // 使用相对路径，通过 nginx 代理到后端
  IAS_URL: '/lmp-cloud-ias-server/api/llm/chat/completions/V2',
  DEFAULT_MODEL: 'BrightChat-General-v1'
};
