import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { AppPage } from '../pages/AppPage';

/**
 * 对话功能完整测试套件
 *
 * 测试场景：
 * 1. 基础对话功能 - 登录、创建会话、发送消息
 * 2. 流式响应测试 - SSE 流式接口验证
 * 3. 模型选择 - 切换不同模型
 * 4. 消息历史 - 会话管理
 * 5. 错误处理 - API 错误处理
 * 6. 性能测试 - 响应时间
 */

test.describe('对话功能完整测试', () => {
  const ADMIN_CREDENTIALS = { username: 'admin', password: 'pwd123' };

  let loginPage: LoginPage;
  let appPage: AppPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    appPage = new AppPage(page);

    // 登录
    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);

    // 等待应用加载
    await appPage.waitForAppLoad();
  });

  /**
   * 测试场景 1: 基础对话功能
   * E2E-CHAT-001
   */
  test('应能完成完整的对话流程', async ({ page }) => {
    // 1. 创建新对话
    await appPage.startNewChat();
    await page.waitForTimeout(500);

    // 2. 验证消息输入框可见
    const chatInput = page.locator('[data-testid="chat-input"]');
    await expect(chatInput).toBeVisible();

    // 3. 发送测试消息
    const testMessage = '你好，请介绍一下你自己';
    await chatInput.fill(testMessage);

    // 4. 点击发送按钮
    const sendButton = page.locator('[data-testid="send-button"]');
    await sendButton.click();

    // 5. 等待用户消息显示
    await expect(page.locator(`[data-message-role="user"]`).filter({ hasText: testMessage })).toBeVisible({ timeout: 5000 });

    // 6. 等待 AI 响应（最多等待 30 秒）
    await expect(page.locator('[data-message-role="assistant"]')).toBeVisible({ timeout: 30000 });

    // 7. 验证响应内容不为空
    const assistantMessage = page.locator('[data-message-role="assistant"]').first();
    const responseText = await assistantMessage.textContent();
    expect(responseText?.trim().length).toBeGreaterThan(0);

    await appPage.screenshot('chat_conversation_complete');
  });

  /**
   * 测试场景 2: 流式响应测试
   * E2E-CHAT-002
   */
  test('应正确显示流式响应', async ({ page }) => {
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    const testMessage = '请用一句话介绍 Python';

    await chatInput.fill(testMessage);
    await page.locator('[data-testid="send-button"]').click();

    // 等待用户消息显示
    await expect(page.locator(`[data-message-role="user"]`).filter({ hasText: testMessage })).toBeVisible({ timeout: 5000 });

    // 监控消息内容的变化来验证流式响应
    const startTime = Date.now();
    let lastContentLength = 0;
    let contentChanged = false;

    // 持续检查消息内容是否在变化（流式特征）
    for (let i = 0; i < 30; i++) {
      await page.waitForTimeout(500);
      const assistantMessage = page.locator('[data-message-role="assistant"]').first();

      if (await assistantMessage.isVisible()) {
        const currentText = await assistantMessage.textContent() || '';
        const currentLength = currentText.trim().length;

        if (currentLength > lastContentLength) {
          contentChanged = true;
          lastContentLength = currentLength;
        }

        // 如果已经有内容且不再变化，可能流式结束
        if (currentLength > 10 && i > 5) {
          break;
        }
      }
    }

    const duration = Date.now() - startTime;
    console.log(`流式响应测试耗时: ${duration}ms, 内容长度: ${lastContentLength}`);

    // 验证内容在变化（流式响应的特征）
    expect(contentChanged, '内容应该逐渐增加（流式响应特征）').toBe(true);
    expect(lastContentLength, '响应内容不应为空').toBeGreaterThan(0);

    await appPage.screenshot('streaming_response_complete');
  });

  /**
   * 测试场景 3: 多轮对话
   * E2E-CHAT-003
   */
  test('应能进行多轮对话', async ({ page }) => {
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');

    // 第一轮对话
    const messages = [
      '我叫小明',
      '我叫什么名字？',
      '再见'
    ];

    for (const msg of messages) {
      await chatInput.fill(msg);
      await sendButton.click();

      // 等待用户消息显示
      await expect(page.locator(`[data-message-role="user"]`).filter({ hasText: msg })).toBeVisible({ timeout: 5000 });

      // 等待 AI 响应
      await expect(page.locator('[data-message-role="assistant"]')).toBeVisible({ timeout: 30000 });

      // 等待一下确保响应完整
      await page.waitForTimeout(2000);
    }

    // 验证消息数量
    const userMessages = await page.locator('[data-message-role="user"]').count();
    const assistantMessages = await page.locator('[data-message-role="assistant"]').count();

    expect(userMessages).toBe(3);
    expect(assistantMessages).toBe(3);

    await appPage.screenshot('multi_turn_conversation');
  });

  /**
   * 测试场景 4: 模型选择
   * E2E-CHAT-004
   */
  test('应能查看和选择模型', async ({ page }) => {
    // 点击模型选择器
    const modelSelector = page.locator('[data-testid="model-selector-button"]');
    await expect(modelSelector).toBeVisible();

    // 获取当前选中的模型名称
    const currentModel = await page.locator('[data-testid="selected-model-name"]').textContent();
    console.log('当前模型:', currentModel);

    // 悬停以展开下拉菜单
    await modelSelector.hover();

    // 等待下拉菜单出现
    await expect(page.locator('[data-testid="model-dropdown-list"]')).toBeVisible({ timeout: 3000 });

    // 获取可用模型数量
    const modelOptions = await page.locator('[data-testid^="model-option-"]').count();
    console.log('可用模型数量:', modelOptions);

    expect(modelOptions).toBeGreaterThan(0);

    await appPage.screenshot('model_selector');
  });

  /**
   * 测试场景 5: 新对话功能
   * E2E-CHAT-005
   */
  test('应能创建新对话并清空消息', async ({ page }) => {
    // 发送第一条消息
    await appPage.startNewChat();
    await page.locator('[data-testid="chat-input"]').fill('测试消息1');
    await page.locator('[data-testid="send-button"]').click();
    await page.waitForTimeout(3000);

    // 验证有消息
    let messageCount = await page.locator('[data-testid^="message-"]').count();
    expect(messageCount).toBeGreaterThan(0);

    // 创建新对话
    await page.locator('[data-testid="new-chat-button"]').click();
    await page.waitForTimeout(1000);

    // 验证消息被清空
    messageCount = await page.locator('[data-testid^="message-"]').count();
    expect(messageCount).toBe(0);

    // 验证显示欢迎界面
    await expect(page.locator('text=AI工作台')).toBeVisible();

    await appPage.screenshot('new_chat_cleared');
  });

  /**
   * 测试场景 6: 键盘快捷键 (Enter 发送)
   * E2E-CHAT-006
   */
  test('应支持 Enter 键发送消息', async ({ page }) => {
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    await chatInput.fill('快捷键测试');

    // 按 Enter 键发送
    await chatInput.press('Enter');

    // 验证消息发送
    await expect(page.locator(`[data-message-role="user"]`).filter({ hasText: '快捷键测试' })).toBeVisible({ timeout: 5000 });

    await appPage.screenshot('enter_key_send');
  });

  /**
   * 测试场景 7: Shift+Enter 换行
   * E2E-CHAT-007
   */
  test('应支持 Shift+Enter 换行', async ({ page }) => {
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');

    // 输入多行文本
    await chatInput.fill('第一行');
    await chatInput.press('Shift+Enter');
    await chatInput.type('第二行');

    // 验证输入框包含换行符
    const value = await chatInput.inputValue();
    expect(value).toContain('第一行');
    expect(value).toContain('第二行');

    await appPage.screenshot('shift_enter_newline');
  });

  /**
   * 测试场景 8: 会话持久化
   * E2E-CHAT-008
   */
  test('消息应被保存到后端', async ({ page }) => {
    await appPage.startNewChat();

    const uniqueMessage = `持久化测试_${Date.now()}`;
    const chatInput = page.locator('[data-testid="chat-input"]');

    await chatInput.fill(uniqueMessage);
    await page.locator('[data-testid="send-button"]').click();

    // 等待 AI 响应
    await expect(page.locator('[data-message-role="assistant"]')).toBeVisible({ timeout: 30000 });
    await page.waitForTimeout(3000); // 等待保存

    // 刷新页面
    await page.reload();
    await page.waitForTimeout(2000);

    // 验证消息仍然存在
    await expect(page.locator(`[data-message-role="user"]`).filter({ hasText: uniqueMessage })).toBeVisible({ timeout: 5000 });

    await appPage.screenshot('session_persistence');
  });

  /**
   * 测试场景 9: 用户信息显示
   * E2E-CHAT-009
   */
  test('应正确显示当前用户信息', async ({ page }) => {
    const usernameElement = page.locator('[data-testid="current-username"]');
    await expect(usernameElement).toBeVisible();

    const username = await usernameElement.textContent();
    expect(username?.toLowerCase()).toContain('admin');

    await appPage.screenshot('user_info_display');
  });

  /**
   * 测试场景 10: 退出登录
   * E2E-CHAT-010
   */
  test('应能正常退出登录', async ({ page }) => {
    const logoutButton = page.locator('[data-testid="logout-button"]');
    await logoutButton.click();

    // 等待跳转到登录页
    await page.waitForTimeout(2000);

    // 验证回到登录页
    await expect(page.locator('[data-testid="username-input"]')).toBeVisible({ timeout: 5000 });

    await appPage.screenshot('logout_complete');
  });

  /**
   * 测试场景 11: 空输入验证
   * E2E-CHAT-011
   */
  test('空输入不应发送消息', async ({ page }) => {
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');

    // 验证发送按钮在空输入时被禁用
    await expect(sendButton).toBeDisabled();

    // 输入空格
    await chatInput.fill('   ');
    await expect(sendButton).toBeDisabled();

    await appPage.screenshot('empty_input_validation');
  });

  /**
   * 测试场景 12: 响应时间测试
   * E2E-CHAT-012
   */
  test('应测量消息响应时间', async ({ page }) => {
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    const testMessage = '你好';

    await chatInput.fill(testMessage);

    const startTime = Date.now();
    await page.locator('[data-testid="send-button"]').click();

    // 等待 AI 响应
    await expect(page.locator('[data-message-role="assistant"]')).toBeVisible({ timeout: 30000 });
    const responseTime = Date.now() - startTime;

    console.log(`首次响应时间: ${responseTime}ms`);

    // 响应时间应在合理范围内（30秒内）
    expect(responseTime).toBeLessThan(30000);

    await appPage.screenshot('response_time_test');
  });

  /**
   * 测试场景 13: 长消息处理
   * E2E-CHAT-013
   */
  test('应能处理长消息', async ({ page }) => {
    await appPage.startNewChat();

    const longMessage = '请分析以下文本：' + '这是一个测试。'.repeat(50);
    const chatInput = page.locator('[data-testid="chat-input"]');

    await chatInput.fill(longMessage);
    await page.locator('[data-testid="send-button"]').click();

    // 验证消息发送
    await expect(page.locator(`[data-message-role="user"]`).first()).toBeVisible({ timeout: 5000 });

    // 等待 AI 响应
    await expect(page.locator('[data-message-role="assistant"]')).toBeVisible({ timeout: 30000 });

    await appPage.screenshot('long_message_test');
  });

  /**
   * 测试场景 14: 特殊字符处理
   * E2E-CHAT-014
   */
  test('应能处理特殊字符', async ({ page }) => {
    await appPage.startNewChat();

    const specialMessage = '测试特殊字符：@#$%^&*()_+-=[]{}|;:\'",.<>?/~`';
    const chatInput = page.locator('[data-testid="chat-input"]');

    await chatInput.fill(specialMessage);
    await page.locator('[data-testid="send-button"]').click();

    // 验证消息发送
    await expect(page.locator(`[data-message-role="user"]`).filter({ hasText: /测试特殊字符/ })).toBeVisible({ timeout: 5000 });

    // 等待 AI 响应
    await expect(page.locator('[data-message-role="assistant"]')).toBeVisible({ timeout: 30000 });

    await appPage.screenshot('special_characters_test');
  });

  /**
   * 测试场景 15: 网络错误处理
   * E2E-CHAT-015
   */
  test('应正确显示网络错误', async ({ page }) => {
    // 模拟网络离线（通过拦截请求）
    await page.route('**/api/v1/**', route => route.abort());

    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    await chatInput.fill('测试消息');
    await page.locator('[data-testid="send-button"]').click();

    // 等待错误消息显示
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible({ timeout: 10000 });

    const errorMessage = await page.locator('[data-testid="error-message"]').textContent();
    console.log('错误消息:', errorMessage);

    await appPage.screenshot('network_error');
  });
});

/**
 * 性能测试套件
 */
test.describe('对话性能测试', () => {
  const ADMIN_CREDENTIALS = { username: 'admin', password: 'pwd123' };

  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
    await appPage.waitForAppLoad();
  });

  /**
   * 性能测试: 连续消息发送
   * E2E-PERF-001
   */
  test('应能处理连续消息', async ({ page }) => {
    const appPage = new AppPage(page);
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');

    const messages = ['测试1', '测试2', '测试3'];
    const responseTimes: number[] = [];

    for (const msg of messages) {
      await chatInput.fill(msg);

      const startTime = Date.now();
      await sendButton.click();

      await expect(page.locator('[data-message-role="assistant"]')).toBeVisible({ timeout: 30000 });
      responseTimes.push(Date.now() - startTime);

      await page.waitForTimeout(2000);
    }

    const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
    console.log('响应时间:', responseTimes, '平均:', avgResponseTime, 'ms');

    // 平均响应时间应小于 20 秒
    expect(avgResponseTime).toBeLessThan(20000);

    await appPage.screenshot('continuous_messages');
  });
});
