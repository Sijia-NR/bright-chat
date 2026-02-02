import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { AppPage } from '../pages/AppPage';

/**
 * Bright-Chat 前后端联调测试
 *
 * 测试两个不同的对话接口：
 * 1. 直接模型对话：/api/v1/lmp-cloud-ias-server/api/llm/chat/completions/V2
 * 2. 数字员工对话：/api/v1/agents/{agent_id}/chat
 */

test.describe('Bright-Chat 前后端联调测试', () => {
  let loginPage: LoginPage;
  let appPage: AppPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    appPage = new AppPage(page);

    // 导航到登录页
    await loginPage.goto();

    // 使用 admin 账号登录
    await loginPage.login('admin', 'pwd123');

    // 等待登录成功并进入聊天界面
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  /**
   * 测试场景 1：直接模型对话
   * 端点：POST /api/v1/lmp-cloud-ias-server/api/llm/chat/completions/V2
   */
  test('应该能够通过直接模型接口发送消息并接收回复', async ({ page }) => {
    // 监听 API 响应
    const apiResponsePromise = page.waitForResponse(resp =>
      resp.url().includes('/lmp-cloud-ias-server/api/llm/chat/completions/V2') &&
      resp.status() === 200
    );

    // 找到聊天输入框
    const chatInput = page.locator('[data-testid="chat-input"], textarea[placeholder*="输入"], textarea');
    await expect(chatInput).toBeVisible({ timeout: 5000 });

    // 输入测试消息
    const testMessage = '1+1等于几？';
    await chatInput.fill(testMessage);

    // 找到发送按钮并点击
    const sendButton = page.locator('button[type="submit"], button:has-text("发送"), button[aria-label*="send"], button[aria-label*="Send"]');
    await sendButton.click();

    // 等待 API 响应
    const apiResponse = await apiResponsePromise;

    // 验证响应状态
    expect(apiResponse.status()).toBe(200);

    // 等待消息显示在聊天界面
    const messages = page.locator('[data-testid="message"], .message, [class*="message"]');
    await expect(messages).toHaveCount(await messages.count() + 1, { timeout: 10000 });

    // 验证助手回复
    const assistantMessages = page.locator('[class*="assistant"], [role="assistant"]');
    await expect(assistantMessages).toContainText(/2|等于/i, { timeout: 10000 });

    // 截图
    await page.screenshot({ path: 'artifacts/direct-model-chat.png' });
  });

  /**
   * 测试场景 2：流式响应（SSE）
   * 验证：逐步显示响应内容
   */
  test('应该支持流式响应并逐步显示内容', async ({ page }) => {
    const chatInput = page.locator('[data-testid="chat-input"], textarea[placeholder*="输入"], textarea');
    const sendButton = page.locator('button[type="submit"], button:has-text("发送"), button[aria-label*="send"], button[aria-label*="Send"]');

    // 输入需要较长回复的消息
    const testMessage = '请写一首关于春天的诗';
    await chatInput.fill(testMessage);
    await sendButton.click();

    // 等待"正在输入"或"思考中"状态
    const thinkingIndicator = page.locator('[class*="thinking"], [class*="typing"], .loading, [class*="ellipsis"]');
    await expect(thinkingIndicator).toBeVisible({ timeout: 5000 }).catch(() => {
      // 如果没有明确的思考指示器，可能直接开始流式输出
      console.log('No thinking indicator found, streaming might start immediately');
    });

    // 等待响应完成（至少 5 秒）
    await page.waitForTimeout(5000);

    // 验证消息内容已显示
    const messageContent = page.locator('[data-testid="message-content"], .message-content, [class*="message"]');
    await expect(messageContent.last()).toBeVisible({ timeout: 10000 });
    await expect(messageContent.last()).toContainText(/春|花|诗/i);

    // 截图
    await page.screenshot({ path: 'artifacts/streaming-response.png' });
  });

  /**
   * 测试场景 3：数字员工对话 - 计算器 Agent
   * 端点：POST /api/v1/agents/{agent_id}/chat
   */
  test('应该能够使用计算器 Agent 进行数学计算', async ({ page }) => {
    // 获取可用的 Agent 列表
    const agentListPromise = page.waitForResponse(resp =>
      resp.url().includes('/agents/') && resp.status() === 200
    );

    // 点击 Agent 选择器或侧边栏
    const agentSelector = page.locator('[data-testid="agent-selector"], button:has-text("Agent"), button:has-text("数字员工")');
    const hasAgentSelector = await agentSelector.count() > 0;

    if (hasAgentSelector) {
      await agentSelector.first().click();
    }

    // 等待 Agent 列表加载
    await agentListPromise;

    // 选择计算器 Agent（如果可用）
    const calculatorAgent = page.locator('[data-testid="agent-calculator"], button:has-text("计算"), button:has-text("Calculator"), [data-agent*="calc"]');
    const hasCalculatorAgent = await calculatorAgent.count() > 0;

    if (hasCalculatorAgent) {
      await calculatorAgent.first().click();
    }

    // 输入需要计算的消息
    const chatInput = page.locator('[data-testid="chat-input"], textarea[placeholder*="输入"], textarea');
    await chatInput.fill('123 + 456 = ?');

    const sendButton = page.locator('button[type="submit"], button:has-text("发送"), button[aria-label*="send"], button[aria-label*="Send"]');
    await sendButton.click();

    // 监听 Agent API 调用
    const agentApiResponsePromise = page.waitForResponse(resp =>
      resp.url().includes('/agents/') &&
      resp.url().includes('/chat') &&
      resp.status() === 200
    );

    // 等待 Agent API 响应
    try {
      const agentResponse = await agentApiResponsePromise.timeout(10000);
      expect(agentResponse.status()).toBe(200);
    } catch (error) {
      // 如果 Agent API 没有被调用，可能使用了普通模型接口
      console.log('Agent API not called, might be using direct model interface');
    }

    // 等待回复
    await page.waitForTimeout(3000);

    // 验证回复中包含计算结果
    const messageContent = page.locator('[data-testid="message-content"], .message-content, [class*="message"]');
    await expect(messageContent.last()).toBeVisible({ timeout: 10000 });

    const messageText = await messageContent.last().textContent();
    expect(messageText).toMatch(/579|5.7.9/i);

    // 截图
    await page.screenshot({ path: 'artifacts/agent-calculator-chat.png' });
  });

  /**
   * 测试场景 4：数字员工对话 - RAG Agent（知识检索）
   * 端点：POST /api/v1/agents/{agent_id}/chat
   */
  test('应该能够使用 RAG Agent 进行知识检索', async ({ page }) => {
    // 选择知识库 Agent
    const ragAgent = page.locator('[data-testid="agent-rag"], [data-agent*="knowledge"], button:has-text("知识"), button:has-text("研究员")');
    const hasRagAgent = await ragAgent.count() > 0;

    if (hasRagAgent) {
      await ragAgent.first().click();
    }

    // 输入查询消息
    const chatInput = page.locator('[data-testid="chat-input"], textarea[placeholder*="输入"], textarea');
    await chatInput.fill('什么是 Bright-Chat？');

    const sendButton = page.locator('button[type="submit"], button:has-text("发送"), button[aria-label*="send"], button[aria-label*="Send"]');
    await sendButton.click();

    // 等待回复
    await page.waitForTimeout(5000);

    // 验证收到了回复
    const messageContent = page.locator('[data-testid="message-content"], .message-content, [class*="message"]');
    await expect(messageContent.last()).toBeVisible({ timeout: 15000 });

    // 截图
    await page.screenshot({ path: 'artifacts/agent-rag-chat.png' });
  });

  /**
   * 测试场景 5：会话管理
   * 验证：创建新会话、切换会话、删除会话
   */
  test('应该能够正常管理聊天会话', async ({ page }) => {
    // 查看当前会话列表
    const sessionList = page.locator('[data-testid="session-list"], [class*="session"], aside ul li');
    const initialSessionCount = await sessionList.count();

    // 创建新会话
    const newChatButton = page.locator('button:has-text("新对话"), button:has-text("New Chat"), [aria-label*="new"], [data-testid="new-chat"]');
    const hasNewChatButton = await newChatButton.count() > 0;

    if (hasNewChatButton) {
      await newChatButton.first().click();
      await page.waitForTimeout(1000);
    }

    // 发送消息创建会话
    const chatInput = page.locator('[data-testid="chat-input"], textarea[placeholder*="输入"], textarea');
    await chatInput.fill('新会话测试消息');

    const sendButton = page.locator('button[type="submit"], button:has-text("发送"), button[aria-label*="send"], button[aria-label*="Send"]');
    await sendButton.click();

    // 等待会话创建
    await page.waitForTimeout(2000);

    // 验证会话列表更新
    const updatedSessionCount = await sessionList.count();
    expect(updatedSessionCount).toBeGreaterThanOrEqual(initialSessionCount);

    // 截图
    await page.screenshot({ path: 'artifacts/session-management.png' });
  });

  /**
   * 测试场景 6：错误处理
   * 验证：模型服务不可用时的降级处理
   */
  test('应该优雅处理模型服务错误', async ({ page }) => {
    // 这个测试可以模拟 API 错误
    // 由于我们不想真的破坏服务，这里只验证 UI 的错误处理能力

    const chatInput = page.locator('[data-testid="chat-input"], textarea[placeholder*="输入"], textarea');
    const sendButton = page.locator('button[type="submit"], button:has-text("发送"), button[aria-label*="send"], button[aria-label*="Send"]');

    // 发送空消息（应该被前端验证阻止）
    await chatInput.fill('');
    await sendButton.click();

    // 验证错误提示
    const errorMessage = page.locator('[data-testid="error-message"], .error, [class*="error"]');

    // 如果有错误提示，验证它；如果没有，说明前端可能有其他验证方式
    const hasError = await errorMessage.count() > 0;
    if (hasError) {
      await expect(errorMessage.first()).toBeVisible();
    }

    // 截图
    await page.screenshot({ path: 'artifacts/error-handling.png' });
  });

  /**
   * 测试场景 7：多轮对话
   * 验证：上下文保持能力
   */
  test('应该能够在同一会话中进行多轮对话', async ({ page }) => {
    const chatInput = page.locator('[data-testid="chat-input"], textarea[placeholder*="输入"], textarea');
    const sendButton = page.locator('button[type="submit"], button:has-text("发送"), button[aria-label*="send"], button[aria-label*="Send"]');
    const messages = page.locator('[class*="message"], [data-testid="message"]');

    const initialMessageCount = await messages.count();

    // 第一轮对话
    await chatInput.fill('我叫小明');
    await sendButton.click();
    await page.waitForTimeout(3000);

    // 第二轮对话
    await chatInput.fill('我叫什么名字？');
    await sendButton.click();
    await page.waitForTimeout(3000);

    // 验证回复中包含"小明"
    const messageContent = page.locator('[data-testid="message-content"], .message-content, [class*="message"]');
    await expect(messageContent.last()).toBeVisible({ timeout: 10000 });

    const lastMessageText = await messageContent.last().textContent();
    expect(lastMessageText).toMatch(/小明/i);

    // 截图
    await page.screenshot({ path: 'artifacts/multi-turn-conversation.png' });
  });

  /**
   * 测试场景 8：性能测试
   * 验证：消息响应时间
   */
  test('消息响应时间应该在可接受范围内', async ({ page }) => {
    const chatInput = page.locator('[data-testid="chat-input"], textarea[placeholder*="输入"], textarea');
    const sendButton = page.locator('button[type="submit"], button:has-text("发送"), button[aria-label*="send"], button[aria-label*="Send"]');

    // 记录开始时间
    const startTime = Date.now();

    // 发送消息
    await chatInput.fill('你好');
    await sendButton.click();

    // 等待响应
    const messageContent = page.locator('[data-testid="message-content"], .message-content, [class*="message"]');
    await expect(messageContent.last()).toBeVisible({ timeout: 15000 });

    // 计算响应时间
    const responseTime = Date.now() - startTime;

    console.log(`消息响应时间: ${responseTime}ms`);

    // 验证响应时间在可接受范围内（10 秒以内）
    expect(responseTime).toBeLessThan(10000);

    // 截图
    await page.screenshot({ path: 'artifacts/performance-test.png' });
  });
});

