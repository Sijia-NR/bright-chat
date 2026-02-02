import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { AppPage } from '../pages/AppPage';

/**
 * 性能测试套件
 *
 * 测试场景：
 * 1. 消息发送响应时间
 * 2. 流式响应延迟
 * 3. 页面加载时间
 * 4. 内存使用监控
 * 5. 并发性能测试
 */

// 性能指标存储
const performanceMetrics: {
  testName: string;
  metricName: string;
  value: number;
  timestamp: number;
}[] = [];

function recordMetric(testName: string, metricName: string, value: number) {
  const metric = {
    testName,
    metricName,
    value,
    timestamp: Date.now()
  };
  performanceMetrics.push(metric);
  console.log(`[性能指标] ${testName} - ${metricName}: ${value}ms`);
}

test.describe('性能测试', () => {
  const ADMIN_CREDENTIALS = { username: 'admin', password: 'pwd123' };

  /**
   * 测试场景 1: 登录性能测试
   * E2E-PERF-001
   */
  test('登录应在合理时间内完成', async ({ page }) => {
    const startTime = Date.now();

    const loginPage = new LoginPage(page);
    await loginPage.goto();

    const gotoTime = Date.now();

    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);

    const loginTime = Date.now();

    const appPage = new AppPage(page);
    await appPage.waitForAppLoad();

    const loadTime = Date.now();

    // 记录性能指标
    recordMetric('登录流程', '页面导航耗时', gotoTime - startTime);
    recordMetric('登录流程', '登录请求耗时', loginTime - gotoTime);
    recordMetric('登录流程', '应用加载耗时', loadTime - loginTime);
    recordMetric('登录流程', '总耗时', loadTime - startTime);

    // 性能断言
    expect(loadTime - startTime).toBeLessThan(10000); // 总耗时应在10秒内

    await loginPage.screenshot('login_performance');
  });

  /**
   * 测试场景 2: 首次消息响应时间
   * E2E-PERF-002
   */
  test('首次消息响应时间应在可接受范围内', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
    await appPage.waitForAppLoad();

    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    const testMessage = '你好，请简单介绍一下你自己';

    await chatInput.fill(testMessage);

    const sendStartTime = Date.now();
    await page.locator('[data-testid="send-button"]').click();

    // 等待 assistant 消息出现
    await expect(page.locator('[data-message-role="assistant"]')).toBeVisible({ timeout: 30000 });
    const firstByteTime = Date.now();

    // 等待内容稳定
    await page.waitForTimeout(3000);
    const completeTime = Date.now();

    recordMetric('首次消息', '首字节时间 (TTFB)', firstByteTime - sendStartTime);
    recordMetric('首次消息', '完成时间', completeTime - sendStartTime);

    // 性能断言
    expect(firstByteTime - sendStartTime).toBeLessThan(5000); // 5秒内应有响应
    expect(completeTime - sendStartTime).toBeLessThan(15000); // 15秒内应完成

    await appPage.screenshot('first_message_performance');
  });

  /**
   * 测试场景 3: 流式响应速度测试
   * E2E-PERF-003
   */
  test('流式响应应持续接收数据', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
    await appPage.waitForAppLoad();

    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    const testMessage = '请详细介绍人工智能的发展历史，包括至少三个重要里程碑';

    await chatInput.fill(testMessage);

    const startTime = Date.now();
    await page.locator('[data-testid="send-button"]').click();

    // 等待用户消息
    await expect(page.locator(`[data-message-role="user"]`).filter({ hasText: testMessage }))
      .toBeVisible({ timeout: 5000 });

    const assistantLocator = page.locator('[data-message-role="assistant"]').last();
    await expect(assistantLocator).toBeVisible({ timeout: 10000 });

    const firstContentTime = Date.now();

    // 监控内容变化
    const updateIntervals: number[] = [];
    let lastLength = 0;
    let lastUpdateTime = firstContentTime;

    for (let i = 0; i < 30; i++) {
      await page.waitForTimeout(500);

      const currentText = await assistantLocator.textContent() || '';
      const currentLength = currentText.trim().length;

      if (currentLength > lastLength) {
        const interval = Date.now() - lastUpdateTime;
        updateIntervals.push(interval);
        lastLength = currentLength;
        lastUpdateTime = Date.now();
      }

      // 如果内容很长且不再变化，提前结束
      if (currentLength > 200 && i > 10) {
        const recentUpdates = updateIntervals.slice(-3);
        if (recentUpdates.every(i => i > 2000)) {
          break;
        }
      }
    }

    const completeTime = Date.now();

    // 计算平均更新间隔
    const avgInterval = updateIntervals.length > 0
      ? updateIntervals.reduce((a, b) => a + b, 0) / updateIntervals.length
      : 0;

    recordMetric('流式响应', '首次内容时间', firstContentTime - startTime);
    recordMetric('流式响应', '平均更新间隔', avgInterval);
    recordMetric('流式响应', '总完成时间', completeTime - startTime);
    recordMetric('流式响应', '最终内容长度', lastLength);
    recordMetric('流式响应', '更新次数', updateIntervals.length);

    console.log('更新间隔 (ms):', updateIntervals);

    // 性能断言
    expect(firstContentTime - startTime).toBeLessThan(3000); // 3秒内应有内容
    expect(avgInterval).toBeLessThan(1000); // 平均更新间隔应小于1秒

    await appPage.screenshot('streaming_performance');
  });

  /**
   * 测试场景 4: 连续消息平均响应时间
   * E2E-PERF-004
   */
  test('连续消息响应时间应保持稳定', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
    await appPage.waitForAppLoad();

    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');
    const responseTimes: number[] = [];

    const messages = [
      '第一个问题：什么是人工智能？',
      '第二个问题：什么是机器学习？',
      '第三个问题：什么是深度学习？',
      '第四个问题：什么是神经网络？',
      '第五个问题：什么是自然语言处理？'
    ];

    for (const msg of messages) {
      await chatInput.fill(msg);

      const startTime = Date.now();
      await page.locator('[data-testid="send-button"]').click();

      await expect(page.locator('[data-message-role="assistant"]')).toBeVisible({ timeout: 30000 });
      await page.waitForTimeout(1000); // 等待内容稳定

      const responseTime = Date.now() - startTime;
      responseTimes.push(responseTime);

      console.log(`消息响应时间: ${responseTime}ms`);
    }

    const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
    const maxResponseTime = Math.max(...responseTimes);
    const minResponseTime = Math.min(...responseTimes);

    recordMetric('连续消息', '平均响应时间', avgResponseTime);
    recordMetric('连续消息', '最大响应时间', maxResponseTime);
    recordMetric('连续消息', '最小响应时间', minResponseTime);

    console.log('响应时间统计:', { avgResponseTime, maxResponseTime, minResponseTime });

    // 性能断言
    expect(avgResponseTime).toBeLessThan(20000); // 平均响应时间应小于20秒

    await appPage.screenshot('continuous_messages_performance');
  });

  /**
   * 测试场景 5: 页面内存使用监控
   * E2E-PERF-005
   */
  test('应监控内存使用情况', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
    await appPage.waitForAppLoad();

    // 获取初始内存使用
    const initialMetrics = await page.evaluate(() => {
      return {
        jsHeapSizeLimit: (performance as any).memory?.jsHeapSizeLimit || 0,
        totalJSHeapSize: (performance as any).memory?.totalJSHeapSize || 0,
        usedJSHeapSize: (performance as any).memory?.usedJSHeapSize || 0
      };
    });

    console.log('初始内存指标:', initialMetrics);

    // 发送多条消息
    await appPage.startNewChat();

    const chatInput = page.locator('[data-testid="chat-input"]');

    for (let i = 0; i < 5; i++) {
      await chatInput.fill(`性能测试消息 ${i + 1}`);
      await page.locator('[data-testid="send-button"]').click();
      await page.waitForTimeout(3000);
    }

    // 获取最终内存使用
    const finalMetrics = await page.evaluate(() => {
      return {
        jsHeapSizeLimit: (performance as any).memory?.jsHeapSizeLimit || 0,
        totalJSHeapSize: (performance as any).memory?.totalJSHeapSize || 0,
        usedJSHeapSize: (performance as any).memory?.usedJSHeapSize || 0
      };
    });

    console.log('最终内存指标:', finalMetrics);

    const memoryIncrease = finalMetrics.usedJSHeapSize - initialMetrics.usedJSHeapSize;
    const memoryIncreaseMB = memoryIncrease / (1024 * 1024);

    recordMetric('内存使用', '内存增量 (MB)', memoryIncreaseMB);
    recordMetric('内存使用', '最终使用 (MB)', finalMetrics.usedJSHeapSize / (1024 * 1024));

    console.log(`内存增量: ${memoryIncreaseMB.toFixed(2)} MB`);

    // 内存增长应在合理范围内（5条消息不应超过50MB）
    expect(memoryIncreaseMB).toBeLessThan(50);

    await appPage.screenshot('memory_usage');
  });

  /**
   * 测试场景 6: 切换会话性能
   * E2E-PERF-006
   */
  test('会话切换应快速响应', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
    await appPage.waitForAppLoad();

    // 创建多个会话
    for (let i = 0; i < 3; i++) {
      await appPage.startNewChat();
      await page.locator('[data-testid="chat-input"]').fill(`会话 ${i + 1} 的消息`);
      await page.locator('[data-testid="send-button"]').click();
      await page.waitForTimeout(2000);
    }

    // 测量切换时间
    const switchTimes: number[] = [];

    const sessionButtons = page.locator('aside button').filter({ hasText: /会话/ });
    const count = await sessionButtons.count();

    if (count >= 2) {
      for (let i = 0; i < Math.min(3, count); i++) {
        const startTime = Date.now();
        await sessionButtons.nth(i).click();
        await page.waitForTimeout(500);
        const switchTime = Date.now() - startTime;
        switchTimes.push(switchTime);
        console.log(`切换会话 ${i + 1} 耗时: ${switchTime}ms`);
      }

      const avgSwitchTime = switchTimes.reduce((a, b) => a + b, 0) / switchTimes.length;

      recordMetric('会话切换', '平均切换时间', avgSwitchTime);

      // 会话切换应在1秒内完成
      expect(avgSwitchTime).toBeLessThan(1000);

      await appPage.screenshot('session_switch_performance');
    } else {
      test.skip(true, '需要至少2个会话');
    }
  });

  /**
   * 测试场景 7: 页面加载性能
   * E2E-PERF-007
   */
  test('页面加载性能测试', async ({ page }) => {
    // 监听所有网络请求
    const requests: { url: string; duration: number; size: number }[] = [];

    page.on('requestfinished', request => {
      const timing = request.timing();
      if (timing) {
        requests.push({
          url: request.url(),
          duration: timing.responseEnd || 0,
          size: request.transferSize() || 0
        });
      }
    });

    const startTime = Date.now();

    const loginPage = new LoginPage(page);
    await loginPage.goto();

    const gotoTime = Date.now();

    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);

    const loginTime = Date.now();

    const appPage = new AppPage(page);
    await appPage.waitForAppLoad();

    const loadTime = Date.now();

    // 等待所有资源加载
    await page.waitForLoadState('networkidle');
    const networkIdleTime = Date.now();

    recordMetric('页面加载', '导航到登录页', gotoTime - startTime);
    recordMetric('页面加载', '登录请求', loginTime - gotoTime);
    recordMetric('页面加载', '应用加载', loadTime - loginTime);
    recordMetric('页面加载', '网络完全空闲', networkIdleTime - loadTime);
    recordMetric('页面加载', '总加载时间', networkIdleTime - startTime);

    // 分析网络请求
    const slowRequests = requests.filter(r => r.duration > 1000);
    const largeRequests = requests.filter(r => r.size > 100000);

    console.log('慢请求 (>1s):', slowRequests.length);
    console.log('大请求 (>100KB):', largeRequests.length);

    if (slowRequests.length > 0) {
      console.log('慢请求详情:', slowRequests.map(r => ({ url: r.url, duration: r.duration })));
    }

    // 性能断言
    expect(networkIdleTime - startTime).toBeLessThan(15000); // 总加载时间应在15秒内

    await appPage.screenshot('page_load_performance');
  });

  /**
   * 测试场景 8: 长时间运行稳定性
   * E2E-PERF-008
   */
  test('长时间运行应保持稳定', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
    await appPage.waitForAppLoad();

    const chatInput = page.locator('[data-testid="chat-input"]');
    const responseTimes: number[] = [];
    const memorySnapshots: number[] = [];

    // 运行10轮对话
    for (let i = 0; i < 10; i++) {
      await appPage.startNewChat();

      await chatInput.fill(`稳定性测试第 ${i + 1} 轮，请简单回复"收到"`);

      const startTime = Date.now();
      await page.locator('[data-testid="send-button"]').click();

      await expect(page.locator('[data-message-role="assistant"]')).toBeVisible({ timeout: 30000 });
      await page.waitForTimeout(1000);

      const responseTime = Date.now() - startTime;
      responseTimes.push(responseTime);

      // 记录内存使用
      const memory = await page.evaluate(() =>
        (performance as any).memory?.usedJSHeapSize || 0
      );
      memorySnapshots.push(memory);

      console.log(`第 ${i + 1} 轮: 响应时间 ${responseTime}ms, 内存 ${(memory / 1024 / 1024).toFixed(2)}MB`);
    }

    // 分析趋势
    const firstHalfAvg = responseTimes.slice(0, 5).reduce((a, b) => a + b, 0) / 5;
    const secondHalfAvg = responseTimes.slice(5).reduce((a, b) => a + b, 0) / 5;

    const firstHalfMemory = memorySnapshots.slice(0, 5).reduce((a, b) => a + b, 0) / 5;
    const secondHalfMemory = memorySnapshots.slice(5).reduce((a, b) => a + b, 0) / 5;

    const performanceDegradation = ((secondHalfAvg - firstHalfAvg) / firstHalfAvg) * 100;
    const memoryGrowth = ((secondHalfMemory - firstHalfMemory) / firstHalfMemory) * 100;

    recordMetric('长时间运行', '前半段平均响应', firstHalfAvg);
    recordMetric('长时间运行', '后半段平均响应', secondHalfAvg);
    recordMetric('长时间运行', '性能衰减率 (%)', performanceDegradation);
    recordMetric('长时间运行', '内存增长率 (%)', memoryGrowth);

    console.log('性能衰减率:', performanceDegradation.toFixed(2) + '%');
    console.log('内存增长率:', memoryGrowth.toFixed(2) + '%');

    // 性能衰减应小于50%
    expect(performanceDegradation).toBeLessThan(50);

    await appPage.screenshot('long_running_stability');
  });
});

/**
 * 性能报告生成
 */
test.afterAll(async () => {
  console.log('\n========================================');
  console.log('性能测试报告');
  console.log('========================================\n');

  // 按测试分组
  const groupedMetrics: Record<string, Record<string, number[]>> = {};

  for (const metric of performanceMetrics) {
    if (!groupedMetrics[metric.testName]) {
      groupedMetrics[metric.testName] = {};
    }
    if (!groupedMetrics[metric.testName][metric.metricName]) {
      groupedMetrics[metric.testName][metric.metricName] = [];
    }
    groupedMetrics[metric.testName][metric.metricName].push(metric.value);
  }

  // 输出报告
  for (const [testName, metrics] of Object.entries(groupedMetrics)) {
    console.log(`\n【${testName}】`);
    for (const [metricName, values] of Object.entries(metrics)) {
      const avg = values.reduce((a, b) => a + b, 0) / values.length;
      const min = Math.min(...values);
      const max = Math.max(...values);
      console.log(`  ${metricName}:`);
      console.log(`    平均: ${avg.toFixed(2)}ms`);
      console.log(`    范围: ${min.toFixed(2)}ms - ${max.toFixed(2)}ms`);
    }
  }

  console.log('\n========================================\n');
});
