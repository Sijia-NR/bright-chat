import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * 应用主页面（更新版 - 使用 data-testid）
 * 包含聊天界面和侧边栏
 */
export class AppPage extends BasePage {
  // 导航相关
  readonly newChatButton: Locator;
  readonly sidebar: Locator;
  readonly adminButton: Locator;
  readonly logoutButton: Locator;
  readonly favoritesButton: Locator;

  // 聊天相关
  readonly aiWorkbenchTitle: Locator;
  readonly chatInput: Locator;
  readonly sendButton: Locator;
  readonly messagesContainer: Locator;
  readonly modelSelectorButton: Locator;
  readonly selectedModelName: Locator;

  // 用户信息
  readonly currentUsername: Locator;
  readonly userInfoSection: Locator;

  // 错误处理
  readonly errorMessage: Locator;

  constructor(page: Page) {
    super(page);

    // 导航按钮 - 使用 data-testid
    this.newChatButton = page.locator('[data-testid="new-chat-button"]');
    this.sidebar = page.locator('aside');
    this.adminButton = page.locator('[data-testid="admin-panel-button"]');
    this.logoutButton = page.locator('[data-testid="logout-button"]');
    this.favoritesButton = page.locator('button').filter({ hasText: /收藏/ });

    // 聊天界面 - 使用 data-testid
    this.aiWorkbenchTitle = page.locator('text=AI工作台');
    this.chatInput = page.locator('[data-testid="chat-input"]');
    this.sendButton = page.locator('[data-testid="send-button"]');
    this.messagesContainer = page.locator('[data-testid="messages-container"]');
    this.modelSelectorButton = page.locator('[data-testid="model-selector-button"]');
    this.selectedModelName = page.locator('[data-testid="selected-model-name"]');

    // 用户信息
    this.currentUsername = page.locator('[data-testid="current-username"]');
    this.userInfoSection = page.locator('[data-testid="user-info-section"]');

    // 错误处理
    this.errorMessage = page.locator('[data-testid="error-message"]');
  }

  /**
   * 等待应用加载完成
   */
  async waitForAppLoad(): Promise<boolean> {
    try {
      await this.page.waitForLoadState('domcontentloaded', { timeout: 10000 });
      await this.page.waitForTimeout(1000); // 等待 React 渲染

      // 检查关键元素
      const hasInput = await this.elementExists('[data-testid="chat-input"]', 5000);
      return hasInput;
    } catch {
      return false;
    }
  }

  /**
   * 点击新对话按钮
   */
  async startNewChat(): Promise<void> {
    await this.safeClick(this.newChatButton, '新对话按钮');
    await this.page.waitForTimeout(1000);
  }

  /**
   * 发送消息
   */
  async sendMessage(message: string): Promise<boolean> {
    try {
      await this.chatInput.waitFor({ state: 'visible', timeout: 5000 });
      await this.chatInput.fill(message);

      // 等待发送按钮启用
      await this.page.waitForTimeout(200);
      await this.sendButton.click();

      // 等待用户消息显示
      await expect(this.page.locator(`[data-message-role="user"]`).filter({ hasText: message }))
        .toBeVisible({ timeout: 5000 });

      await this.screenshot('message_sent');
      return true;
    } catch (error) {
      console.error('Send message error:', error);
      await this.screenshot('send_message_error');
      return false;
    }
  }

  /**
   * 获取消息数量
   */
  async getMessageCount(): Promise<number> {
    return await this.page.locator('[data-testid^="message-"]').count();
  }

  /**
   * 获取用户消息数量
   */
  async getUserMessageCount(): Promise<number> {
    return await this.page.locator('[data-message-role="user"]').count();
  }

  /**
   * 获取助手消息数量
   */
  async getAssistantMessageCount(): Promise<number> {
    return await this.page.locator('[data-message-role="assistant"]').count();
  }

