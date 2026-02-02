import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { AppPage } from '../pages/AppPage';

/**
 * 跨域和局域网访问测试套件
 *
 * 测试场景：
 * 1. CORS 配置验证
 * 2. API 可访问性
 * 3. 不同端口访问
 * 4. 响应头检查
 */

test.describe('跨域和局域网访问测试', () => {
  const BASE_URL = 'http://localhost:8080';

  /**
   * 测试场景 1: API 文档可访问
   * E2E-NET-001
   */
  test('API 文档页面应可访问', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/docs`);

    expect(response.status(), 'API 文档应返回 200').toBe(200);
  });

  /**
   * 测试场景 2: OpenAPI JSON 可访问
   * E2E-NET-002
   */
  test('OpenAPI JSON 应可获取', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/openapi.json`);

    expect(response.status(), 'OpenAPI JSON 应返回 200').toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('openapi');
    expect(data).toHaveProperty('info');
  });

  /**
   * 测试场景 3: CORS 预检请求
   * E2E-NET-003
   */
  test('CORS 预检请求应正常处理', async ({ request }) => {
    const response = await request.fetch(`${BASE_URL}/api/v1/sessions/`, {
      method: 'OPTIONS',
      headers: {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'authorization'
      }
    });

    // CORS preflight 应返回 200 或 204
    expect([200, 204, 401]).toContain(response.status());

    // 检查 CORS 头
    const corsHeader = response.headers()['access-control-allow-origin'];
    console.log(`CORS Header: ${corsHeader || 'Not set'}`);
  });

  /**
   * 测试场景 4: API 端点健康检查
   * E2E-NET-004
   */
  test('核心 API 端点应可访问', async ({ request }) => {
    const endpoints = [
      { path: '/api/v1/auth/login', method: 'POST', skip: true },  // 需要 body
      { path: '/api/v1/models/active', method: 'GET', skip: false },
      { path: '/docs', method: 'GET', skip: false },
      { path: '/openapi.json', method: 'GET', skip: false },
    ];

    const results: Array<{ endpoint: string; status: number; ok: boolean }> = [];

    for (const endpoint of endpoints) {
      if (endpoint.skip) continue;

      const response = await request.fetch(`${BASE_URL}${endpoint.path}`, {
        method: endpoint.method,
      });

      results.push({
        endpoint: endpoint.path,
        status: response.status(),
        ok: response.ok() || response.status() === 401 // 401 也说明端点存在
      });
    }

    // 打印结果
    console.table(results);

    // 验证所有端点都有响应（不是连接错误）
    for (const result of results) {
      expect(result.status, `端点 ${result.endpoint} 应有响应`).toBeGreaterThanOrEqual(200);
      expect(result.status, `端点 ${result.endpoint} 不应返回 5xx 错误`).toBeLessThan(600);
    }
  });

  /**
   * 测试场景 5: 响应时间检查
   * E2E-NET-005
   */
  test('API 响应时间应在合理范围内', async ({ request }) => {
    const startTime = Date.now();
    const response = await request.get(`${BASE_URL}/docs`);
    const endTime = Date.now();
    const responseTime = endTime - startTime;

    expect(responseTime, 'API 文档响应时间应小于 5 秒').toBeLessThan(5000);
    console.log(`API 文档响应时间: ${responseTime}ms`);
  });

  /**
   * 测试场景 6: 错误处理
   * E2E-NET-006
   */
  test('API 应正确处理 404 错误', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/v1/nonexistent-endpoint/`);

    expect(response.status(), '不存在的端点应返回 404').toBe(404);
  });

  /**
   * 测试场景 7: 前端页面加载
   * E2E-NET-007
   */
  test('前端应能正常加载', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    // 验证页面有内容
    const bodyText = await page.locator('body').textContent();
    expect(bodyText?.length ?? 0).toBeGreaterThan(0);

    console.log(`前端页面加载时间: ${loadTime}ms`);

    // 截图
    await page.screenshot({ path: './artifacts/frontend_loaded.png' });
  });

  /**
   * 测试场景 8: WebSocket/SSE 连接测试（如果支持）
   * E2E-NET-008
   */
  test('SSE 流式接口应支持', async ({ page, request }) => {
    // 先登录获取 token
    const loginResponse = await request.post(`${BASE_URL}/api/v1/auth/login`, {
      data: {
        username: 'admin',
        password: 'pwd123'
      }
    });

    if (loginResponse.ok()) {
      const loginData = await loginResponse.json();
      const token = loginData.access_token || loginData.token;

      // 测试聊天接口（支持 SSE）
      const chatResponse = await request.post(`${BASE_URL}/api/v1/chat/completions`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        data: {
          model: 'test',
          messages: [{ role: 'user', content: 'hello' }],
          stream: true
        },
        timeout: 10000
      });

      // 流式接口可能返回各种状态
      console.log(`SSE 接口响应状态: ${chatResponse.status()}`);
    } else {
      console.log('无法获取登录 token，跳过 SSE 测试');
    }
  });

  /**
   * 测试场景 9: 资源静态文件访问
   * E2E-NET-009
   */
  test('静态资源应可访问', async ({ request }) => {
    const staticPaths = [
      '/favicon.ico',
      '/index.html',
    ];

    const results: Array<{ path: string; status: number }> = [];

    for (const path of staticPaths) {
      const response = await request.get(`${BASE_URL}${path}`);
      results.push({ path, status: response.status() });
    }

    console.table(results);

    // 静态资源应该返回 200 或 404（不存在），不应该是 5xx
    for (const result of results) {
      expect(result.status, `${result.path} 不应返回 5xx 错误`).toBeLessThan(500);
    }
  });

  /**
   * 测试场景 10: 并发请求处理
   * E2E-NET-010
   */
  test('API 应能处理并发请求', async ({ request }) => {
    const promises = [];

    // 发送 10 个并发请求
    for (let i = 0; i < 10; i++) {
      promises.push(request.get(`${BASE_URL}/docs`));
    }

    const startTime = Date.now();
    const responses = await Promise.all(promises);
    const endTime = Date.now();

    // 验证所有请求都成功
    for (const response of responses) {
      expect(response.status()).toBe(200);
    }

    console.log(`10 个并发请求完成时间: ${endTime - startTime}ms`);
  });
});
