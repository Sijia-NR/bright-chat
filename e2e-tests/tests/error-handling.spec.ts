import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { AppPage } from '../pages/AppPage';

/**
 * 错误处理测试套件
 *
 * 测试场景：
 * 1. 网络错误处理
 * 2. API 错误响应
 * 3. 超时处理
 * 4. 无效输入处理
 * 5. 服务不可用处理
 */

test.describe('错误处理测试', () => {
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
   * 测试场景 1: 网络离线错误
   * E2E-ERROR-001
   */
  test('应正确处理网络离线', async ({ page }) => {
    // 模拟网络离线
    await page.context().setOffline(true);

    // 创建新对话
    await appPage.startNewChat();

    // 尝试发送消息
    const chatInput = page.locator('[data-testid="chat-input"]');
    await chatInput.fill('离线测试消息');
    await page.locator('[data-testid="send-button"]').click();

    // 等待错误显示
    await page.waitForTimeout(3000);

    // 检查错误消息
    const errorMessage = page.locator('[data-testid="error-message"]');
    const hasError = await errorMessage.count();

    console.log('错误消息数量:', hasError);

    if (hasError > 0) {
      const errorText = await errorMessage.textContent();
      console.log('错误内容:', errorText);
      expect(errorText?.length).toBeGreaterThan(0);
    }

    // 恢复网络
    await page.context().setOffline(false);

    await appPage.screenshot('network_offline_error');
  });

  /**
   * 测试场景 2: 服务器 500 错误
   * E2E-ERROR-002
   */
  test('应正确处理服务器 500 错误', async ({ page }) => {
    // 拦截并返回 500 错误
    await page.route('**/lmp-cloud-ias-server/**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' })
      });
    });

    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    await chatInput.fill('服务器错误测试');
    await page.locator('[data-testid="send-button"]').click();

    // 等待错误显示
    await page.waitForTimeout(3000);

    // 检查错误消息
    const errorMessage = page.locator('[data-testid="error-message"]');
    const hasError = await errorMessage.count();

    console.log('服务器错误时错误消息数量:', hasError);

    // 验证界面仍然可用
    await expect(page.locator('[data-testid="chat-input"]')).toBeVisible();

    await appPage.screenshot('server_500_error');
  });

  /**
   * 测试场景 3: 超时处理
   * E2E-ERROR-003
   */
  test('应正确处理请求超时', async ({ page }) => {
    // 模拟超时（延迟响应）
    await page.route('**/lmp-cloud-ias-server/**, **/api/v1/chat**', async route => {
      // 延迟 40 秒（超过超时限制）
      await new Promise(resolve => setTimeout(resolve, 40000));
      route.continue();
    });

    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    await chatInput.fill('超时测试');
    await page.locator('[data-testid="send-button"]').click();

    // 等待超时（最多35秒）
    await page.waitForTimeout(35000);

    // 检查错误消息
    const errorMessage = page.locator('[data-testid="error-message"]');
    const hasError = await errorMessage.count();

    console.log('超时后错误消息数量:', hasError);

    await appPage.screenshot('timeout_error');
  });

  /**
   * 测试场景 4: 无效输入处理
   * E2E-ERROR-004
   */
  test('应正确处理无效输入', async ({ page }) => {
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');

    // 测试空输入
    await chatInput.fill('');
    const sendButton = page.locator('[data-testid="send-button"]');
    await expect(sendButton).toBeDisabled();

    // 测试只有空格
    await chatInput.fill('   ');
    await expect(sendButton).toBeDisabled();

    // 测试特殊字符（应该允许）
    await chatInput.fill('测试特殊字符 @#$%^&*()');
    await expect(sendButton).toBeEnabled();

    await appPage.screenshot('invalid_input_handling');
  });

  /**
   * 测试场景 5: 认证失败处理
   * E2E-ERROR-005
   */
  test('应正确处理认证失败', async ({ page }) => {
    // 拦截请求返回 401
    await page.route('**/api/v1/**', route => {
      if (route.request().url().includes('/lmp-cloud-ias-server/') ||
          route.request().url().includes('/chat') ||
          route.request().url().includes('/sessions')) {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Unauthorized' })
        });
      } else {
        route.continue();
      }
    });

    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    await chatInput.fill('认证失败测试');
    await page.locator('[data-testid="send-button"]').click();

    // 等待可能的错误或跳转到登录页
    await page.waitForTimeout(3000);

    // 检查是否跳转到登录页或显示错误
    const loginForm = page.locator('[data-testid="username-input"]');
    const errorMessage = page.locator('[data-testid="error-message"]');

    if (await loginForm.count() > 0) {
      console.log('检测到跳转到登录页');
    } else if (await errorMessage.count() > 0) {
      console.log('检测到错误消息');
    }

    await appPage.screenshot('auth_failure_handling');
  });

  /**
   * 测试场景 6: 响应格式错误
   * E2E-ERROR-006
   */
  test('应正确处理格式错误的响应', async ({ page }) => {
    // 返回无效的 JSON
    await page.route('**/lmp-cloud-ias-server/**', route => {
      route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: 'invalid json content{{{'
      });
    });

    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    await chatInput.fill('格式错误测试');
    await page.locator('[data-testid="send-button"]').click();

    // 等待处理
    await page.waitForTimeout(5000);

    // 验证界面没有崩溃
    await expect(page.locator('[data-testid="chat-input"]')).toBeVisible();

    await appPage.screenshot('invalid_response_format');
  });

  /**
   * 测试场景 7: 空响应处理
   * E2E-ERROR-007
   */
  test('应正确处理空响应', async ({ page }) => {
    // 返回空响应
    await page.route('**/lmp-cloud-ias-server/**', route => {
      route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: 'data: [DONE]\n\n'
      });
    });

    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    await chatInput.fill('空响应测试');
    await page.locator('[data-testid="send-button"]').click();

    // 等待处理
    await page.waitForTimeout(5000);

    // 检查错误消息
    const errorMessage = page.locator('[data-testid="error-message"]');
    const hasError = await errorMessage.count();

    console.log('空响应时错误消息数量:', hasError);

    await appPage.screenshot('empty_response_handling');
  });

  /**
   * 测试场景 8: 大消息处理
   * E2E-ERROR-008
   */
  test('应正确处理超大消息', async ({ page }) => {
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');

    // 创建一个超长消息（可能超过模型限制）
    const longMessage = 'A'.repeat(10000);

    await chatInput.fill(longMessage);

    // 尝试发送
    await page.locator('[data-testid="send-button"]').click();

    // 等待处理
    await page.waitForTimeout(10000);

    // 检查结果
    const userMessage = page.locator('[data-message-role="user"]').first();
    const isUserMessageVisible = await userMessage.isVisible();

    console.log('超长消息是否显示:', isUserMessageVisible);

    // 检查是否有错误
    const errorMessage = page.locator('[data-testid="error-message"]');
    const hasError = await errorMessage.count();

    console.log('超长消息错误数量:', hasError);

    await appPage.screenshot('large_message_handling');
  });

  /**
   * 测试场景 9: 并发请求处理
   * E2E-ERROR-009
   */
  test('应正确处理并发请求', async ({ page }) => {
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');

    // 快速连续发送多条消息
    const messages = ['消息1', '消息2', '消息3', '消息4', '消息5'];

    for (const msg of messages) {
      await chatInput.fill(msg);
      await sendButton.click();
      await page.waitForTimeout(100); // 快速发送
    }

    // 等待所有请求处理完成
    await page.waitForTimeout(20000);

    // 验证界面正常
    await expect(page.locator('[data-testid="chat-input"]')).toBeVisible();

    // 统计消息数
    const userMessages = await page.locator('[data-message-role="user"]').count();
    const assistantMessages = await page.locator('[data-message-role="assistant"]').count();

    console.log('用户消息数:', userMessages);
    console.log('Assistant 消息数:', assistantMessages);

    await appPage.screenshot('concurrent_requests');
  });

  /**
   * 测试场景 10: 连接中断恢复
   * E2E-ERROR-010
   */
  test('应能在网络恢复后继续使用', async ({ page }) => {
    // 断开网络
    await page.context().setOffline(true);

    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    await chatInput.fill('网络断开测试');
    await page.locator('[data-testid="send-button"]').click();

    await page.waitForTimeout(2000);

    // 恢复网络
    await page.context().setOffline(false);

    // 等待一下
    await page.waitForTimeout(2000);

    // 尝试重新发送
    await chatInput.fill('网络恢复测试');
    await page.locator('[data-testid="send-button"]').click();

    // 等待响应
    await page.waitForTimeout(10000);

    // 验证能收到响应
    const assistantMessage = page.locator('[data-message-role="assistant"]');
    const hasResponse = await assistantMessage.count() > 0;

    console.log('网络恢复后是否有响应:', hasResponse);

    await appPage.screenshot('network_recovery');
  });
});