  /**
   * 检查是否有 AI 回复
   */
  async hasAIResponse(timeout = 30000): Promise<boolean> {
    try {
      const assistantMessages = this.page.locator('[data-message-role="assistant"]');
      await assistantMessages.first().waitFor({ state: 'visible', timeout });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 等待 AI 响应并返回内容
   */
  async waitForAIResponse(timeout = 30000): Promise<string | null> {
    try {
      const assistantMessage = this.page.locator('[data-message-role="assistant"]').last();
      await assistantMessage.waitFor({ state: 'visible', timeout });
      await this.page.waitForTimeout(2000); // 等待流式内容稳定
      return await assistantMessage.textContent();
    } catch {
      return null;
    }
  }

  /**
   * 点击管理面板按钮
   */
  async openAdminPanel(): Promise<boolean> {
    const clicked = await this.safeClick(this.adminButton, '管理面板按钮');
    if (clicked) {
      await this.page.waitForTimeout(1000);
    }
    return clicked;
  }

  /**
   * 执行登出
   */
  async logout(): Promise<boolean> {
    const clicked = await this.safeClick(this.logoutButton, '退出登录按钮');
    if (clicked) {
      await this.page.waitForTimeout(2000);
      await this.screenshot('after_logout');
    }
    return clicked;
  }

  /**
   * 获取当前用户名
   */
  async getCurrentUsername(): Promise<string | null> {
    try {
      await this.currentUsername.waitFor({ state: 'visible', timeout: 5000 });
      return await this.currentUsername.textContent();
    } catch {
      return null;
    }
  }

  /**
   * 检查侧边栏是否可见
   */
  async isSidebarVisible(): Promise<boolean> {
    return await this.sidebar.isVisible();
  }

  /**
   * 选择模型
   */
  async selectModel(modelId: string): Promise<boolean> {
    try {
      // 悬停在模型选择器上
      await this.modelSelectorButton.hover();
      await this.page.waitForTimeout(500);

      // 点击特定模型选项
      const modelOption = this.page.locator(`[data-testid="model-option-${modelId}"]`);
      await modelOption.click();

      await this.page.waitForTimeout(500);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 获取当前选中的模型名称
   */
  async getSelectedModelName(): Promise<string> {
    try {
      return await this.selectedModelName.textContent() || '';
    } catch {
      return '';
    }
  }

  /**
   * 获取可用模型列表
   */
  async getAvailableModels(): Promise<string[]> {
    const models: string[] = [];

    // 悬停以展开下拉菜单
    await this.modelSelectorButton.hover();
    await this.page.waitForTimeout(500);

    const options = await this.page.locator('[data-testid^="model-option-"]').all();
    for (const option of options) {
      const text = await option.textContent();
      if (text) models.push(text);
    }

    return models;
  }

  /**
   * 检查是否有错误提示
   */
  async hasError(): Promise<boolean> {
    const count = await this.errorMessage.count();
    return count > 0;
  }

  /**
   * 获取错误信息
   */
  async getErrorText(): Promise<string> {
    if (await this.errorMessage.count() > 0) {
      return await this.errorMessage.textContent() || '';
    }
    return '';
  }

  /**
   * 等待错误消息消失
   */
  async waitForErrorToDisappear(timeout = 5000): Promise<boolean> {
    return await this.waitForElementToDisappear('[data-testid="error-message"]', timeout);
  }

  /**
   * 检查是否正在输入（isTyping 状态）
   */
  async isTyping(): Promise<boolean> {
    // 检查是否有打字动画
    const typingIndicator = this.page.locator('.animate-pulse').filter({ hasText: /^B$/ });
    return await typingIndicator.count() > 0;
  }

  /**
   * 等待输入完成
   */
  async waitForTypingComplete(timeout = 30000): Promise<boolean> {
    try {
      const typingIndicator = this.page.locator('.animate-pulse').filter({ hasText: /^B$/ });
      await typingIndicator.waitFor({ state: 'hidden', timeout });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 清空输入框
   */
  async clearInput(): Promise<void> {
    await this.chatInput.fill('');
  }

  /**
   * 获取输入框当前内容
   */
  async getInputValue(): Promise<string> {
    return await this.chatInput.inputValue();
  }

  /**
   * 按 Enter 键发送消息
   */
  async sendWithEnter(message: string): Promise<void> {
    await this.chatInput.fill(message);
    await this.chatInput.press('Enter');
  }

  /**
   * 按 Shift+Enter 换行
   */
  async typeWithShiftEnter(message: string): Promise<void> {
    await this.chatInput.fill(message);
    await this.chatInput.press('Shift+Enter');
  }
}
