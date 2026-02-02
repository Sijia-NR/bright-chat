import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * 登录页面
 * 用户认证相关测试
 */
export class LoginPage extends BasePage {
  // 页面元素选择器
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    super(page);
    this.usernameInput = page.locator('[data-testid="username-input"]');
    this.passwordInput = page.locator('[data-testid="password-input"]');
    this.loginButton = page.locator('[data-testid="login-button"]');
    this.errorMessage = page.locator('.error, [class*="error"], [role="alert"]');
  }

  /**
   * 导航到登录页（首页）
   */
  async goto(): Promise<void> {
    await this.page.goto('http://localhost:3000');
    await this.waitForNetworkIdle();
  }

  /**
   * 执行登录操作
   */
  async login(username: string, password: string): Promise<boolean> {
    try {
      // 检查是否已在登录页面
      await this.page.waitForLoadState('domcontentloaded');

      // 输入用户名
      await this.usernameInput.waitFor({ state: 'visible', timeout: 5000 });
      await this.usernameInput.fill(username);

      // 输入密码
      await this.passwordInput.fill(password);

      // 点击登录按钮
      await this.loginButton.click();

      // 等待登录完成
      await this.page.waitForTimeout(2000);

      // 检查是否登录成功（查找登录后的页面元素）
      const isLoggedIn = await this.isLoginSuccessful();

      if (isLoggedIn) {
        await this.screenshot('login_success');
      } else {
        await this.screenshot('login_failed');
      }

      return isLoggedIn;
    } catch (error) {
      console.error('Login error:', error);
      await this.screenshot('login_error');
      return false;
    }
  }

  /**
   * 检查登录是否成功
   */
  async isLoginSuccessful(): Promise<boolean> {
    try {
      // 检查是否有登录后的元素
      const hasAIWorkbench = await this.elementExists('text=AI工作台', 3000);
      const hasAdminPanel = await this.elementExists('text=管理面板', 3000);
      const hasSidebar = await this.elementExists('aside', 3000);

      return hasAIWorkbench || hasAdminPanel || hasSidebar;
    } catch {
      return false;
    }
  }

  /**
   * 检查是否已登录
   */
  async isLoggedIn(): Promise<boolean> {
    return await this.isLoginSuccessful();
  }

  /**
   * 获取错误消息
   */
  async getErrorMessage(): Promise<string | null> {
    if (await this.errorMessage.count() > 0) {
      return await this.errorMessage.textContent();
    }
    return null;
  }

  /**
   * 测试错误登录
   */
  async testInvalidCredentials(wrongUsername: string, wrongPassword: string): Promise<{
    attempted: boolean;
    errorShown: boolean;
    errorText: string | null;
  }> {
    const initialState = await this.page.content();

    await this.usernameInput.fill(wrongUsername);
    await this.passwordInput.fill(wrongPassword);
    await this.loginButton.click();
    await this.page.waitForTimeout(2000);

    const errorText = await this.getErrorMessage();
    const errorShown = errorText !== null;
    const contentChanged = await this.page.content() !== initialState;

    await this.screenshot('invalid_login_attempt');

    return {
      attempted: true,
      errorShown,
      errorText
    };
  }

  /**
   * 检查登录表单是否可见
   */
  async isLoginFormVisible(): Promise<boolean> {
    try {
      await this.usernameInput.waitFor({ state: 'visible', timeout: 3000 });
      return true;
    } catch {
      return false;
    }
  }
}
