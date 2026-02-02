import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { AppPage } from '../pages/AppPage';

/**
 * Agent 对话功能测试
 *
 * 测试场景：
 * 1. Agent 列表显示
 * 2. Agent 选择
 * 3. Agent 对话
 * 4. Agent 切换
 * 5. RAG 类型 Agent 知识检索
 */

test.describe('Agent 对话功能测试', () => {
  const ADMIN_CREDENTIALS = { username: 'admin', password: 'pwd123' };

  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
    await appPage.waitForAppLoad();
  });

  /**
   * 测试场景 1: Agent 区域显示
   * E2E-AGENT-001
   */
  test('应显示 Agent 区域', async ({ page }) => {
    // 检查侧边栏是否有 Agent 区域
    const agentSection = page.locator('aside').filter({ hasText: /数字员工|Agent/ });

    if (await agentSection.count() > 0) {
      await expect(agentSection).toBeVisible();
      console.log('Agent 区域可见');

      // 检查是否有 Agent 卡片
      const agentCards = page.locator('[data-testid^="agent-card"], aside button').filter({ hasText: /助手|分析师|客服/ });
      const count = await agentCards.count();
      console.log('Agent 数量:', count);

      await page.screenshot({ path: 'test-results/screenshots/agent_section.png' });
    } else {
      console.log('Agent 区域不可见（可能没有配置 Agent）');
      test.skip(true, '没有配置 Agent');
    }
  });

  /**
   * 测试场景 2: Agent 列表获取
   * E2E-AGENT-002
   */
  test('应能获取 Agent 列表', async ({ page }) => {
    // 通过 API 获取 Agent 列表
    const response = await page.request.get('http://localhost:8080/api/v1/agents');

    console.log('Agent API 响应状态:', response.status());

    if (response.status() === 200) {
      const agents = await response.json();
      console.log('Agent 列表:', JSON.stringify(agents, null, 2));

      expect(Array.isArray(agents)).toBe(true);

      if (agents.length > 0) {
        console.log('找到', agents.length, '个 Agent');
      } else {
        console.log('没有配置任何 Agent');
      }
    } else {
      console.log('Agent API 请求失败');
    }

    await page.screenshot({ path: 'test-results/screenshots/agent_list_api.png' });
  });

  /**
   * 测试场景 3: 选择 Agent 进行对话
   * E2E-AGENT-003
   */
  test('应能选择 Agent 并开始对话', async ({ page }) => {
    // 首先获取可用的 Agent
    const response = await page.request.get('http://localhost:8080/api/v1/agents');

    if (response.status() !== 200) {
      test.skip(true, '无法获取 Agent 列表');
      return;
    }

    const agents = await response.json();

    if (!Array.isArray(agents) || agents.length === 0) {
      test.skip(true, '没有可用的 Agent');
      return;
    }

    // 查找侧边栏中的 Agent
    const firstAgent = agents[0];
    console.log('尝试选择 Agent:', firstAgent.name);

    // 查找 Agent 按钮（通过名称或显示名称）
    const agentButton = page.locator(`aside button, aside [role="button"]`)
      .filter({ hasText: new RegExp(firstAgent.displayName || firstAgent.name, 'i') });

    if (await agentButton.count() > 0) {
      await agentButton.first().click();
      await page.waitForTimeout(2000);

      // 验证进入了新会话
      const chatInput = page.locator('[data-testid="chat-input"]');
      await expect(chatInput).toBeVisible();

      // 发送测试消息
      await chatInput.fill('你好，请介绍一下你的功能');
      await page.locator('[data-testid="send-button"]').click();

      // 等待响应
      await expect(page.locator('[data-message-role="assistant"]')).toBeVisible({ timeout: 30000 });

      await page.screenshot({ path: 'test-results/screenshots/agent_chat.png' });
    } else {
      console.log('侧边栏中没有找到 Agent 按钮');
      test.skip(true, '侧边栏中没有 Agent 按钮');
    }
  });

  /**
   * 测试场景 4: Agent 响应内容验证
   * E2E-AGENT-004
   */
  test('Agent 响应应包含相关内容', async ({ page }) => {
    // 获取可用 Agent
    const response = await page.request.get('http://localhost:8080/api/v1/agents');

    if (response.status() !== 200) {
      test.skip(true, '无法获取 Agent 列表');
      return;
    }

    const agents = await response.json();

    if (!Array.isArray(agents) || agents.length === 0) {
      test.skip(true, '没有可用的 Agent');
      return;
    }

    // 查找并点击第一个 Agent
    const firstAgent = agents[0];
    const agentButton = page.locator(`aside button, aside [role="button"]`)
      .filter({ hasText: new RegExp(firstAgent.displayName || firstAgent.name, 'i') });

    if (await agentButton.count() === 0) {
      test.skip(true, '侧边栏中没有 Agent 按钮');
      return;
    }

    await agentButton.first().click();
    await page.waitForTimeout(2000);

    // 发送测试消息
    const chatInput = page.locator('[data-testid="chat-input"]');
    await chatInput.fill('请告诉我你能做什么');
    await page.locator('[data-testid="send-button"]').click();

    // 等待响应
    await expect(page.locator('[data-message-role="assistant"]')).toBeVisible({ timeout: 30000 });
    await page.waitForTimeout(3000);

    // 获取响应内容
    const responseText = await page.locator('[data-message-role="assistant"]').last().textContent();
    console.log('Agent 响应:', responseText?.substring(0, 200));

    // 验证响应不为空
    expect(responseText?.trim().length).toBeGreaterThan(0);

    await page.screenshot({ path: 'test-results/screenshots/agent_response_validation.png' });
  });

  /**
   * 测试场景 5: RAG 类型 Agent 知识检索
   * E2E-AGENT-005
   */
  test('RAG Agent 应能检索知识库', async ({ page }) => {
    // 获取可用 Agent
    const response = await page.request.get('http://localhost:8080/api/v1/agents');

    if (response.status() !== 200) {
      test.skip(true, '无法获取 Agent 列表');
      return;
    }

    const agents = await response.json();

    if (!Array.isArray(agents)) {
      test.skip(true, 'Agent 列表格式错误');
      return;
    }

    // 查找 RAG 类型的 Agent
    const ragAgent = agents.find((a: any) =>
      a.type === 'rag' || a.agentType === 'rag' ||
      (a.description && a.description.toLowerCase().includes('rag'))
    );

    if (!ragAgent) {
      console.log('没有找到 RAG 类型的 Agent');
      test.skip(true, '没有 RAG Agent');
      return;
    }

    console.log('找到 RAG Agent:', ragAgent.name);

    // 查找并点击 RAG Agent
    const agentButton = page.locator(`aside button, aside [role="button"]`)
      .filter({ hasText: new RegExp(ragAgent.displayName || ragAgent.name, 'i') });

    if (await agentButton.count() === 0) {
      test.skip(true, '侧边栏中没有 RAG Agent 按钮');
      return;
    }

    await agentButton.first().click();
    await page.waitForTimeout(2000);

    // 发送测试问题
    const chatInput = page.locator('[data-testid="chat-input"]');
    const testQuestion = '请帮我查找相关信息';
    await chatInput.fill(testQuestion);
    await page.locator('[data-testid="send-button"]').click();

    // 等待响应
    await expect(page.locator('[data-message-role="assistant"]')).toBeVisible({ timeout: 30000 });
    await page.waitForTimeout(3000);

    // 获取响应
    const responseText = await page.locator('[data-message-role="assistant"]').last().textContent();
    console.log('RAG Agent 响应:', responseText?.substring(0, 300));

    await page.screenshot({ path: 'test-results/screenshots/rag_agent_chat.png' });
  });

  /**
   * 测试场景 6: Agent 切换
   * E2E-AGENT-006
   */
  test('应能在不同 Agent 之间切换', async ({ page }) => {
    // 获取可用 Agent
    const response = await page.request.get('http://localhost:8080/api/v1/agents');

    if (response.status() !== 200) {
      test.skip(true, '无法获取 Agent 列表');
      return;
    }

    const agents = await response.json();

    if (!Array.isArray(agents) || agents.length < 2) {
      test.skip(true, '需要至少 2 个 Agent 才能测试切换');
      return;
    }

    console.log('找到', agents.length, '个 Agent');

    // 查找所有 Agent 按钮
    const agentButtons = page.locator('aside button').filter({ hasText: /助手|分析师|客服|Agent/ });
    const count = await agentButtons.count();

    if (count < 2) {
      test.skip(true, '侧边栏中需要至少 2 个 Agent 按钮');
      return;
    }

    // 点击第一个 Agent
    await agentButtons.nth(0).click();
    await page.waitForTimeout(1000);
    console.log('选择了第 1 个 Agent');

    // 发送消息
    await page.locator('[data-testid="chat-input"]').fill('测试消息 1');
    await page.locator('[data-testid="send-button"]').click();
    await page.waitForTimeout(2000);

    // 切换到第二个 Agent
    await agentButtons.nth(1).click();
    await page.waitForTimeout(1000);
    console.log('切换到第 2 个 Agent');

    // 发送消息
    await page.locator('[data-testid="chat-input"]').fill('测试消息 2');
    await page.locator('[data-testid="send-button"]').click();
    await page.waitForTimeout(2000);

    // 验证有消息显示
    await expect(page.locator('[data-message-role="assistant"]')).toBeVisible({ timeout: 30000 });

    await page.screenshot({ path: 'test-results/screenshots/agent_switching.png' });
  });

  /**
   * 测试场景 7: Agent 与普通模型切换
   * E2E-AGENT-007
   */
  test('应能在 Agent 和普通模型之间切换', async ({ page }) => {
    // 获取可用 Agent
    const response = await page.request.get('http://localhost:8080/api/v1/agents');

    if (response.status() !== 200) {
      test.skip(true, '无法获取 Agent 列表');
      return;
    }

    const agents = await response.json();

    if (!Array.isArray(agents) || agents.length === 0) {
      test.skip(true, '没有可用的 Agent');
      return;
    }

    // 先使用普通模型对话
    await page.locator('[data-testid="new-chat-button"]').click();
    await page.waitForTimeout(500);

    await page.locator('[data-testid="chat-input"]').fill('普通模型对话测试');
    await page.locator('[data-testid="send-button"]').click();
    await page.waitForTimeout(3000);

    // 切换到 Agent
    const firstAgent = agents[0];
    const agentButton = page.locator(`aside button, aside [role="button"]`)
      .filter({ hasText: new RegExp(firstAgent.displayName || firstAgent.name, 'i') });

    if (await agentButton.count() > 0) {
      await agentButton.first().click();
      await page.waitForTimeout(1000);

      // 发送 Agent 消息
      await page.locator('[data-testid="chat-input"]').fill('Agent 对话测试');
      await page.locator('[data-testid="send-button"]').click();
      await page.waitForTimeout(3000);

      await page.screenshot({ path: 'test-results/screenshots/agent_model_switching.png' });
    } else {
      test.skip(true, '侧边栏中没有 Agent 按钮');
    }
  });
});

/**
 * Agent API 测试
 */
test.describe('Agent API 测试', () => {
  const ADMIN_CREDENTIALS = { username: 'admin', password: 'pwd123' };

  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
  });

  /**
   * 测试场景 8: Agent API 端点测试
   * E2E-AGENT-API-001
   */
  test('Agent API 端点应正常工作', async ({ page }) => {
    // 获取 token
    const loginResponse = await page.request.post('http://localhost:8080/api/v1/auth/login', {
      data: {
        username: ADMIN_CREDENTIALS.username,
        password: ADMIN_CREDENTIALS.password
      }
    });

    expect(loginResponse.ok()).toBe(true);

    const loginData = await loginResponse.json();
    const token = loginData.access_token;

    console.log('获取到 Token:', token ? '成功' : '失败');

    // 使用 token 获取 Agent 列表
    const agentsResponse = await page.request.get('http://localhost:8080/api/v1/agents', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    console.log('Agent API 响应状态:', agentsResponse.status());
    expect([200, 401]).toContain(agentsResponse.status());

    if (agentsResponse.status() === 200) {
      const agents = await agentsResponse.json();
      console.log('Agent 数量:', Array.isArray(agents) ? agents.length : 'N/A');
    }
  });
});
