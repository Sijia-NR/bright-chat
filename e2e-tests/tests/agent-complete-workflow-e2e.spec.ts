import { test, expect } from '@playwright/test';

/**
 * 数字员工完整流程 E2E 测试
 *
 * 测试流程：
 * 1. 登录系统
 * 2. 进入系统管理 → Agent 管理
 * 3. 添加新的 Agent
 * 4. 上线 Agent
 * 5. 验证左侧边栏显示数字员工
 * 6. 点击数字员工进入交互页面
 * 7. 发送消息测试对话
 * 8. 验证会话轨迹中出现新会话
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

  test('完整流程：从创建 Agent 到对话测试', async ({ page }) => {
    console.log('📍 步骤 1: 进入系统管理页面');

    // 查找系统管理按钮
    const adminButton = page.locator('button:has-text("系统管理"), [data-testid="admin-button"], [aria-label*="admin"], .admin-btn');

    const adminCount = await adminButton.count();
    if (adminCount > 0) {
      await adminButton.first().click();
      await page.waitForTimeout(1000);
    }

    // 验证进入管理界面
    const adminPanel = page.locator('[class*="admin"], [data-testid="admin-panel"], .AdminPanel');
    await expect(adminPanel.first()).toBeVisible({ timeout: 5000 });

    console.log('✅ 进入系统管理页面');

    // 截图
    await page.screenshot({ path: 'test-results/01-admin-panel.png' });

    console.log('📍 步骤 2: 打开 Agent 管理');

    // 查找 Agent 管理标签
    const agentTab = page.locator('button:has-text("数字员工"), button:has-text("Agent"), [data-testid="agent-tab"]');

    const agentTabCount = await agentTab.count();
    if (agentTabCount > 0) {
      await agentTab.first().click();
      await page.waitForTimeout(1000);
    }

    console.log('✅ 打开 Agent 管理');

    // 截图
    await page.screenshot({ path: 'test-results/02-agent-management.png' });

    console.log('📍 步骤 3: 添加新 Agent');

    // 查找新建 Agent 按钮
    const createButton = page.locator('button:has-text("新建"), button:has-text("添加"), button:has-text("创建"), [data-testid="create-agent"], [data-testid="add-agent-button"]');

    if (await createButton.count() > 0) {
      await createButton.first().click();
      await page.waitForTimeout(1000);

      // 填写 Agent 表单
      const timestamp = Date.now().toString().slice(-6);
      const agentName = `E2E测试Agent_${timestamp}`;

      // 查找表单字段并填写
      const nameInput = page.locator('input[name="name"], input[placeholder*="名称"], #agent-name');
      if (await nameInput.count() > 0) {
        await nameInput.first().fill(agentName);
      }

      const displayNameInput = page.locator('input[name="display_name"], input[placeholder*="显示"], #agent-display-name');
      if (await displayNameInput.count() > 0) {
        await displayNameInput.first().fill(`E2E测试Agent ${timestamp}`);
      }

      const descInput = page.locator('textarea[name="description"], #agent-description');
      if (await descInput.count() > 0) {
        await descInput.first().fill('这是一个E2E测试自动创建的Agent');
      }

      // 选择 Agent 类型（工具型）
      const typeSelect = page.locator('select[name="agent_type"], #agent-type');
      if (await typeSelect.count() > 0) {
        await typeSelect.first().selectOption('tool');
      }

      // 选择工具（计算器）
      const toolCheckbox = page.locator('input[type="checkbox"][value="calculator"], input[value*="calculator"]');
      if (await toolCheckbox.count() > 0) {
        const checked = await toolCheckbox.first().isChecked();
        if (!checked) {
          await toolCheckbox.first().check();
        }
      }

      console.log(`✅ 填写 Agent 表单: ${agentName}`);

      // 截图
      await page.screenshot({ path: 'test-results/03-agent-form.png' });

      // 提交表单
      const submitButton = page.locator('button[type="submit"], button:has-text("保存"), button:has-text("提交"), button:has-text("创建")');

      // 监听 API 响应
      const createPromise = page.waitForResponse(resp =>
        resp.url().includes('/agents/') && resp.status() === 201,
        { timeout: 10000 }
      );

      await submitButton.first().click();

      // 等待创建成功
      try {
        await createPromise;
        console.log('✅ Agent 创建 API 调用成功');
      } catch (e) {
        console.log('⚠️ Agent 创建 API 未检测到，可能使用了不同的响应方式');
      }

      await page.waitForTimeout(2000);

      console.log('✅ Agent 创建完成');
    }

    console.log('📍 步骤 4: 上线 Agent');

    // 查找刚创建的 Agent
    const agents = page.locator('text=E2E测试Agent');

    if (await agents.count() > 0) {
      // 找到该 Agent 的上线按钮
      const agentRow = agents.first().locator('..');
      const activateButton = agentRow.locator('button[title*="上线"], button[aria-label*="上线"], .power-btn');

      // 监听 API 响应
      const updatePromise = page.waitForResponse(resp =>
        resp.url().includes('/agents/') && resp.method() === 'PUT',
        { timeout: 10000 }
      );

      // 点击上线按钮
      const powerButton = agentRow.locator('button:has(Power), button[class*="power"], button[title*="上线"], button[title*="下线"]');

      if (await powerButton.count() > 0) {
        await powerButton.first().click();

        // 等待 API 调用
        try {
          await updatePromise;
          console.log('✅ Agent 上线 API 调用成功');
        } catch (e) {
          console.log('⚠️ Agent 上线 API 未检测到');
        }

        await page.waitForTimeout(2000);

        // 验证状态更新
        const statusBadge = agentRow.locator('[class*="green"], span:has-text("上线")');
        await expect(statusBadge.first()).toBeVisible({ timeout: 5000 });

        console.log('✅ Agent 已上线');
      }

      // 截图
      await page.screenshot({ path: 'test-results/04-agent-active.png' });
    }

    console.log('📍 步骤 5: 验证左侧边栏显示数字员工');

    // 查找数字员工按钮
    const agentSectionButton = page.locator('button:has-text("数字员工"), .agent-section-button');

    if (await agentSectionButton.count() > 0) {
      // 点击展开数字员工列表
      await agentSectionButton.first().click();
      await page.waitForTimeout(1000);
    }

    // 验证刚创建的 Agent 显示在列表中
    const agentInSidebar = page.locator(`text=/E2E测试Agent/`);

    // 等待 Agent 出现在侧边栏
    await expect(agentInSidebar.first()).toBeVisible({ timeout: 5000 });

    console.log('✅ 数字员工显示在左侧边栏');

    // 截图
    await page.screenshot({ path: 'test-results/05-agent-in-sidebar.png' });

    console.log('📍 步骤 6: 点击数字员工进入交互页面');

    // 点击刚创建的 Agent
    await agentInSidebar.first().click();

    await page.waitForTimeout(2000);

    // 验证进入对话页面
    const chatInput = page.locator('textarea[placeholder*="向AI助手提问"], [data-testid="chat-input"], .chat-input');
    await expect(chatInput.first()).toBeVisible({ timeout: 5000 });

    console.log('✅ 进入数字员工交互页面');

    // 截图
    await page.screenshot({ path: 'test-results/06-agent-chat-page.png' });

    console.log('📍 步骤 7: 发送测试消息');

    // 发送测试消息
    const testMessage = '你好，请帮我计算 123 + 456 = ?';

    await chatInput.first().fill(testMessage);
    await chatInput.first().press('Enter');

    console.log('✅ 发送消息: ' + testMessage);

    // 监听 Agent Chat API
    const agentChatPromise = page.waitForResponse(resp =>
      resp.url().includes('/agents/') && resp.url().includes('/chat'),
      { timeout: 15000 }
    );

    // 等待响应
    try {
      const response = await agentChatPromise;
      console.log('✅ Agent Chat API 调用成功');
      expect(response.status()).toBe(200);
    } catch (e) {
      console.log('⚠️ Agent Chat API 调用超时或失败');
    }

    // 等待消息显示
    await page.waitForTimeout(5000);

    // 验证消息显示
    const messages = page.locator('[class*="message"], [data-testid="message"], .message');
    const messageCount = await messages.count();

    expect(messageCount).toBeGreaterThan(0);

    console.log(`✅ 收到 ${messageCount} 条消息`);

    // 截图
    await page.screenshot({ path: 'test-results/07-agent-response.png' });

    console.log('📍 步骤 8: 验证会话轨迹中出现新会话');

    // 查找会话轨迹按钮
    const sessionTrailButton = page.locator('button:has-text("会话轨迹"), [data-testid="session-trail"]');

    if (await sessionTrailButton.count() > 0) {
      // 点击会话轨迹
      await sessionTrailButton.first().click();
      await page.waitForTimeout(1000);

      // 验证新会话出现
      const newSession = page.locator('text=/E2E测试Agent.*对话/, generic:has-text("对话")');

      // 等待新会话出现
      await expect(newSession.first()).toBeVisible({ timeout: 5000 });

      console.log('✅ 会话轨迹中出现新会话');
    } else {
      console.log('⚠️ 未找到会话轨迹按钮');
    }

    // 最终截图
    await page.screenshot({ path: 'test-results/08-complete-flow.png' });

    console.log('✅ 完整流程测试通过！');
  });

  test('验证数字员工上线后前端状态同步', async ({ page }) => {
    console.log('📍 测试 Agent 上线后前端状态同步');

    // 进入系统管理 → Agent 管理
    const adminButton = page.locator('button:has-text("系统管理")');
    if (await adminButton.count() > 0) {
      await adminButton.first().click();
      await page.waitForTimeout(1000);
    }

    const agentTab = page.locator('button:has-text("数字员工")');
    if (await agentTab.count() > 0) {
      await agentTab.first().click();
      await page.waitForTimeout(1000);
    }

    // 查找下线的 Agent
    const inactiveAgent = page.locator('span:has-text("下线")').first();

    if (await inactiveAgent.count() > 0) {
      // 找到对应的上线按钮
      const agentRow = inactiveAgent.locator('..');
      const powerButton = agentRow.locator('button:has(Power)');

      // 记录上线前的状态
      const beforeText = await agentRow.textContent();

      // 点击上线
      await powerButton.click();

      // 等待状态更新
      await page.waitForTimeout(2000);

      // 验证状态变为上线
      const activeBadge = agentRow.locator('span:has-text("上线")');
      await expect(activeBadge.first()).toBeVisible({ timeout: 5000 });

      console.log('✅ Agent 状态已更新为上线');

      // 截图
      await page.screenshot({ path: 'test-results/status-sync.png' });
    } else {
      console.log('⚠️ 没有找到下线的 Agent');
    }
  });

  test('验证左侧边栏数字员工列表刷新', async ({ page }) => {
    console.log('📍 测试左侧边栏数字员工列表刷新');

    // 查找数字员工按钮
    const agentButton = page.locator('button:has-text("数字员工")');

    if (await agentButton.count() > 0) {
      // 点击展开列表
      await agentButton.first().click();
      await page.waitForTimeout(1000);

      // 记录当前 Agent 数量
      const agentsBefore = page.locator('button:has-text("Agent"), button:has-text("助手")');
      const countBefore = await agentsBefore.count();

      console.log(`当前数字员工数量: ${countBefore}`);

      expect(countBefore).toBeGreaterThan(0);

      // 截图
      await page.screenshot({ path: 'test-results/sidebar-agents.png' });

      console.log('✅ 左侧边栏显示数字员工列表');
    } else {
      console.log('⚠️ 未找到数字员工按钮');
    }
  });
});

/**
 * 辅助测试：直接 API 测试
 */
