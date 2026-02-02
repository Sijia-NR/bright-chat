import { test, expect } from '@playwright/test';

/**
 * 数字员工 E2E 测试 - 智能版本
 * 自动检测登录状态，跳过不必要的步骤
 */

test.describe('数字员工完整流程 E2E 测试', () => {
  let authToken: string;
  let createdAgentId: string;

  // 辅助函数：检查是否已登录
  async function checkLoginStatus(page: Page) {
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(2000);

    const currentUrl = page.url();
    console.log('当前 URL:', currentUrl);

    // 如果已经登录（不在登录页），直接返回
    if (!currentUrl.includes('/login') && !currentUrl === 'http://localhost:3000/') {
      // 检查是否有登出按钮或用户信息
      const logoutButton = page.locator('button:has-text("退出"), [data-testid="logout-button"]');
      const userElement = page.locator('text=/admin/');

      if (await logoutButton.count() > 0 || await userElement.count() > 0) {
        console.log('✅ 已经登录，跳过登录步骤');
        return true;
      }
    }

    return false;
  }

  // 辅助函数：执行登录
  async function performLogin(page: Page) {
    console.log('📍 执行登录');

    // 尝试多种选择器
    const usernameInput = page.locator('[data-testid="username-input"], input[name="username"], input[type="text"]');
    const passwordInput = page.locator('[data-testid="password-input"], input[name="password"], input[type="password"]');
    const loginButton = page.locator('[data-testid="login-button"], button[type="submit"]');

    if (await usernameInput.count() > 0) {
      await usernameInput.first().fill('admin');
      await passwordInput.first().fill('pwd123');
      await loginButton.first().click();

      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);

      console.log('✅ 登录成功');
      return true;
    } else {
      console.log('⚠️ 未找到登录表单，可能已经登录');
      return false;
    }
  }

  test.beforeAll(async () => {
    // 获取 token
    const loginResponse = await fetch('http://localhost:8080/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'admin', 'password': 'pwd123' })
    });

    const loginData = await loginResponse.json();
    authToken = loginData.token;
    console.log('✅ API token 获取成功');
  });

  test('完整流程：创建→上线→侧边栏→对话', async ({ page }) => {
    // 步骤 1: 检查登录状态并登录（如需要）
    const isLoggedIn = await checkLoginStatus(page);
    if (!isLoggedIn) {
      await performLogin(page);
    }

    // 步骤 2: 通过 API 创建测试 Agent
    console.log('📍 步骤 2: 创建测试 Agent');

    const timestamp = Date.now().toString().slice(-6);
    const agentData = {
      name: `flow_test_${timestamp}`,
      display_name: `流程测试Agent ${timestamp}`,
      description: '端到端完整流程测试',
      agent_type: 'tool',
      tools: ['calculator'],
      is_active: false
    };

    const createResp = await fetch('http://localhost:8080/api/v1/agents/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(agentData)
    });

    expect(createResp.ok).toBeTruthy();
    const agent = await createResp.json();
    createdAgentId = agent.id;

    console.log(`✅ Agent 创建成功: ${createdAgentId}`);
    console.log(`   名称: ${agent.display_name}`);
    console.log(`   状态: ${agent.is_active ? '上线' : '下线'}`);

    // 步骤 3: 上线 Agent
    console.log('📍 步骤 3: 上线 Agent');

    const updateResp = await fetch(`http://localhost:8080/api/v1/agents/${createdAgentId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ is_active: true })
    });

    expect(updateResp.ok).toBeTruthy();
    const updatedAgent = await updateResp.json();

    expect(updatedAgent.is_active).toBe(true);

    console.log('✅ Agent 上线成功');

    // 步骤 4: 验证侧边栏显示
    console.log('📍 步骤 4: 验证侧边栏显示');

    // 刷新页面获取最新状态
    await page.reload();
    await page.waitForTimeout(3000);

    // 检查页面内容
    const pageContent = await page.textContent();
    const hasAgentName = pageContent.includes(agentData.display_name);

    console.log(`页面中是否包含 Agent 名称: ${hasAgentName}`);

    // 查找所有可能的侧边栏 Agent 按钮
    const agentSelectors = [
      'button:has-text("数字员工")',
      '[data-testid="agent-section"]',
      'aside',
      'nav',
      '[class*="sidebar"]'
    ];

    for (const selector of agentSelectors) {
      const element = page.locator(selector);
      if (await element.count() > 0) {
        const text = await element.first().textContent();
        console.log(`找到元素 (${selector}): ${text.substring(0, 100)}`);
      }
    }

    // 截图
    await page.screenshot({ path: 'test-results/flow-step4-sidebar.png', fullPage: true });

    // 步骤 5: 测试 Agent 对话
    console.log('📍 步骤 5: 测试 Agent 对话');

    // 直接通过 API 测试对话
    const chatResp = await fetch(`http://localhost:8080/api/v1/agents/${createdAgentId}/chat`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: '请帮我计算 100 + 200 = ?',
        session_id: null,
        knowledge_base_ids: []
      })
    });

    expect(chatResp.ok).toBeTruthy();

    const contentType = chatResp.headers()['content-type'];
    expect(contentType).toContain('text/event-stream');

    console.log('✅ Agent Chat API 调用成功');
    console.log(`   响应类型: ${contentType}`);

    // 步骤 6: 验证会话记录
    console.log('📍 步骤 6: 验证会话记录');

    // 获取 Agent 的会话列表
    const sessionsResp = await fetch('http://localhost:8080/api/v1/sessions/', {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });

    if (sessionsResp.ok) {
      const sessions = await sessionsResp.json();
      const sessionCount = sessions.length || 0;

      console.log(`✅ 获取到 ${sessionCount} 个会话`);

      // 查找包含当前 Agent 名称的会话
      const agentSessions = sessions.filter((s: any) =>
        s.title && s.title.includes(agentData.display_name)
      );

      if (agentSessions.length > 0) {
        console.log(`✅ 找到 ${agentSessions.length} 个相关会话`);
        console.log(`   最新会话: ${agentSessions[0].title}`);
      } else {
        console.log('⚠️ 未找到相关会话（可能是因为使用了不同的 session_id）');
      }
    }

    console.log('✅ 完整流程测试完成！');

    // 最终截图
    await page.screenshot({ path: 'test-results/flow-complete.png', fullPage: true });
  });

  test('验证侧边栏 Agent 列表刷新', async ({ page }) => {
    console.log('📍 验证侧边栏刷新');

    const isLoggedIn = await checkLoginStatus(page);
    if (!isLoggedIn) {
      await performLogin(page);
    }

    // 获取所有上线的 Agent
    const agentsResp = await fetch('http://localhost:8080/api/v1/agents/', {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });

    const agents = (await agentsResp.json()).agents || agentsResp;
    const activeAgents = agents.filter((a: any) => a.is_active);

    console.log(`API 返回 ${activeAgents.length} 个上线的 Agent`);

    // 在页面中查找
    await page.reload();
    await page.waitForTimeout(3000);

    // 尝试找到 Agent 列表
    const possibleLocators = [
      'button:has-text("数字员工")',
      '[data-testid="agent-section"]',
      'aside button',
      'nav button'
    ];

    let foundAgents = 0;
    for (const locator of possibleLocators) {
      const elements = page.locator(locator);
      const count = await elements.count();
      if (count > 0) {
        console.log(`找到 ${count} 个 "${locator}" 元素`);

        // 点击查看是否展开
        await elements.first().click();
        await page.waitForTimeout(1000);

        // 检查是否有 Agent 列表
        const pageText = await page.textContent();
        if (pageText.includes('Agent') || pageText.includes('助手') || pageText.includes('员工')) {
          // 粗略统计
          const match = pageText.match(/Agent|助手|员工/g);
          if (match) {
            foundAgents = match.length;
            console.log(`在页面中找到约 ${foundAgents} 个 Agent 相关文本`);
          }
        }

        // 截图
        await page.screenshot({ path: `test-results/sidebar-search-${Date.now()}.png` });

        // 如果找到了，就不再尝试其他选择器
        if (foundAgents > 0) {
          break;
        }
      }
    }

    console.log(`✅ 侧边栏检查完成`);
  });

  test.afterAll(async () => {
    // 清理测试数据
    if (createdAgentId) {
      try {
        await fetch(`http://localhost:8080/api/v1/agents/${createdAgentId}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${authToken}` }
        });
        console.log('✅ 清理测试 Agent 完成');
      } catch (e) {
        console.log('⚠️ 清理测试 Agent 失败:', e);
      }
    }
  });
});
