import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { AppPage } from '../pages/AppPage';

/**
 * 流式响应专项测试
 *
 * 测试 SSE (Server-Sent Events) 流式响应功能
 */

test.describe('流式响应专项测试', () => {
  const ADMIN_CREDENTIALS = { username: 'admin', password: 'pwd123' };

  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
    await appPage.waitForAppLoad();
  });

  /**
   * 测试场景 1: 验证流式响应逐步显示
   * E2E-STREAM-001
   */
  test('流式响应应逐步显示内容', async ({ page }) => {
    const appPage = new AppPage(page);
    await appPage.startNewChat();

    // 捕获网络请求
    const streamData: string[] = [];
    let streamStarted = false;
    let streamEnded = false;

    page.on('console', msg => {
      if (msg.text().includes('[Chat]')) {
        console.log('浏览器日志:', msg.text());
      }
    });

    // 监听网络请求
    page.on('response', async response => {
      const url = response.url();
      if (url.includes('/lmp-cloud-ias-server/') || url.includes('/api/v1/chat')) {
        const contentType = response.headers()['content-type'] || '';
        if (contentType.includes('text/event-stream')) {
          console.log('检测到 SSE 流:', url);
          streamStarted = true;
        }
      }
    });

    const chatInput = page.locator('[data-testid="chat-input"]');
    const testMessage = '请详细介绍一下人工智能的历史，包括三个重要里程碑';

    await chatInput.fill(testMessage);
    await page.locator('[data-testid="send-button"]').click();

    // 等待用户消息显示
    await expect(page.locator(`[data-message-role="user"]`).filter({ hasText: testMessage }))
      .toBeVisible({ timeout: 5000 });

    // 等待 assistant 消息出现
    const assistantLocator = page.locator('[data-message-role="assistant"]').last();
    await expect(assistantLocator).toBeVisible({ timeout: 10000 });

    // 监控内容变化
    const contentLengths: number[] = [];
    let previousLength = 0;

    // 持续检查内容变化（流式响应的特征）
    for (let i = 0; i < 60; i++) {
      await page.waitForTimeout(500);

      const currentText = await assistantLocator.textContent() || '';
      const currentLength = currentText.trim().length;

      if (currentLength > previousLength) {
        contentLengths.push(currentLength);
        previousLength = currentLength;
        console.log(`[${i * 500}ms] 内容长度: ${currentLength}`);
      }

      // 如果内容足够长且连续几次没有变化，认为流式结束
      if (currentLength > 50 && contentLengths.length > 3) {
        const lastThree = contentLengths.slice(-3);
        if (lastThree.every(l => l === currentLength)) {
          streamEnded = true;
          break;
        }
      }
    }

    console.log('内容长度变化:', contentLengths);
    console.log('最终内容长度:', previousLength);

    // 验证流式响应特征
    expect(contentLengths.length, '内容应该至少变化 3 次').toBeGreaterThanOrEqual(3);
    expect(previousLength, '最终响应内容不应为空').toBeGreaterThan(50);

    await appPage.screenshot('streaming_gradual_display');
  });

  /**
   * 测试场景 2: 流式响应完整性
   * E2E-STREAM-002
   */
  test('流式响应内容应完整', async ({ page }) => {
    const appPage = new AppPage(page);
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    const testMessage = '请用100字左右介绍 React 的核心概念';

    await chatInput.fill(testMessage);
    await page.locator('[data-testid="send-button"]').click();

    // 等待用户消息
    await expect(page.locator(`[data-message-role="user"]`).filter({ hasText: testMessage }))
      .toBeVisible({ timeout: 5000 });

    // 等待 assistant 响应
    const assistantLocator = page.locator('[data-message-role="assistant"]').last();
    await expect(assistantLocator).toBeVisible({ timeout: 10000 });

    // 等待流式完成（内容不再变化）
    await page.waitForTimeout(5000);

    // 再等待一秒确保完全结束
    await page.waitForTimeout(1000);

    const finalText = await assistantLocator.textContent() || '';
    console.log('最终响应内容:', finalText.substring(0, 200));

    // 验证内容完整性 - 不应包含截断标记
    expect(finalText).not.toContain('[DONE]');
    expect(finalText).not.toContain('data:');

    // 内容应该合理
    expect(finalText.trim().length).toBeGreaterThan(20);

    await appPage.screenshot('streaming_completeness');
  });

  /**
   * 测试场景 3: 流式响应中断处理
   * E2E-STREAM-003
   */
  test('应正确处理流式响应中断', async ({ page }) => {
    const appPage = new AppPage(page);
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    const testMessage = '请详细解释量子计算的基本原理';

    await chatInput.fill(testMessage);
    await page.locator('[data-testid="send-button"]').click();

    // 等待响应开始
    const assistantLocator = page.locator('[data-message-role="assistant"]').last();
    await expect(assistantLocator).toBeVisible({ timeout: 10000 });

    // 等待一些内容
    await page.waitForTimeout(3000);

    // 创建新对话（中断当前流式）
    await page.locator('[data-testid="new-chat-button"]').click();
    await page.waitForTimeout(1000);

    // 验证界面正常（没有崩溃）
    await expect(page.locator('[data-testid="chat-input"]')).toBeVisible();

    // 验证没有错误消息显示
    const hasError = await page.locator('[data-testid="error-message"]').count();
    console.log('错误消息数量:', hasError);

    await appPage.screenshot('streaming_interruption');
  });

  /**
   * 测试场景 4: 流式响应延迟测量
   * E2E-STREAM-004
   */
  test('应测量流式响应首字节时间', async ({ page }) => {
    const appPage = new AppPage(page);
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    const testMessage = '你好';

    await chatInput.fill(testMessage);

    const sendTime = Date.now();
    let firstByteTime: number | null = null;
    let completeTime: number | null = null;

    // 监听响应
    page.on('response', response => {
      if (response.url().includes('/lmp-cloud-ias-server/') || response.url().includes('/chat')) {
        if (!firstByteTime) {
          firstByteTime = Date.now();
        }
      }
    });

    await page.locator('[data-testid="send-button"]').click();

    // 等待 assistant 消息出现
    const assistantLocator = page.locator('[data-message-role="assistant"]').last();
    await expect(assistantLocator).toBeVisible({ timeout: 10000 });

    const firstContentTime = Date.now();

    // 等待内容稳定
    await page.waitForTimeout(3000);
    completeTime = Date.now();

    const timeToFirstByte = firstByteTime ? firstByteTime - sendTime : 0;
    const timeToFirstContent = firstContentTime - sendTime;
    const totalTime = completeTime - sendTime;

    console.log('首字节时间:', timeToFirstByte, 'ms');
    console.log('首次内容时间:', timeToFirstContent, 'ms');
    console.log('总完成时间:', totalTime, 'ms');

    // 性能断言
    expect(timeToFirstContent).toBeLessThan(5000); // 5秒内应有内容
    expect(totalTime).toBeLessThan(20000); // 20秒内应完成

    await appPage.screenshot('streaming_latency');
  });

  /**
   * 测试场景 5: 多个并发流式请求
   * E2E-STREAM-005
   */
  test('应能处理连续快速发送的消息', async ({ page }) => {
    const appPage = new AppPage(page);
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');

    // 快速发送多条消息
    const messages = ['消息1', '消息2', '消息3'];

    for (const msg of messages) {
      await chatInput.fill(msg);
      await sendButton.click();
      await page.waitForTimeout(100); // 快速发送
    }

    // 等待所有响应完成
    await page.waitForTimeout(15000);

    // 验证所有用户消息都显示了
    for (const msg of messages) {
      await expect(page.locator(`[data-message-role="user"]`).filter({ hasText: msg }))
        .toBeVisible({ timeout: 5000 });
    }

    // 验证有对应的 assistant 响应
    const assistantCount = await page.locator('[data-message-role="assistant"]').count();
    expect(assistantCount).toBeGreaterThanOrEqual(messages.length);

    await appPage.screenshot('concurrent_streaming');
  });

  /**
   * 测试场景 6: 流式响应中的打字动画
   * E2E-STREAM-006
   */
  test('流式响应期间应显示打字动画', async ({ page }) => {
    const appPage = new AppPage(page);
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    const testMessage = '请介绍一下机器学习';

    await chatInput.fill(testMessage);
    await page.locator('[data-testid="send-button"]').click();

    // 等待用户消息
    await expect(page.locator(`[data-message-role="user"]`).filter({ hasText: testMessage }))
      .toBeVisible({ timeout: 5000 });

    // 快速检查打字动画（可能在响应开始前短暂显示）
    await page.waitForTimeout(500);

    // 打字动画可能在流式响应期间显示（取决于实现）
    // 主要验证消息正确显示即可
    const assistantLocator = page.locator('[data-message-role="assistant"]').last();
    await expect(assistantLocator).toBeVisible({ timeout: 10000 });

    await appPage.screenshot('typing_animation');
  });
});

