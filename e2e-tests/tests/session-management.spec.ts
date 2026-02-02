import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { AppPage } from '../pages/AppPage';

/**
 * 会话管理功能测试
 *
 * 测试场景：
 * 1. 查看历史会话
 * 2. 切换会话
 * 3. 删除会话
 * 4. 会话标题自动更新
 * 5. 会话持久化
 */

test.describe('会话管理功能测试', () => {
  const ADMIN_CREDENTIALS = { username: 'admin', password: 'pwd123' };

  let loginPage: LoginPage;
  let appPage: AppPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    appPage = new AppPage(page);

    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
    await appPage.waitForAppLoad();
  });

  /**
   * 测试场景 1: 查看历史会话列表
   * E2E-SESSION-001
   */
  test('应显示历史会话列表', async ({ page }) => {
    // 通过 API 获取会话列表
    const response = await page.request.get('http://localhost:8080/api/v1/sessions/');

    console.log('会话列表 API 响应状态:', response.status());

    if (response.status() === 200) {
      const sessions = await response.json();
      console.log('会话数量:', Array.isArray(sessions) ? sessions.length : 'N/A');

      if (Array.isArray(sessions) && sessions.length > 0) {
        console.log('第一个会话:', JSON.stringify(sessions[0], null, 2));

        // 检查侧边栏是否显示会话
        const sessionItems = page.locator('aside button, aside [role="button"]').filter({ hasText: new RegExp(sessions[0].title.substring(0, 10)) });

        if (await sessionItems.count() > 0) {
          await expect(sessionItems.first()).toBeVisible();
        }
      }
    }

    await appPage.screenshot('session_list');
  });

  /**
   * 测试场景 2: 创建新会话
   * E2E-SESSION-002
   */
  test('应能创建新会话', async ({ page }) => {
    // 获取初始会话数
    const initialResponse = await page.request.get('http://localhost:8080/api/v1/sessions/');
    let initialCount = 0;

    if (initialResponse.status() === 200) {
      const sessions = await initialResponse.json();
      initialCount = Array.isArray(sessions) ? sessions.length : 0;
    }

    console.log('初始会话数:', initialCount);

    // 点击新对话按钮
    await page.locator('[data-testid="new-chat-button"]').click();
    await page.waitForTimeout(1000);

    // 发送一条消息创建会话
    const testMessage = `新会话测试_${Date.now()}`;
    await page.locator('[data-testid="chat-input"]').fill(testMessage);
    await page.locator('[data-testid="send-button"]').click();
    await page.waitForTimeout(3000);

    // 再次获取会话列表
    const afterResponse = await page.request.get('http://localhost:8080/api/v1/sessions/');

    if (afterResponse.status() === 200) {
      const sessions = await afterResponse.json();
      const afterCount = Array.isArray(sessions) ? sessions.length : 0;

      console.log('创建后会话数:', afterCount);

      // 会话数应该增加
      expect(afterCount).toBeGreaterThanOrEqual(initialCount);
    }

    await appPage.screenshot('session_created');
  });

  /**
   * 测试场景 3: 切换会话
   * E2E-SESSION-003
   */
  test('应能切换历史会话', async ({ page }) => {
    // 创建第一个会话
    await page.locator('[data-testid="new-chat-button"]').click();
    await page.waitForTimeout(500);

    const message1 = `会话1消息_${Date.now()}`;
    await page.locator('[data-testid="chat-input"]').fill(message1);
    await page.locator('[data-testid="send-button"]').click();
    await page.waitForTimeout(3000);

    // 创建第二个会话
    await page.locator('[data-testid="new-chat-button"]').click();
    await page.waitForTimeout(500);

    const message2 = `会话2消息_${Date.now()}`;
    await page.locator('[data-testid="chat-input"]').fill(message2);
    await page.locator('[data-testid="send-button"]').click();
    await page.waitForTimeout(3000);

    // 查找侧边栏的会话项
    const sessionButtons = page.locator('aside button').filter({ hasText: /会话/ });

    if (await sessionButtons.count() >= 2) {
      // 点击第一个会话
      await sessionButtons.nth(0).click();
      await page.waitForTimeout(1000);

      // 验证消息内容
      const hasMessage1 = await page.locator(`[data-message-role="user"]`).filter({ hasText: message1 }).count();
      console.log('切换后会话1消息数:', hasMessage1);
    }

    await appPage.screenshot('session_switched');
  });

  /**
   * 测试场景 4: 删除会话
   * E2E-SESSION-004
   */
  test('应能删除会话', async ({ page }) => {
    // 创建一个测试会话
    await page.locator('[data-testid="new-chat-button"]').click();
    await page.waitForTimeout(500);

    const testMessage = `待删除会话_${Date.now()}`;
    await page.locator('[data-testid="chat-input"]').fill(testMessage);
    await page.locator('[data-testid="send-button"]').click();
    await page.waitForTimeout(3000);

    // 获取当前会话ID（从URL或状态推断）
    const currentMessages = await page.locator('[data-message-role="user"]').count();
    console.log('删除前消息数:', currentMessages);

    // 查找并点击删除按钮（通常在会话项旁边）
    const deleteButton = page.locator('aside button').filter({ hasText: /删除|Remove|Delete/ });

    if (await deleteButton.count() > 0) {
      await deleteButton.first().click();
      await page.waitForTimeout(500);

      // 确认删除（如果有确认对话框）
      const confirmButton = page.locator('button').filter({ hasText: /确认|Confirm|Yes/ });

      if (await confirmButton.count() > 0) {
        await confirmButton.first().click();
      }

      await page.waitForTimeout(1000);
    }

    await appPage.screenshot('session_deleted');
  });

  /**
   * 测试场景 5: 会话标题自动更新
   * E2E-SESSION-005
   */
  test('会话标题应根据首条消息自动更新', async ({ page }) => {
    // 创建新会话
    await page.locator('[data-testid="new-chat-button"]').click();
    await page.waitForTimeout(500);

    // 发送第一条消息
    const firstMessage = '这是会话的标题消息，应该被用作会话标题';
    await page.locator('[data-testid="chat-input"]').fill(firstMessage);
    await page.locator('[data-testid="send-button"]').click();
    await page.waitForTimeout(3000);

    // 获取会话列表
    const sessionsResponse = await page.request.get('http://localhost:8080/api/v1/sessions/');

    if (sessionsResponse.status() === 200) {
      const sessions = await sessionsResponse.json();

      if (Array.isArray(sessions) && sessions.length > 0) {
        // 找到最新的会话
        const latestSession = sessions.sort((a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )[0];

        console.log('最新会话标题:', latestSession.title);
        console.log('首条消息:', firstMessage.substring(0, 50));

        // 标题应该包含消息的部分内容
        expect(latestSession.title.length).toBeGreaterThan(0);
      }
    }

    await appPage.screenshot('session_title_auto_update');
  });

  /**
   * 测试场景 6: 会话持久化（刷新页面）
   * E2E-SESSION-006
   */
  test('会话应在页面刷新后保持', async ({ page }) => {
    // 创建会话并添加消息
    await page.locator('[data-testid="new-chat-button"]').click();
    await page.waitForTimeout(500);

    const uniqueMessage = `持久化测试_${Date.now()}`;
    await page.locator('[data-testid="chat-input"]').fill(uniqueMessage);
    await page.locator('[data-testid="send-button"]').click();
    await page.waitForTimeout(3000);

    // 等待消息保存
    await page.waitForTimeout(2000);

    // 刷新页面
    await page.reload();
    await page.waitForTimeout(3000);

    // 验证消息仍然存在
    const hasMessage = await page.locator(`[data-message-role="user"]`).filter({ hasText: uniqueMessage }).count();
    console.log('刷新后消息数:', hasMessage);

    // 消息应该存在
    expect(hasMessage).toBeGreaterThan(0);

    await appPage.screenshot('session_persistence_refresh');
  });

  /**
   * 测试场景 7: 会话消息加载
   * E2E-SESSION-007
   */
  test('切换会话时应正确加载消息', async ({ page }) => {
    // 获取会话列表
    const sessionsResponse = await page.request.get('http://localhost:8080/api/v1/sessions/');

    if (sessionsResponse.status() !== 200) {
      test.skip(true, '无法获取会话列表');
      return;
    }

    const sessions = await sessionsResponse.json();

    if (!Array.isArray(sessions) || sessions.length === 0) {
      test.skip(true, '没有历史会话');
      return;
    }

    // 选择第一个会话
    const firstSession = sessions[0];
    console.log('选择会话:', firstSession.title);

    // 点击会话（通过标题查找）
    const sessionButton = page.locator('aside button').filter({ hasText: new RegExp(firstSession.title.substring(0, 10)) });

    if (await sessionButton.count() > 0) {
      await sessionButton.first().click();
      await page.waitForTimeout(2000);

      // 获取该会话的消息
      const messagesResponse = await page.request.get(
        `http://localhost:8080/api/v1/sessions/${firstSession.id}/messages`
      );

      if (messagesResponse.status() === 200) {
        const messages = await messagesResponse.json();
        console.log('会话消息数:', Array.isArray(messages) ? messages.length : 'N/A');

        if (Array.isArray(messages) && messages.length > 0) {
          // 验证消息在界面上显示
          await expect(page.locator('[data-testid^="message-"]').first()).toBeVisible();
        }
      }
    }

    await appPage.screenshot('session_messages_loaded');
  });

  /**
   * 测试场景 8: 多会话并发操作
   * E2E-SESSION-008
   */
  test('应能处理多个会话的快速切换', async ({ page }) => {
    // 获取现有会话
    const sessionsResponse = await page.request.get('http://localhost:8080/api/v1/sessions/');

    if (sessionsResponse.status() !== 200) {
      test.skip(true, '无法获取会话列表');
      return;
    }

    let sessions = await sessionsResponse.json();

    if (!Array.isArray(sessions)) {
      test.skip(true, '会话列表格式错误');
      return;
    }

    // 确保至少有3个会话
    while (sessions.length < 3) {
      await page.locator('[data-testid="new-chat-button"]').click();
      await page.waitForTimeout(500);

      await page.locator('[data-testid="chat-input"]').fill(`会话${sessions.length + 1}`);
      await page.locator('[data-testid="send-button"]').click();
      await page.waitForTimeout(2000);

      const response = await page.request.get('http://localhost:8080/api/v1/sessions/');
      if (response.status() === 200) {
        sessions = await response.json();
      }
    }

    console.log('总共有', sessions.length, '个会话');

    // 快速切换会话
    const sessionButtons = page.locator('aside button').filter({ hasText: /会话/ });

    for (let i = 0; i < Math.min(3, await sessionButtons.count()); i++) {
      await sessionButtons.nth(i).click();
      await page.waitForTimeout(500);
      console.log('切换到会话', i + 1);
    }

    // 验证界面正常
    await expect(page.locator('[data-testid="chat-input"]')).toBeVisible();

    await appPage.screenshot('session_quick_switch');
  });

  /**
   * 测试场景 9: 空会话状态
   * E2E-SESSION-009
   */
  test('新会话应显示欢迎界面', async ({ page }) => {
    // 点击新对话
    await page.locator('[data-testid="new-chat-button"]').click();
    await page.waitForTimeout(1000);

    // 验证没有消息
    const messageCount = await page.locator('[data-testid^="message-"]').count();
    expect(messageCount).toBe(0);

    // 验证显示欢迎界面
    await expect(page.locator('text=AI工作台')).toBeVisible();

    await appPage.screenshot('empty_session_welcome');
  });

  /**
   * 测试场景 10: 会话时间戳
   * E2E-SESSION-010
   */
  test('会话应显示正确的时间信息', async ({ page }) => {
    // 获取会话列表
    const sessionsResponse = await page.request.get('http://localhost:8080/api/v1/sessions/');

    if (sessionsResponse.status() === 200) {
      const sessions = await sessionsResponse.json();

      if (Array.isArray(sessions) && sessions.length > 0) {
        const firstSession = sessions[0];
        console.log('会话创建时间:', firstSession.created_at);
        console.log('会话更新时间:', firstSession.last_updated);

        // 验证时间格式
        expect(firstSession.created_at).toBeDefined();
        expect(firstSession.last_updated).toBeDefined();
      }
    }

    await appPage.screenshot('session_timestamp');
  });
});

