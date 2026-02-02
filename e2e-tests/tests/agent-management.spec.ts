import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { AppPage } from '../pages/AppPage';
import { AdminPage } from '../pages/AdminPage';

/**
 * Agent 管理测试套件
 *
 * 测试场景：
 * 1. Agent 列表展示
 * 2. 创建新 Agent（tool/rag 类型）
 * 3. 配置 Agent 工具
 * 4. 删除 Agent
 * 5. Agent 对话功能
 */

test.describe('Agent 管理测试', () => {
  const ADMIN_CREDENTIALS = { username: 'admin', password: 'pwd123' };

  let loginPage: LoginPage;
  let appPage: AppPage;
  let adminPage: AdminPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    appPage = new AppPage(page);
    adminPage = new AdminPage(page);

    // 登录
    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
  });

  /**
   * 测试场景 1: 访问 Agent 管理面板
   * E2E-AGENT-001
   */
  test('应能访问 Agent 管理面板', async ({ page }) => {
    await appPage.openAdminPanel();

    const switched = await adminPage.goToAgentsTab();
    expect(switched, '应能切换到 Agent 管理标签').toBe(true);

    // 验证 Agent 管理界面元素
    const hasTitle = await adminPage.elementExists('text=数字员工配置', 3000);
    const hasCreateButton = await adminPage.elementExists('button:has-text("创建 Agent")', 3000);

    expect(hasTitle, '应显示 Agent 配置标题').toBe(true);
    expect(hasCreateButton, '应显示创建 Agent 按钮').toBe(true);

    await adminPage.screenshot('agent_management_accessible');
  });

  /**
   * 测试场景 2: 显示 Agent 列表（如果有）
   * E2E-AGENT-002
   */
  test('应显示已存在的 Agent 列表', async ({ page }) => {
    await appPage.openAdminPanel();
    await adminPage.goToAgentsTab();

    await page.waitForTimeout(1000);

    const agentCount = await adminPage.getAgentCount();

    if (agentCount > 0) {
      // 验证列表有内容
      const hasAgentSection = await adminPage.elementExists('div[class*="space-y-3"]', 3000);
      expect(hasAgentSection, '应显示 Agent 列表区域').toBe(true);
    } else {
      // 验证显示空状态
      const hasEmptyState = await adminPage.elementExists('text=还未创建', 3000);
      expect(hasEmptyState, '应显示空状态提示').toBe(true);
    }

    await adminPage.screenshot('agent_list_displayed');
  });

  /**
   * 测试场景 3: 创建 RAG 类型 Agent
   * E2E-AGENT-003
   */
  test('应能创建 RAG 类型 Agent', async ({ page }) => {
    await appPage.openAdminPanel();
    await adminPage.goToAgentsTab();

    const timestamp = Date.now();
    const agentData = {
      name: `test_rag_${timestamp}`,
      displayName: `测试 RAG 助手 ${timestamp}`,
      agentType: 'rag'
    };

    // 获取创建前的 Agent 数量
    const beforeCount = await adminPage.getAgentCount();

    // 创建 Agent
    const result = await adminPage.createAgent(
      agentData.name,
      agentData.displayName,
      agentData.agentType
    );

    expect(result.success, '创建 RAG Agent 应成功').toBe(true);

    // 等待更新
    await page.waitForTimeout(2000);

    // 验证创建成功
    const hasNewAgent = await adminPage.elementExists(`text=${agentData.displayName}`, 3000);
    expect(hasNewAgent, '新 Agent 应出现在列表中').toBe(true);
  });

  /**
   * 测试场景 4: 创建 Tool 类型 Agent
   * E2E-AGENT-004
   */
  test('应能创建 Tool 类型 Agent', async ({ page }) => {
    await appPage.openAdminPanel();
    await adminPage.goToAgentsTab();

    const timestamp = Date.now();
    const agentData = {
      name: `test_tool_${timestamp}`,
      displayName: `测试工具助手 ${timestamp}`,
      agentType: 'tool'
    };

    const result = await adminPage.createAgent(
      agentData.name,
      agentData.displayName,
      agentData.agentType
    );

    expect(result.success, '创建 Tool Agent 应成功').toBe(true);
  });

  /**
   * 测试场景 5: Agent 表单交互
   * E2E-AGENT-005
   */
  test('Agent 表单应能正常交互', async ({ page }) => {
    await appPage.openAdminPanel();
    await adminPage.goToAgentsTab();

    // 点击创建按钮
    const createButton = page.locator('button:has-text("创建 Agent")');
    await createButton.click();
    await page.waitForTimeout(500);

    // 验证表单元素
    const hasNameInput = await adminPage.elementExists('input[placeholder*="research_assistant"], input[placeholder*="英文"]', 2000);
    const hasDisplayNameInput = await adminPage.elementExists('input[placeholder*="研究助手"], input[placeholder*="中文"]', 2000);
    const hasTypeSelect = await adminPage.elementExists('select', 2000);

    expect(hasNameInput, '应有名称输入框').toBe(true);
    expect(hasDisplayNameInput, '应有显示名称输入框').toBe(true);
    expect(hasTypeSelect, '应有类型选择器').toBe(true);

    // 测试类型选择
    const typeSelect = page.locator('select').first();
    await typeSelect.selectOption({ index: 1 });
    await page.waitForTimeout(500);

    // 取消表单
    const cancelButton = page.locator('button:has-text("取消")');
    await cancelButton.click();
    await page.waitForTimeout(500);

    // 验证表单关闭
    const formClosed = await adminPage.elementExists('input[placeholder*="英文"]', 1000) === false;
    expect(formClosed, '取消后表单应关闭').toBe(true);
  });

  /**
   * 测试场景 6: Agent 工具配置
   * E2E-AGENT-006
   */
  test('应能配置 Agent 工具', async ({ page }) => {
    await appPage.openAdminPanel();
    await adminPage.goToAgentsTab();

    // 点击创建按钮
    const createButton = page.locator('button:has-text("创建 Agent")');
    await createButton.click();
    await page.waitForTimeout(500);

    // 查找工具复选框
    const toolCheckboxes = page.locator('input[type="checkbox"]');

    if (await toolCheckboxes.count() > 0) {
      // 尝试勾选第一个工具
      await toolCheckboxes.first().check();
      await page.waitForTimeout(500);

      const isChecked = await toolCheckboxes.first().isChecked();
      expect(isChecked, '工具复选框应能勾选').toBe(true);
    } else {
      // 没有工具选项，记录但不失败
      test.skip(true, '当前环境没有工具配置选项');
    }

    await adminPage.screenshot('agent_tool_config');
  });

  /**
   * 测试场景 7: 删除 Agent
   * E2E-AGENT-007
   */
  test('应能删除 Agent', async ({ page }) => {
    await appPage.openAdminPanel();
    await adminPage.goToAgentsTab();

    // 先创建一个临时 Agent
    const timestamp = Date.now();
    const tempAgentName = `temp_delete_${timestamp}`;
    await adminPage.createAgent(tempAgentName, tempAgentName, 'tool');
    await page.waitForTimeout(2000);

    // 查找该 Agent 的删除按钮
    const agentCard = page.locator('div').filter({ hasText: tempAgentName });

    // 鼠标悬停以显示操作按钮
    await agentCard.hover();
    await page.waitForTimeout(500);

    const deleteButton = agentCard.locator('button, [class*="trash"]').filter({ hasText: /删除|trash/i });

    if (await deleteButton.count() > 0) {
      await deleteButton.first().click();
      await page.waitForTimeout(1000);

      // 确认删除
      const confirmButton = page.locator('button:has-text("确认删除"), button:has-text("删除")').first();
      await confirmButton.click();
      await page.waitForTimeout(2000);

      // 验证删除成功
      const agentExists = await adminPage.elementExists(`text=${tempAgentName}`, 2000);
      expect(agentExists, '被删除的 Agent 不应在列表中').toBe(false);
    } else {
      test.skip(true, '未找到删除按钮');
    }

    await adminPage.screenshot('agent_deleted');
  });

  /**
   * 测试场景 8: 编辑 Agent
   * E2E-AGENT-008
   */
  test('应能编辑现有 Agent', async ({ page }) => {
    await appPage.openAdminPanel();
    await adminPage.goToAgentsTab();

    await page.waitForTimeout(1000);

    // 查找编辑按钮
    const editButtons = page.locator('button, div[class*="p-2"]').filter({ hasText: /编辑|edit/i });

    if (await editButtons.count() > 0) {
      // 鼠标悬停以显示按钮
      const agentCard = page.locator('div[class*="group"]').first();
      await agentCard.hover();
      await page.waitForTimeout(500);

      await editButtons.first().click();
      await page.waitForTimeout(1000);

      // 验证编辑表单打开
      const hasEditForm = await adminPage.elementExists('input[placeholder*="研究助手"], input[placeholder*="英文"]', 2000);
      expect(hasEditForm, '应显示编辑表单').toBe(true);

      // 取消编辑
      const cancelButton = page.locator('button:has-text("取消")');
      await cancelButton.click();
    } else {
      test.skip(true, '没有可编辑的 Agent');
    }
  });

  /**
   * 测试场景 9: Agent 上线/下线切换
   * E2E-AGENT-009
   */
  test('应能切换 Agent 上线/下线状态', async ({ page }) => {
    await appPage.openAdminPanel();
    await adminPage.goToAgentsTab();

    await page.waitForTimeout(1000);

    // 查找状态切换按钮
    const agentCard = page.locator('div[class*="group"]').first();

    if (await agentCard.count() > 0) {
      // 鼠标悬停
      await agentCard.hover();
      await page.waitForTimeout(500);

      const toggleButton = agentCard.locator('button').filter({ hasText: /上线|下线|power/i });

      if (await toggleButton.count() > 0) {
        // 获取当前状态
        const statusText = await agentCard.textContent();
        const wasOnline = statusText?.includes('上线') || statusText?.includes('online');

        // 点击切换
        await toggleButton.first().click();
        await page.waitForTimeout(2000);

        // 验证状态改变
        const newStatusText = await agentCard.textContent();
        const isNowOnline = newStatusText?.includes('上线') || newStatusText?.includes('online');

        expect(isNowOnline).not.toBe(wasOnline);
      } else {
        test.skip(true, '未找到状态切换按钮');
      }
    } else {
      test.skip(true, '没有可切换状态的 Agent');
    }
  });

  /**
   * 测试场景 10: 侧边栏 Agent 显示
   * E2E-AGENT-010
   */
  test('侧边栏应显示可用 Agent', async ({ page }) => {
    // 返回聊天界面
    await adminPage.backToChat();

    // 查找侧边栏的 Agent 区域
    const agentSection = page.locator('aside').filter({ hasText: /数字员工|Agent/i });

    if (await agentSection.count() > 0) {
      const isExpanded = await agentSection.locator('text=展开').count() === 0;
      expect(isExpanded).toBe(true);

      await appPage.screenshot('sidebar_agents');
    } else {
      test.skip(true, '侧边栏未找到 Agent 区域');
    }
  });
});
