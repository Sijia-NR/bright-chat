import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

test.describe('Bright-Chat 聊天功能测试', () => {
  test('直接模型对话测试', async ({ page }) => {
    // 登录
    await page.goto('http://localhost:3000');
    await page.fill('[data-testid="username-input"]', 'admin');
    await page.fill('[data-testid="password-input"]', 'pwd123');
    await page.click('[data-testid="login-button"]');
    
    // 等待加载
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    
    // 监听 API
    const apiPromise = page.waitForResponse(resp =>
      resp.url().includes('/lmp-cloud-ias-server') && resp.status() === 200
    );
    
    // 输入消息
    const chatInput = page.locator('[data-testid="chat-input"]');
    await expect(chatInput).toBeVisible();
    await chatInput.fill('1+1=?');
    await chatInput.press('Enter');
    
    // 等待 API 响应
    await apiPromise;
    await page.waitForTimeout(3000);
    
    // 验证有消息
    const messages = page.locator('[class*="message"]');
    await expect(messages.first()).toBeVisible();
    
    console.log('✅ 直接模型对话测试通过');
  });
  
  test('多轮对话测试', async ({ page }) => {
    // 登录
    await page.goto('http://localhost:3000');
    await page.fill('[data-testid="username-input"]', 'admin');
    await page.fill('[data-testid="password-input"]', 'pwd123');
    await page.click('[data-testid="login-button"]');
    
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    
    const chatInput = page.locator('[data-testid="chat-input"]');
    
    // 第一轮
    await chatInput.fill('我叫小明');
    await chatInput.press('Enter');
    await page.waitForTimeout(3000);
    
    // 第二轮
    await chatInput.fill('我叫什么名字？');
    await chatInput.press('Enter');
    await page.waitForTimeout(3000);
    
    // 验证回复
    const messages = page.locator('[class*="message"]');
    await expect(messages.last()).toBeVisible();
    
    console.log('✅ 多轮对话测试通过');
  });
});