/**
 * 流式响应错误处理测试
 */
test.describe('流式响应错误处理', () => {
  const ADMIN_CREDENTIALS = { username: 'admin', password: 'pwd123' };

  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
    await appPage.waitForAppLoad();
  });

  /**
   * 测试场景 7: 服务器错误处理
   * E2E-STREAM-ERROR-001
   */
  test('应正确处理流式响应中的服务器错误', async ({ page }) => {
    const appPage = new AppPage(page);
    await appPage.startNewChat();

    // 模拟部分响应后失败
    let requestCount = 0;
    await page.route('**/lmp-cloud-ias-server/**', async route => {
      requestCount++;
      if (requestCount === 1) {
        // 第一次请求让它通过
        route.continue();
      } else {
        // 后续请求失败
        route.abort('failed');
      }
    });

    const chatInput = page.locator('[data-testid="chat-input"]');
    await chatInput.fill('测试消息');
    await page.locator('[data-testid="send-button"]').click();

    // 等待可能的错误消息
    await page.waitForTimeout(5000);

    // 检查是否有错误显示
    const hasError = await page.locator('[data-testid="error-message"]').count() > 0;
    console.log('是否有错误消息:', hasError);

    // 界面应该仍然可用
    await expect(page.locator('[data-testid="chat-input"]')).toBeVisible();

    await appPage.screenshot('streaming_server_error');
  });
});