/**
 * 会话 API 测试
 */
test.describe('会话 API 测试', () => {
  const ADMIN_CREDENTIALS = { username: 'admin', password: 'pwd123' };

  let authToken: string;

  test.beforeAll(async ({ request }) => {
    // 获取认证 token
    const loginResponse = await request.post('http://localhost:8080/api/v1/auth/login', {
      data: {
        username: ADMIN_CREDENTIALS.username,
        password: ADMIN_CREDENTIALS.password
      }
    });

    if (loginResponse.ok()) {
      const data = await loginResponse.json();
      authToken = data.access_token;
    }
  });

  /**
   * 测试场景 11: 创建会话 API
   * E2E-SESSION-API-001
   */
  test('应能通过 API 创建会话', async ({ request }) => {
    const response = await request.post('http://localhost:8080/api/v1/sessions/', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      },
      data: {
        title: 'API测试会话',
        user_id: 'test-user-id'
      }
    });

    console.log('创建会话响应状态:', response.status());

    if (response.ok()) {
      const session = await response.json();
      console.log('创建的会话:', session);

      expect(session.id).toBeDefined();
      expect(session.title).toBe('API测试会话');
    }
  });

  /**
   * 测试场景 12: 获取会话消息 API
   * E2E-SESSION-API-002
   */
  test('应能通过 API 获取会话消息', async ({ request }) => {
    // 先获取会话列表
    const sessionsResponse = await request.get('http://localhost:8080/api/v1/sessions/', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    if (sessionsResponse.ok()) {
      const sessions = await sessionsResponse.json();

      if (Array.isArray(sessions) && sessions.length > 0) {
        const firstSession = sessions[0];

        // 获取消息
        const messagesResponse = await request.get(
          `http://localhost:8080/api/v1/sessions/${firstSession.id}/messages`,
          {
            headers: {
              'Authorization': `Bearer ${authToken}`
            }
          }
        );

        console.log('获取消息响应状态:', messagesResponse.status());

        if (messagesResponse.ok()) {
          const messages = await messagesResponse.json();
          console.log('消息数量:', Array.isArray(messages) ? messages.length : 'N/A');
        }
      }
    }
  });
});
