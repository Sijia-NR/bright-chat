
// 动态获取后端地址（支持 localhost、局域网和外网访问）
const getBackendUrl = () => {
  // 开发模式：使用相对路径，由 Vite 代理转发
  // 这样无论从哪个端口访问（3000/9006/19030），API 请求都会被代理到正确的后端端口
  if (import.meta.env.DEV) {
    return '/api/v1';  // 开发模式通过 Vite 代理访问后端
  }

  // 生产模式：从环境变量读取
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }

  // 生产模式默认：使用相对路径（通过 Nginx 反向代理）
  return '/api/v1';
};

export const CONFIG = {
  USE_MOCK: false, // 核心开关：true 使用模拟数据，false 连接真实后端
  // 使用 getter 确保每次访问时都动态获取 URL
  get API_BASE_URL() {
    const url = getBackendUrl();
    console.log('[CONFIG] API_BASE_URL:', url);
    return url;
  },
  IAS_URL: '/lmp-cloud-ias-server/api/llm/chat/completions/V2', // 相对路径，由服务器端代理
  DEFAULT_MODEL: 'glm-4-flash' // 使用已配置的模型
};