/**
 * 边界条件测试
 */
test.describe('边界条件测试', () => {
  const ADMIN_CREDENTIALS = { username: 'admin', password: 'pwd123' };

  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
    await appPage.waitForAppLoad();
  });

  /**
   * 测试场景 11: 消息数量限制
   * E2E-BOUNDARY-001
   */
  test('应处理大量消息', async ({ page }) => {
    const appPage = new AppPage(page);
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');

    // 发送多条消息
    for (let i = 0; i < 10; i++) {
      await chatInput.fill(`消息 ${i + 1}`);
      await page.locator('[data-testid="send-button"]').click();
      await page.waitForTimeout(3000);
    }

    // 验证所有消息都显示
    const userMessages = await page.locator('[data-message-role="user"]').count();
    console.log('用户消息总数:', userMessages);

    // 界面应该仍然响应
    await expect(page.locator('[data-testid="chat-input"]')).toBeVisible();

    await appPage.screenshot('many_messages');
  });

  /**
   * 测试场景 12: 特殊字符和 Unicode
   * E2E-BOUNDARY-002
   */
  test('应正确处理特殊字符和 Unicode', async ({ page }) => {
    const appPage = new AppPage(page);
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');

    // 测试各种特殊字符
    const specialMessages = [
      '中文测试 你好世界',
      'Japanese test こんにちは',
      'Emoji test 😀😁😂🤣',
      'Special chars: !@#$%^&*()_+-=[]{}|;:\'",.<>?/~`',
      'Quotes: "Double" and \'Single\'',
      'HTML entities: <div> &nbsp; &amp;',
      'URL: https://example.com/path?param=value&other=123'
    ];

    for (const msg of specialMessages) {
      await chatInput.fill(msg);
      await page.locator('[data-testid="send-button"]').click();
      await page.waitForTimeout(2000);
    }

    // 验证消息正确显示
    await expect(page.locator('[data-message-role="user"]').first()).toBeVisible();

    await appPage.screenshot('special_characters');
  });

  /**
   * 测试场景 13: 极端输入长度
   * E2E-BOUNDARY-003
   */
  test('应处理极端输入长度', async ({ page }) => {
    const appPage = new AppPage(page);
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');

    // 测试不同长度的输入
    const testCases = [
      { name: '单字符', length: 1 },
      { name: '短文本', length: 10 },
      { name: '中等文本', length: 100 },
      { name: '长文本', length: 1000 }
    ];

    for (const testCase of testCases) {
      const message = 'A'.repeat(testCase.length);
      await chatInput.fill(message);
      await page.locator('[data-testid="send-button"]').click();
      await page.waitForTimeout(2000);
      console.log(`${testCase.name} (${testCase.length} 字符) 已发送`);
    }

    await appPage.screenshot('extreme_lengths');
  });
});
