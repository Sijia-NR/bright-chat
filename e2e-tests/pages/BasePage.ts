import { Page, Locator } from '@playwright/test';

/**
 * 基础页面类
 * 提供通用方法和工具函数
 */
export class BasePage {
  readonly page: Page;
  readonly screenshotDir: string;

  constructor(page: Page) {
    this.page = page;
    this.screenshotDir = './artifacts';
  }

  /**
   * 导航到指定 URL
   */
  async goto(path = ''): Promise<void> {
    await this.page.goto(path);
  }

  /**
   * 等待网络空闲
   */
  async waitForNetworkIdle(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 截图保存
   */
  async screenshot(name: string): Promise<string> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${this.screenshotDir}/${name}_${timestamp}.png`;
    await this.page.screenshot({ path: filename, fullPage: true });
    return filename;
  }

  /**
   * 安全点击 - 等待元素可见后点击
   */
  async safeClick(locator: Locator, description?: string): Promise<boolean> {
    try {
      await locator.waitFor({ state: 'visible', timeout: 5000 });
      await locator.click();
      return true;
    } catch (error) {
      console.error(`Click failed for ${description || locator}:`, error);
      return false;
    }
  }

  /**
   * 安全填写 - 等待元素可见后填写
   */
  async safeFill(locator: Locator, value: string, description?: string): Promise<boolean> {
    try {
      await locator.waitFor({ state: 'visible', timeout: 5000 });
      await locator.fill(value);
      return true;
    } catch (error) {
      console.error(`Fill failed for ${description || locator}:`, error);
      return false;
    }
  }

  /**
   * 等待元素出现
   */
  async waitForElement(selector: string, timeout = 5000): Promise<Locator | null> {
    try {
      const locator = this.page.locator(selector).first();
      await locator.waitFor({ state: 'visible', timeout });
      return locator;
    } catch {
      return null;
    }
  }

  /**
   * 检查元素是否存在
   */
  async elementExists(selector: string, timeout = 2000): Promise<boolean> {
    try {
      await this.page.locator(selector).first().waitFor({ state: 'visible', timeout });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 获取元素文本内容
   */
  async getText(selector: string): Promise<string> {
    const locator = this.page.locator(selector).first();
    return await locator.textContent() || '';
  }

  /**
   * 等待导航完成
   */
  async waitForNavigation(): Promise<void> {
    await this.page.waitForLoadState('domcontentloaded');
  }

  /**
   * 刷新页面
   */
  async reload(): Promise<void> {
    await this.page.reload();
    await this.waitForNetworkIdle();
  }

  /**
   * 执行 JavaScript
   */
  async evaluate<T>(fn: () => T): Promise<T> {
    return await this.page.evaluate(fn);
  }

  /**
   * 获取控制台日志
   */
  getConsoleLogs(): string[] {
    const logs: string[] = [];
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        logs.push(msg.text());
      }
    });
    return logs;
  }
}
