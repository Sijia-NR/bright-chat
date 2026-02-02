import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * 管理面板页面
 * 包含用户管理、模型管理、Agent 管理
 */
export class AdminPage extends BasePage {
  // 标题和导航
  readonly adminTitle: Locator;
  readonly backButton: Locator;

  // 选项卡
  readonly usersTab: Locator;
  readonly modelsTab: Locator;
  readonly agentsTab: Locator;

  // 用户管理
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly roleSelect: Locator;
  readonly createUserButton: Locator;
  readonly userList: Locator;

  // Agent 管理
  readonly agentList: Locator;
  readonly createAgentButton: Locator;
  readonly agentFormName: Locator;
  readonly agentFormDisplayName: Locator;
  readonly agentFormType: Locator;

  constructor(page: Page) {
    super(page);

    // 标题和导航
    this.adminTitle = page.locator('text=系统管理中心');
    this.backButton = page.locator('button:has-text("返回对话")');

    // 选项卡
    this.usersTab = page.locator('button:has-text("用户注册与管理")');
    this.modelsTab = page.locator('button:has-text("LLM 模型管理")');
    this.agentsTab = page.locator('button:has-text("Agent 管理"), button:has-text("数字员工")');

    // 用户管理表单
    this.usernameInput = page.locator('input[placeholder*="用户名"], input[placeholder*="田户名"]');
    this.passwordInput = page.locator('input[placeholder*="密码"]');
    this.roleSelect = page.locator('select');
    this.createUserButton = page.locator('button:has-text("确认创建账号"), button:has-text("创建")');
    this.userList = page.locator('text=用户管理列表');

    // Agent 管理
    this.createAgentButton = page.locator('button:has-text("创建 Agent"), button:has-text("创建")');
    this.agentFormName = page.locator('input[placeholder*="研究助手"], input[placeholder*="agent"]');
  }

  /**
   * 检查是否在管理面板
   */
  async isAdminPanelVisible(): Promise<boolean> {
    return await this.elementExists('text=系统管理中心', 3000);
  }

  /**
   * 切换到用户管理标签
   */
  async goToUsersTab(): Promise<boolean> {
    const clicked = await this.safeClick(this.usersTab, '用户管理标签');
    if (clicked) {
      await this.page.waitForTimeout(1000);
    }
    return clicked;
  }

  /**
   * 切换到模型管理标签
   */
  async goToModelsTab(): Promise<boolean> {
    const clicked = await this.safeClick(this.modelsTab, '模型管理标签');
    if (clicked) {
      await this.page.waitForTimeout(1000);
    }
    return clicked;
  }

  /**
   * 切换到 Agent 管理标签
   */
  async goToAgentsTab(): Promise<boolean> {
    const clicked = await this.safeClick(this.agentsTab, 'Agent 管理标签');
    if (clicked) {
      await this.page.waitForTimeout(1000);
    }
    return clicked;
  }

  /**
   * 创建新用户
   */
  async createUser(username: string, password: string, role: string = 'user'): Promise<{
    success: boolean;
    error?: string;
  }> {
    try {
      await this.goToUsersTab();

      // 等待表单加载
      await this.page.waitForTimeout(500);

      // 填写表单
      await this.usernameInput.fill(username);
      await this.passwordInput.fill(password);

      // 选择角色
      if (role === 'admin') {
        await this.roleSelect.selectOption({ label: '系统管理员' });
      }

      await this.screenshot('before_create_user');

      // 提交表单
      await this.createUserButton.click();

      // 等待处理
      await this.page.waitForTimeout(2000);

      await this.screenshot('after_create_user');

      return { success: true };
    } catch (error) {
      console.error('Create user error:', error);
      await this.screenshot('create_user_error');
      return { success: false, error: String(error) };
    }
  }

  /**
   * 获取用户数量
   */
  async getUserCount(): Promise<number> {
    try {
      // 查找用户卡片
      const userCards = this.page.locator('div:has-text("Admin"), div[class*="rounded"]');
      return await userCards.count();
    } catch {
      return 0;
    }
  }

  /**
   * 创建 Agent
   */
  async createAgent(name: string, displayName: string, agentType: string = 'rag'): Promise<{
    success: boolean;
    error?: string;
  }> {
    try {
      await this.goToAgentsTab();

      // 点击创建 Agent 按钮
      const createBtn = this.page.locator('button:has-text("创建 Agent")');
      await createBtn.click();

      await this.page.waitForTimeout(500);

      // 填写表单
      const nameInput = this.page.locator('input[placeholder*="research_assistant"], input[placeholder*="英文"]');
      await nameInput.fill(name);

      const displayNameInput = this.page.locator('input[placeholder*="研究助手"], input[placeholder*="中文"]');
      await displayNameInput.fill(displayName);

      // 选择类型
      const typeSelect = this.page.locator('select').filter({ hasText: /知识库增强型|工具型|自定义型/ });
      await typeSelect.selectOption({ label: agentType === 'rag' ? '知识库增强型' : '工具型' });

      await this.screenshot('before_create_agent');

      // 提交
      const submitBtn = this.page.locator('button:has-text("创建 Agent")');
      await submitBtn.click();

      await this.page.waitForTimeout(2000);

      await this.screenshot('after_create_agent');

      return { success: true };
    } catch (error) {
      console.error('Create agent error:', error);
      await this.screenshot('create_agent_error');
      return { success: false, error: String(error) };
    }
  }

  /**
   * 获取 Agent 数量
   */
  async getAgentCount(): Promise<number> {
    try {
      const agentCards = this.page.locator('div:has-text("上线"), div:has-text("下线")');
      return await agentCards.count();
    } catch {
      return 0;
    }
  }

  /**
   * 返回聊天界面
   */
  async backToChat(): Promise<boolean> {
    const clicked = await this.safeClick(this.backButton, '返回对话按钮');
    if (clicked) {
      await this.page.waitForTimeout(1000);
    }
    return clicked;
  }
}
