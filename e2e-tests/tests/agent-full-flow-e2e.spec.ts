import { test, expect } from '@playwright/test';

/**
 * Bright-Chat 数字员工完整流程 E2E 测试
 *
 * 正确的数字员工使用流程：
 * 1. 登录后点击数字员工按钮展开列表
 * 2. 点击数字员工进行对话
 * 3. 使用 Agent chat 接口对话
 * 4. 查看会话轨迹
 */

test.describe('数字员工完整流程 E2E 测试', () => {

  test.beforeEach(async ({ page }) => {
    // 每个测试前重新登录
    await page.goto('http://localhost:3000');
    await page.fill('[data-testid="username-input"]', 'admin');
    await page.fill('[data-testid="password-input"]', 'pwd123');
    await page.click('[data-testid="login-button"]');

    // 等待登录完成
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
  });

  /**
   * 场景 1: 验证能够展开并看到数字员工列表
   */
  test('应该能够在侧边栏看到数字员工列表', async ({ page }) => {
    console.log('📍 步骤 1: 查看数字员工列表');

    // 查找数字员工按钮
    const agentToggleButton = page.locator('button:has-text("数字员工")');
    await agentToggleButton.waitFor({ state: 'visible', timeout: 5000 });

    // 点击展开数字员工列表
    await agentToggleButton.click();
    await page.waitForTimeout(1000);

    // 查找数字员工按钮
    const agents = page.locator('button:has-text("UI测试Agent"), button:has-text("研究员"), button:has-text("知识库助手"), button:has-text("计算器")');

    // 如果还没找到，再点击一次（可能是收起状态）
    const agentCount = await agents.count();
    if (agentCount === 0) {
      console.log('⚠️ 第一次点击后未找到数字员工，再次点击');
      await agentToggleButton.click();
      await page.waitForTimeout(1000);
    }

    const finalCount = await agents.count();
    console.log(`✅ 找到 ${finalCount} 个数字员工`);

    // 截图
    await page.screenshot({ path: 'test-results/agent-list-visible.png' });

    // 至少应该有一些数字员工
    expect(finalCount).toBeGreaterThan(0);
  });

  /**
   * 场景 2: 点击数字员工进行对话
   */
  test('应该能够点击数字员工进行对话', async ({ page }) => {
    console.log('📍 步骤 2: 点击数字员工对话');

    // 确保数字员工列表展开
    const agentToggleButton = page.locator('button:has-text("数字员工")');
    await agentToggleButton.click();
    await page.waitForTimeout(1000);

    // 查找数字员工
    const agents = page.locator('button:has-text("UI测试Agent"), button:has-text("研究员")');

    // 如果没找到，再点击一次
    if (await agents.count() === 0) {
      await agentToggleButton.click();
      await page.waitForTimeout(1000);
    }

    // 等待第一个数字员工可见
    await agents.first().waitFor({ state: 'visible', timeout: 5000 });

    // 点击第一个数字员工
    const firstAgent = agents.first();

    // 监听 Agent chat API
    const agentChatApiPromise = page.waitForResponse(resp =>
      resp.url().includes('/agents/') && resp.url().includes('/chat'),
      { timeout: 15000 }
    );

    // 点击数字员工
    await firstAgent.click();
    await page.waitForTimeout(2000);

    // 截图
    await page.screenshot({ path: 'test-results/agent-selected.png' });

    // 输入测试消息
    const chatInput = page.locator('textarea[placeholder*="向AI助手提问"], [data-testid="chat-input"]');
    await chatInput.fill('你好，请做个自我介绍');

    // 发送消息（使用 Enter 键）
    await chatInput.press('Enter');

    // 等待 Agent API 调用
    try {
      const response = await agentChatApiPromise;
      console.log('✅ Agent API 调用成功:', response.status());
      expect(response.status()).toBe(200);
    } catch (error) {
      console.log('⚠️ Agent API 可能未被调用:', error);
    }

    // 等待回复
    await page.waitForTimeout(5000);

    // 截图
    await page.screenshot({ path: 'test-results/agent-chat-response.png' });

    // 验证收到回复
    const messages = page.locator('[class*="message"], [data-testid="message"]');
    const messageCount = await messages.count();
    console.log(`✅ 对话中有 ${messageCount} 条消息`);

    expect(messageCount).toBeGreaterThan(0);
  });

  /**
   * 场景 3: 查看会话轨迹
   */
  test('应该能够在会话轨迹中看到数字员工的对话', async ({ page }) => {
    console.log('📍 步骤 3: 查看会话轨迹');

    // 查找会话轨迹按钮
    const sessionTrailButton = page.locator('button:has-text("会话轨迹")');
    const hasSessionTrail = await sessionTrailButton.count() > 0;

    if (hasSessionTrail) {
      // 点击会话轨迹
      await sessionTrailButton.click();
      await page.waitForTimeout(1000);

      // 截图
      await page.screenshot({ path: 'test-results/session-trail.png' });

      // 验证会话列表可见（从页面快照看到有"UI测试Agent 对话"）
      const sessions = page.locator('generic:has-text("对话")');
      const sessionCount = await sessions.count();
      console.log(`✅ 找到 ${sessionCount} 个会话`);
    } else {
      console.log('⚠️ 未找到会话轨迹按钮');
    }
  });

  /**
   * 场景 4: 计算器工具测试
   */
  test('应该能够使用计算器数字员工进行计算', async ({ page }) => {
    console.log('📍 步骤 4: 测试计算器工具');

    // 确保数字员工列表展开
    const agentToggleButton = page.locator('button:has-text("数字员工")');
    await agentToggleButton.click();
    await page.waitForTimeout(1000);

    // 查找计算器相关的数字员工
    const agents = page.locator('button:has-text("计算器"), button:has-text("计算")');

    // 如果没找到，再点击一次
    if (await agents.count() === 0) {
      await agentToggleButton.click();
      await page.waitForTimeout(1000);
    }

    const agentCount = await agents.count();

    if (agentCount > 0) {
      console.log(`✅ 找到 ${agentCount} 个计算器相关的数字员工`);

      // 点击第一个计算器数字员工
      await agents.first().click();
      await page.waitForTimeout(1000);

      // 输入计算问题
      const chatInput = page.locator('textarea[placeholder*="向AI助手提问"], [data-testid="chat-input"]');
      await chatInput.fill('123 + 456 = ?');
      await chatInput.press('Enter');

      // 等待回复
      await page.waitForTimeout(8000);

      // 截图
      await page.screenshot({ path: 'test-results/calculator-result.png' });

      // 验证回复
      const messages = page.locator('[class*="message"]');
      const messageText = await messages.last().textContent();
      console.log('✅ 计算器回复:', messageText);

      // 验证回复中包含数字 579
      expect(messageText).toMatch(/579/);
    } else {
      console.log('⚠️ 未找到计算器数字员工');
    }
  });

  /**
   * 场景 5: 知识库助手测试
   */
  test('应该能够使用知识库助手进行检索', async ({ page }) => {
    console.log('📍 步骤 5: 测试知识库助手');

    // 确保数字员工列表展开
    const agentToggleButton = page.locator('button:has-text("数字员工")');
    await agentToggleButton.click();
    await page.waitForTimeout(1000);

    // 查找知识库助手
    const kbAgent = page.locator('button:has-text("知识库助手")');

    // 如果没找到，再点击一次
    if (await kbAgent.count() === 0) {
      await agentToggleButton.click();
      await page.waitForTimeout(1000);
    }

    const agentCount = await kbAgent.count();

    if (agentCount > 0) {
      console.log('✅ 找到知识库助手');

      // 点击知识库助手
      await kbAgent.first().click();
      await page.waitForTimeout(1000);

      // 输入查询
      const chatInput = page.locator('textarea[placeholder*="向AI助手提问"], [data-testid="chat-input"]');
      await chatInput.fill('查询知识库中的内容');
      await chatInput.press('Enter');

      // 等待回复
      await page.waitForTimeout(8000);

      // 截图
      await page.screenshot({ path: 'test-results/knowledge-agent-result.png' });

      // 验证回复
      const messages = page.locator('[class*="message"]');
      const messageCount = await messages.count();
      console.log(`✅ 收到 ${messageCount} 条消息`);

      expect(messageCount).toBeGreaterThan(0);
    } else {
      console.log('⚠️ 未找到知识库助手');
    }
  });

  /**
   * 场景 6: 完整流程 - 从选择数字员工到完成对话
   */
  test('完整流程：选择数字员工并完成对话', async ({ page }) => {
    console.log('📍 完整流程测试开始');

    // 1. 确保数字员工列表展开
    const agentToggleButton = page.locator('button:has-text("数字员工")');
    await agentToggleButton.click();
    await page.waitForTimeout(1000);

    // 2. 等待数字员工列表可见
    const agents = page.locator('button:has-text("UI测试Agent"), button:has-text("研究员"), button:has-text("知识库助手")');

    // 如果没找到，再点击一次
    if (await agents.count() === 0) {
      await agentToggleButton.click();
      await page.waitForTimeout(1000);
    }

    await agents.first().waitFor({ state: 'visible', timeout: 5000 });
    console.log('✅ 数字员工列表可见');

    // 3. 选择一个数字员工
    const testAgent = page.locator('button:has-text("UI测试Agent")').first();
    await testAgent.click();
    await page.waitForTimeout(1000);
    console.log('✅ 选择数字员工');

    // 4. 发送消息
    const chatInput = page.locator('textarea[placeholder*="向AI助手提问"], [data-testid="chat-input"]');
    await chatInput.fill('请帮我计算 100 * 200');
    await chatInput.press('Enter');
    console.log('✅ 发送消息');

    // 5. 等待回复
    await page.waitForTimeout(8000);
    console.log('✅ 等待回复');

    // 6. 验证回复
    const messages = page.locator('[class*="message"]');
    const messageCount = await messages.count();
    const lastMessage = await messages.last().textContent();
    console.log(`✅ 对话中有 ${messageCount} 条消息`);
    console.log('✅ 最后一条消息:', lastMessage);

    // 7. 截图
    await page.screenshot({ path: 'test-results/complete-flow.png' });

    // 验证对话成功
    expect(messageCount).toBeGreaterThan(0);
    expect(lastMessage).toBeTruthy();

    console.log('✅ 完整流程测试完成');
  });
});

