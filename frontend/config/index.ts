
// 动态获取后端地址（支持 localhost 和局域网访问）
const getBackendUrl = () => {
  // 从环境变量读取，或根据当前页面地址推断
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  // 使用当前页面的协议和主机，端口改为 8080
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  return `${protocol}//${hostname}:8080/api/v1`;
};

export const CONFIG = {
  USE_MOCK: false, // 核心开关：true 使用模拟数据，false 连接真实后端
  API_BASE_URL: getBackendUrl(),  // 动态获取后端地址
  IAS_URL: '/lmp-cloud-ias-server/api/llm/chat/completions/V2', // 相对路径，会自动添加到 API_BASE_URL 后面
  DEFAULT_MODEL: 'glm-4-flash' // 使用已配置的模型
};