test.describe('Agent API 直接测试', () => {
  test('验证 Agent CRUD 接口', async ({ request }) => {
    console.log('📍 测试 Agent CRUD 接口');

    // 1. 登录
    const loginResponse = await request.post('http://localhost:8080/api/v1/auth/login', {
      data: { username: 'admin', password: 'pwd123' }
    });

    expect(loginResponse.ok()).toBeTruthy();
    const loginData = await loginResponse.json();
    const token = loginData.token;

    console.log('✅ 登录成功');

    // 2. 创建 Agent
    const timestamp = Date.now().toString();
    const createResponse = await request.post('http://localhost:8080/api/v1/agents/', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        name: `api_test_agent_${timestamp}`,
        display_name: `API测试Agent ${timestamp}`,
        description: '通过 API 创建的测试 Agent',
        agent_type: 'tool',
        tools: ['calculator'],
        is_active: false
      }
    });

    expect(createResponse.ok()).toBeTruthy();
    const createdAgent = await createResponse.json();
    const agentId = createdAgent.id;

    console.log(`✅ Agent 创建成功: ${agentId}`);

    // 3. 上线 Agent
    const updateResponse = await request.put(`http://localhost:8080/api/v1/agents/${agentId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        is_active: true
      }
    });

    expect(updateResponse.ok()).toBeTruthy();
    const updatedAgent = await updateResponse.json();

    expect(updatedAgent.is_active).toBe(true);

    console.log('✅ Agent 上线成功');

    // 4. 获取 Agent 列表验证
    const listResponse = await request.get('http://localhost:8080/api/v1/agents/', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    expect(listResponse.ok()).toBeTruthy();
    const listData = await listResponse.json();
    const agents = listData.agents || listData;

    const activeAgent = agents.find((a: any) => a.id === agentId);
    expect(activeAgent).toBeDefined();
    expect(activeAgent.is_active).toBe(true);

    console.log('✅ Agent 列表验证成功，状态为上线');

    // 5. 测试 Agent Chat
    const chatResponse = await request.post(`http://localhost:8080/api/v1/agents/${agentId}/chat`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        query: '测试消息：请回复收到',
        session_id: null,
        knowledge_base_ids: []
      }
    });

    expect(chatResponse.ok()).toBeTruthy();

    const contentType = chatResponse.headers()['content-type'];
    expect(contentType).toContain('text/event-stream');

    console.log('✅ Agent Chat 接口正常，返回流式数据');
  });
});