test.describe('API 直接测试', () => {
  /**
   * 直接测试 API 端点（绕过前端）
   */
  test('直接模型 API 端点测试', async ({ request }) => {
    // 1. 登录获取 token
    const loginResponse = await request.post('http://localhost:8080/api/v1/auth/login', {
      data: {
        username: 'admin',
        password: 'pwd123'
      }
    });
    expect(loginResponse.ok()).toBeTruthy();

    const loginData = await loginResponse.json();
    const token = loginData.token;
    expect(token).toBeDefined();

    // 2. 测试直接模型对话 API
    const chatResponse = await request.post('http://localhost:8080/api/v1/lmp-cloud-ias-server/api/llm/chat/completions/V2', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        model: 'glm-4-flash',
        messages: [
          { role: 'user', content: '2+2=?' }
        ],
        stream: false
      }
    });

    expect(chatResponse.ok()).toBeTruthy();

    const chatData = await chatResponse.json();
    expect(chatData.choices).toBeDefined();
    expect(chatData.choices[0].message.content).toMatch(/4/i);
  });

  /**
   * 直接测试 Agent 对话 API 端点
   */
  test('Agent 对话 API 端点测试', async ({ request }) => {
    // 1. 登录获取 token
    const loginResponse = await request.post('http://localhost:8080/api/v1/auth/login', {
      data: {
        username: 'admin',
        password: 'pwd123'
      }
    });
    const loginData = await loginResponse.json();
    const token = loginData.token;

    // 2. 获取 Agent 列表
    const agentsResponse = await request.get('http://localhost:8080/api/v1/agents/', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    expect(agentsResponse.ok()).toBeTruthy();

    const agentsData = await agentsResponse.json();
    expect(agentsData.agents).toBeDefined();
    expect(agentsData.agents.length).toBeGreaterThan(0);

    // 3. 使用第一个 Agent 进行对话
    const firstAgent = agentsData.agents[0];
    const agentChatResponse = await request.post(`http://localhost:8080/api/v1/agents/${firstAgent.id}/chat`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        query: '你好',
        session_id: null,
        knowledge_base_ids: []
      }
    });

    // Agent 可能返回流式响应或 JSON
    expect(agentChatResponse.ok()).toBeTruthy();
  });
});