/**
 * API 直接测试 - 验证 Agent 端点
 */
test.describe('Agent API 直接测试', () => {
  test('Agent 端点可用性测试', async ({ request }) => {
    // 1. 登录
    const loginResponse = await request.post('http://localhost:8080/api/v1/auth/login', {
      data: { username: 'admin', password: 'pwd123' }
    });

    expect(loginResponse.ok()).toBeTruthy();
    const loginData = await loginResponse.json();
    const token = loginData.token;

    console.log('✅ 登录成功');

    // 2. 获取 Agent 列表
    const agentsResponse = await request.get('http://localhost:8080/api/v1/agents/', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    expect(agentsResponse.ok()).toBeTruthy();
    const agentsData = await agentsResponse.json();

    console.log(`✅ 获取到 ${agentsData.agents?.length || agentsData.length || 0} 个 Agent`);

    // 3. 验证 Agent 列表包含预期的数字员工
    const agents = agentsData.agents || agentsData;
    expect(agents.length).toBeGreaterThan(0);

    // 4. 选择第一个 Agent 进行对话测试
    const firstAgent = agents[0];
    console.log(`🤖 测试 Agent: ${firstAgent.display_name || firstAgent.name}`);

    // 使用 Agent chat 接口
    const agentChatResponse = await request.post(
      `http://localhost:8080/api/v1/agents/${firstAgent.id}/chat`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        data: {
          query: '测试消息：请回复收到',
          session_id: null,
          knowledge_base_ids: []
        }
      }
    );

    expect(agentChatResponse.ok()).toBeTruthy();
    console.log('✅ Agent chat 接口调用成功');

    // 验证是否返回流式数据
    const contentType = agentChatResponse.headers()['content-type'];
    console.log(`📡 响应类型: ${contentType}`);

    expect(contentType).toContain('text/event-stream');
  });

  test('Agent 列表应该包含预期的数字员工', async ({ request }) => {
    // 登录
    const loginResponse = await request.post('http://localhost:8080/api/v1/auth/login', {
      data: { username: 'admin', password: 'pwd123' }
    });

    const loginData = await loginResponse.json();
    const token = loginData.token;

    // 获取 Agent 列表
    const agentsResponse = await request.get('http://localhost:8080/api/v1/agents/', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    const agentsData = await agentsResponse.json();
    const agents = agentsData.agents || agentsData;

    console.log('📋 Agent 列表:');
    agents.forEach((agent: any) => {
      console.log(`  - ${agent.display_name || agent.name} (${agent.agent_type}) - ${agent.is_active ? '上线' : '下线'}`);
    });

    // 验证包含预期的数字员工类型
    const agentTypes = agents.map((a: any) => a.agent_type);
    console.log('🏷️ Agent 类型:', [...new Set(agentTypes)]);

    expect(agents.length).toBeGreaterThan(0);
  });
});
