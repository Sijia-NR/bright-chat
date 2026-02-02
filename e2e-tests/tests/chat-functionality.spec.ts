import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { AppPage } from '../pages/AppPage';

/**
 * 聊天功能测试套件
 *
 * 测试场景：
 * 1. 发送消息
 * 2. 查看消息历史
 * 3. 创建新对话
 * 4. 选择模型
 * 5. 消息流式响应
 */

test.describe('聊天功能测试', () => {
  const ADMIN_CREDENTIALS = { username: 'admin', password: 'pwd123' };

  let loginPage: LoginPage;
  let appPage: AppPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    appPage = new AppPage(page);

    // 登录
    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
  });

  /**
   * 测试场景 1: 聊天界面加载
   * E2E-CHAT-001
   */
  test('聊天界面应正常加载', async ({ page }) => {
    const isAppLoaded = await appPage.waitForAppLoad();
    expect(isAppLoaded, '聊天界面应加载完成').toBe(true);

    // 验证关键元素
    const hasTitle = await appPage.elementExists('text=AI工作台', 3000);
    const hasInput = await appPage.elementExists('textarea', 3000);
    const hasSidebar = await appPage.elementExists('aside', 3000);

    expect(hasTitle, '应显示 AI 工作台标题').toBe(true);
    expect(hasInput, '应显示输入框').toBe(true);
    expect(hasSidebar, '应显示侧边栏').toBe(true);

    await appPage.screenshot('chat_interface_loaded');
  });

  /**
   * 测试场景 2: 新对话功能
   * E2E-CHAT-002
   */
  test('应能创建新对话', async ({ page }) => {
    // 点击新对话按钮
    await appPage.startNewChat();

    // 验证消息区域被清空
    await page.waitForTimeout(1000);
    const messageCount = await appPage.getMessageCount();

    // 新对话应该没有消息
    expect(messageCount).toBe(0);

    await appPage.screenshot('new_chat_created');
  });

  /**
   * 测试场景 3: 发送消息
   * E2E-CHAT-003
   */
  test('应能发送消息', async ({ page }) => {
    // 先创建新对话
    await appPage.startNewChat();

    // 发送测试消息
    const messageSent = await appPage.sendMessage('你好，这是一条测试消息');

    expect(messageSent, '消息应发送成功').toBe(true);

    // 验证消息出现在界面上
    await page.waitForTimeout(2000);
    const messageCount = await appPage.getMessageCount();
    expect(messageCount, '应有用户消息显示').toBeGreaterThan(0);

    await appPage.screenshot('message_sent');
  });

  /**
   * 测试场景 4: 输入框功能
   * E2E-CHAT-004
   */
  test('输入框应能正常输入和清空', async ({ page }) => {
    const textarea = page.locator('textarea').first();

    // 等待输入框可见
    await textarea.waitFor({ state: 'visible' });

    // 输入文本
    await textarea.fill('测试文本');
    let value = await textarea.inputValue();
    expect(value).toBe('测试文本');

    // 清空
    await textarea.clear();
    value = await textarea.inputValue();
    expect(value).toBe('');

    await appPage.screenshot('input_functionality');
  });

  /**
   * 测试场景 5: 侧边栏会话列表
   * E2E-CHAT-005
   */
  test('侧边栏应显示会话列表', async ({ page }) => {
    const sidebar = page.locator('aside');

    // 检查侧边栏
    expect(await sidebar.isVisible()).toBe(true);

    // 检查是否有会话轨迹区域
    const hasSessionSection = await appPage.elementExists('aside:has-text("会话")', 2000);

    if (hasSessionSection) {
      await appPage.screenshot('session_list_visible');
    }
  });

  /**
   * 测试场景 6: 用户信息显示
   * E2E-CHAT-006
   */
  test('应显示当前登录用户信息', async ({ page }) => {
    const username = await appPage.getCurrentUsername();

    expect(username, '应显示用户名').not.toBeNull();
    expect(username?.toLowerCase()).toContain('admin');

    await appPage.screenshot('user_info_displayed');
  });

  /**
   * 测试场景 7: 模型选择器
   * E2E-CHAT-007
   */
  test('应能查看和选择模型', async ({ page }) => {
    // 检查是否有模型选择器
    const hasModelSelector = await appPage.elementExists('select, [role="combobox"]', 3000);

    if (hasModelSelector) {
      const models = await appPage.getAvailableModels();
      console.log(`可用模型: ${models.join(', ')}`);

      // 应该至少有一个模型
      expect(models.length).toBeGreaterThan(0);
    } else {
      // 没有模型选择器，可能是简化版界面
      console.log('当前界面没有模型选择器');
    }

    await appPage.screenshot('model_selector');
  });

  /**
   * 测试场景 8: 多行输入支持
   * E2E-CHAT-008
   */
  test('输入框应支持多行输入', async ({ page }) => {
    const textarea = page.locator('textarea').first();
    await textarea.waitFor({ state: 'visible' });

    const multiLineText = '第一行\n第二行\n第三行';
    await textarea.fill(multiLineText);

    const value = await textarea.inputValue();
    expect(value).toContain('第一行');
    expect(value).toContain('第二行');

    await appPage.screenshot('multiline_input');
  });

  /**
   * 测试场景 9: 消息显示样式
   * E2E-CHAT-009
   */
  test('消息应正确显示样式', async ({ page }) => {
    await appPage.startNewChat();
    await appPage.sendMessage('样式测试消息');
    await page.waitForTimeout(2000);

    // 查找用户消息
    const userMessages = page.locator('div').filter({ hasText: '样式测试消息' });
    const count = await userMessages.count();

    expect(count, '消息应显示').toBeGreaterThan(0);

    await appPage.screenshot('message_style');
  });

  /**
   * 测试场景 10: 空状态显示
   * E2E-CHAT-010
   */
  test('新对话应显示欢迎界面', async ({ page }) => {
    await appPage.startNewChat();

    // 检查是否有欢迎界面
    const hasWelcome = await appPage.elementExists('text=AI工作台', 2000);
    expect(hasWelcome, '应显示欢迎界面').toBe(true);

    await appPage.screenshot('welcome_state');
  });

  /**
   * 测试场景 11: 键盘快捷键
   * E2E-CHAT-011
   */
  test('应支持 Enter 键发送消息', async ({ page }) => {
    await appPage.startNewChat();

    const textarea = page.locator('textarea').first();
    await textarea.waitFor({ state: 'visible' });

    // 输入消息
    await textarea.fill('快捷键测试');

    // 按 Enter 发送
    await page.keyboard.press('Enter');
    await page.waitForTimeout(2000);

    // 验证消息发送
    const hasMessage = await appPage.elementExists('text=快捷键测试', 3000);
    expect(hasMessage, '消息应通过 Enter 键发送').toBe(true);
  });

  /**
   * 测试场景 12: 侧边栏折叠/展开
   * E2E-CHAT-012
   */
  test('侧边栏应能折叠和展开', async ({ page }) => {
    const sidebar = page.locator('aside');

    // 检查初始状态
    const initialWidth = await sidebar.evaluate(el => el.getBoundingClientRect().width);

    // 查找折叠按钮（如果存在）
    const collapseButton = page.locator('button').filter({ hasText: /折叠|收起|菜单/ });

    if (await collapseButton.count() > 0) {
      await collapseButton.first().click();
      await page.waitForTimeout(500);

      const collapsedWidth = await sidebar.evaluate(el => el.getBoundingClientRect().width);

      // 宽度应该变化
      expect(collapsedWidth).not.toBe(initialWidth);

      await appPage.screenshot('sidebar_collapsed');
    } else {
      console.log('未找到侧边栏折叠按钮');
    }
  });
});
