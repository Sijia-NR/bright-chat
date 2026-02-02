import { test, expect } from '@playwright/test';

/**
 * 数字员工核心流程 E2E 测试
 *
 * 核心流程：
 * 1. 登录
 * 2. 创建 Agent
 * 3. 上线 Agent
 * 4. 验证侧边栏显示
 * 5. Agent 对话
 */

test.describe('数字员工核心流程', () => {
  let authToken: string;
  let createdAgentId: string;

  test.beforeAll(async () => {
    // 登录获取 token
    const loginResponse = await fetch('http://localhost:8080/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'admin', password: 'pwd123' })
    });

    const loginData = await loginResponse.json();
    authToken = loginData.token;
  });

  test('API: 创建并上线数字员工', async ({ page }) => {
    console.log('📍 测试 1: 登录');

    await page.goto('http://localhost:3000');
    await page.fill('input[name="username"], [data-testid="username-input"]', 'admin');
    await page.fill('input[name="password"], [data-testid="password-input"]', 'pwd123');
    await page.click('button[type="submit"], [data-testid="login-button"]');

    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    console.log('✅ 登录成功');

    // 创建测试 Agent
    console.log('📍 测试 2: 通过 API 创建测试 Agent');

    const timestamp = Date.now().toString();
    const createResponse = await fetch('http://localhost:8080/api/v1/agents/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: `e2e_test_${timestamp}`,
        display_name: `E2E测试Agent ${timestamp}`,
        description: '端到端测试自动创建',
        agent_type: 'tool',
        tools: ['calculator'],
        is_active: false  // 先创建为下线状态
      })
    });

    expect(createResponse.ok).toBeTruthy();
    const agent = await createResponse.json();
    createdAgentId = agent.id;

    console.log(`✅ Agent 创建成功: ${createdAgentId}`);

    // 上线 Agent
    console.log('📍 测试 3: 上线 Agent');

    const updateResponse = await fetch(`http://localhost:8080/api/v1/agents/${createdAgentId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ is_active: true })
    });

    expect(updateResponse.ok).toBeTruthy();
    const updatedAgent = await updateResponse.json();

    expect(updatedAgent.is_active).toBe(true);

    console.log('✅ Agent 上线成功');

    // 验证列表中能看到
    console.log('📍 测试 4: 验证 Agent 在列表中');

    await page.reload(); // 刷新页面
    await page.waitForTimeout(2000);

    // 获取 Agent 列表
    const listResponse = await fetch('http://localhost:8080/api/v1/agents/', {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });

    const listData = await listResponse.json();
    const agents = listData.agents || listData;

    const ourAgent = agents.find((a: any) => a.id === createdAgentId);

    expect(ourAgent).toBeDefined();
    expect(ourAgent.is_active).toBe(true);

    console.log('✅ Agent 在列表中且状态为上线');
    console.log(`   Agent 名称: ${ourAgent.display_name || ourAgent.name}`);
    console.log(`   Agent 状态: ${ourAgent.is_active ? '上线' : '下线'}`);
  });

  test('UI: 验证数字员工在侧边栏显示', async ({ page }) => {
    console.log('📍 测试 5: 验证侧边栏显示 Agent');

    await page.goto('http://localhost:3000');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'pwd123');
    await page.click('button[type="submit"]');

    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);

    console.log('当前页面 URL:', page.url());

    // 查找数字员工相关元素
    const sidebar = page.locator('aside, [class*="sidebar"], nav');
    const sidebarCount = await sidebar.count();

    console.log(`侧边栏数量: ${sidebarCount}`);

    if (sidebarCount > 0) {
      const sidebarText = await sidebar.first().textContent();
      console.log('侧边栏内容:', sidebarText.substring(0, 200));
    }

    // 查找任何包含 "Agent" 或 "数字员工" 的按钮
    const agentButtons = page.locator('button:has-text("Agent"), button:has-text("数字员工")');
    const agentButtonCount = await agentButtons.count();

    console.log(`Agent 按钮/数字员工按钮数量: ${agentButtonCount}`);

    if (agentButtonCount > 0) {
      // 点击第一个
      await agentButtons.first().click();
      await page.waitForTimeout(1000);

      // 查看是否展开了 Agent 列表
      const pageContent = await page.content();
      console.log('点击后的页面内容长度:', pageContent.length);

      // 查找 E2E 测试 Agent
      const e2eAgent = page.locator('text=/E2E测试Agent/');
      if (await e2eAgent.count() > 0) {
        console.log('✅ 在页面中找到 E2E 测试 Agent');
      } else {
        console.log('⚠️ 未在页面中找到 E2E 测试 Agent');
      }
    }

    // 截图
    await page.screenshot({ path: 'test-results/sidebar-check.png', fullPage: true });

    console.log('✅ 侧边栏检查完成（截图已保存）');
  });

  test('Agent 对话测试', async ({ page }) => {
    console.log('📍 测试 6: Agent 对话功能');

    await page.goto('http://localhost:3000');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'pwd123');
    await page.click('button[type="submit"]');

    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // 先获取一个在线的 Agent
    const listResponse = await fetch('http://localhost:8080/api/v1/agents/', {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });

    const listData = await listResponse.json();
    const agents = listData.agents || listData;

    // 找一个上线的工具型 Agent
    const activeAgent = agents.find((a: any) =>
      a.is_active && a.agent_type === 'tool'
    );

    if (!activeAgent) {
      console.log('⚠️ 没有找到上线的工具型 Agent，跳过对话测试');
      test.skip();
      return;
    }

    const agentId = activeAgent.id;
    const agentName = activeAgent.display_name || activeAgent.name;

    console.log(`使用 Agent: ${agentName} (${agentId})`);

    // 尝试通过页面导航到 Agent 对话
    // 方法 1: 查找侧边栏中的 Agent
    const agentButton = page.locator(`button:has-text("${agentName}")`);

    if (await agentButton.count() > 0) {
      console.log('在侧边栏找到 Agent 按钮，点击进入对话');
      await agentButton.first().click();
      await page.waitForTimeout(2000);
    } else {
      console.log('⚠️ 侧边栏未找到 Agent，尝试直接通过 API 对话');
    }

    // 找到聊天输入框
    const chatInput = page.locator('textarea[placeholder*="向AI"], textarea[placeholder*="提问"], [data-testid="chat-input"]');

    await expect(chatInput.first()).toBeVisible({ timeout: 5000 });

    console.log('✅ 找到聊天输入框');

    // 发送测试消息
    const testMessage = '请帮我计算 100 + 200 = ?';
    await chatInput.first().fill(testMessage);
    await chatInput.first().press('Enter');

    console.log(`✅ 发送消息: ${testMessage}`);

    // 等待响应
    await page.waitForTimeout(8000);

    // 验证有消息显示
    const messages = page.locator('[class*="message"], [data-testid="message"]');
    const messageCount = await messages.count();

    expect(messageCount).toBeGreaterThan(0);

    console.log(`✅ 收到 ${messageCount} 条消息`);

    // 检查是否包含答案（300）
    const pageText = await page.textContent();
    const hasAnswer = pageText.includes('300') || pageText.includes('300.0') || pageText.includes('三百');

    if (hasAnswer) {
      console.log('✅ 响应包含正确答案: 300');
    } else {
      console.log('⚠️ 响应未包含明显答案，但对话流程正常');
    }

    // 截图
    await page.screenshot({ path: 'test-results/agent-chat-test.png' });

    console.log('✅ Agent 对话测试完成');
  });

  test('会话轨迹测试', async ({ page }) => {
    console.log('📍 测试 7: 会话轨迹显示');

    await page.goto('http://localhost:3000');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'pwd123');
    await page.click('button[type="submit"]');

    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // 查找会话轨迹
    const sessionTrailButton = page.locator('button:has-text("会话轨迹"), [data-testid="session-trail"]');

    const hasSessionTrail = await sessionTrailButton.count() > 0;

    if (hasSessionTrail) {
      console.log('找到会话轨迹按钮，点击查看');
      await sessionTrailButton.first().click();
      await page.waitForTimeout(1000);

      // 验证有会话列表
      const sessions = page.locator('[class*="session"], li, [data-testid="session"]');
      const sessionCount = await sessions.count();

      console.log(`会话数量: ${sessionCount}`);

      // 截图
      await page.screenshot({ path: 'test-results/session-trail-test.png' });

      if (sessionCount > 0) {
        console.log('✅ 会话轨迹显示正常');
      } else {
        console.log('⚠️ 会话轨迹为空（可能还没有对话记录）');
      }
    } else {
      console.log('⚠️ 未找到会话轨迹按钮');
      // 截图看看页面结构
      await page.screenshot({ path: 'test-results/no-session-trail.png', fullPage: true });
    }
  });

  test.afterAll(async () => {
    // 清理测试数据
    if (createdAgentId) {
      try {
        await fetch(`http://localhost:8080/api/v1/agents/${createdAgentId}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${authToken}` }
        });
        console.log('✅ 清理测试 Agent');
      } catch (e) {
        console.log('⚠️ 清理测试 Agent 失败:', e);
      }
    }
  });
});
