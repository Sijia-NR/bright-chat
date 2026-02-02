import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { AppPage } from '../pages/AppPage';
import { AdminPage } from '../pages/AdminPage';

/**
 * 用户管理测试套件
 *
 * 测试场景：
 * 1. 查看用户列表
 * 2. 创建新用户
 * 3. 编辑用户信息
 * 4. 删除用户
 * 5. 权限控制（普通用户无法访问）
 */

test.describe('用户管理测试（仅 Admin）', () => {
  const ADMIN_CREDENTIALS = { username: 'admin', password: 'pwd123' };

  let loginPage: LoginPage;
  let appPage: AppPage;
  let adminPage: AdminPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    appPage = new AppPage(page);
    adminPage = new AdminPage(page);

    // 使用 admin 账号登录
    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
  });

  /**
   * 测试场景 1: 访问管理面板
   * E2E-USER-001
   */
  test('Admin 用户应能访问管理面板', async ({ page }) => {
    const opened = await appPage.openAdminPanel();
    expect(opened, '应能打开管理面板').toBe(true);

    const isAdminVisible = await adminPage.isAdminPanelVisible();
    expect(isAdminVisible, '应显示系统管理中心').toBe(true);

    await adminPage.screenshot('admin_panel_accessible');
  });

  /**
   * 测试场景 2: 查看用户管理标签
   * E2E-USER-002
   */
  test('应能切换到用户管理标签', async ({ page }) => {
    await appPage.openAdminPanel();

    const switched = await adminPage.goToUsersTab();
    expect(switched, '应能切换到用户管理标签').toBe(true);

    // 验证用户列表标题存在
    const hasUserList = await adminPage.elementExists('text=用户管理列表', 3000);
    expect(hasUserList, '应显示用户管理列表').toBe(true);

    await adminPage.screenshot('user_management_tab');
  });

  /**
   * 测试场景 3: 查看用户列表
   * E2E-USER-003
   */
  test('应能查看用户列表', async ({ page }) => {
    await appPage.openAdminPanel();
    await adminPage.goToUsersTab();

    // 等待用户列表加载
    await page.waitForTimeout(1000);

    const userCount = await adminPage.getUserCount();
    expect(userCount, '用户列表应至少有 admin 用户').toBeGreaterThanOrEqual(1);

    // 验证 admin 用户存在
    const hasAdmin = await adminPage.elementExists('text=admin', 3000);
    expect(hasAdmin, '应显示 admin 用户').toBe(true);

    await adminPage.screenshot('user_list_displayed');
  });

  /**
   * 测试场景 4: 创建新用户
   * E2E-USER-004
   */
  test('应能创建新用户', async ({ page }) => {
    await appPage.openAdminPanel();
    await adminPage.goToUsersTab();

    // 生成唯一用户名
    const timestamp = Date.now();
    const newUser = {
      username: `test_user_${timestamp}`,
      password: 'test123456',
      role: 'user'
    };

    // 获取创建前的用户数
    const beforeCount = await adminPage.getUserCount();

    // 创建用户
    const result = await adminPage.createUser(
      newUser.username,
      newUser.password,
      newUser.role
    );

    expect(result.success, '创建用户应成功').toBe(true);

    // 等待列表更新
    await page.waitForTimeout(2000);

    // 验证用户已添加（数量增加或能在列表中找到）
    const afterCount = await adminPage.getUserCount();
    const hasNewUser = await adminPage.elementExists(`text=${newUser.username}`, 3000);

    expect(hasNewUser || afterCount > beforeCount, '新用户应出现在列表中').toBe(true);
  });

  /**
   * 测试场景 5: 创建 Admin 角色用户
   * E2E-USER-005
   */
  test('应能创建 Admin 角色的用户', async ({ page }) => {
    await appPage.openAdminPanel();
    await adminPage.goToUsersTab();

    const timestamp = Date.now();
    const newAdmin = {
      username: `test_admin_${timestamp}`,
      password: 'admin123456',
      role: 'admin'
    };

    const result = await adminPage.createUser(
      newAdmin.username,
      newAdmin.password,
      newAdmin.role
    );

    expect(result.success, '创建 Admin 用户应成功').toBe(true);
  });

  /**
   * 测试场景 6: 创建用户表单验证
   * E2E-USER-006
   */
  test('创建用户表单应正常交互', async ({ page }) => {
    await appPage.openAdminPanel();
    await adminPage.goToUsersTab();

    // 验证表单元素存在
    expect(await adminPage.elementExists('input[placeholder*="用户名"], input[placeholder*="田户名"]')).toBe(true);
    expect(await adminPage.elementExists('input[placeholder*="密码"]')).toBe(true);
    expect(await adminPage.elementExists('select')).toBe(true);

    // 测试角色选择
    const roleSelect = page.locator('select');
    await roleSelect.selectOption('user');
    await page.waitForTimeout(500);

    const selectedValue = await roleSelect.inputValue();
    expect(selectedValue).toBeTruthy();
  });

  /**
   * 测试场景 7: 删除用户
   * E2E-USER-007
   */
  test('应能删除用户（非当前登录用户）', async ({ page }) => {
    await appPage.openAdminPanel();
    await adminPage.goToUsersTab();

    // 先创建一个测试用户
    const timestamp = Date.now();
    const tempUser = `temp_delete_${timestamp}`;
    await adminPage.createUser(tempUser, 'temp123', 'user');
    await page.waitForTimeout(2000);

    // 查找该用户的删除按钮
    const deleteButton = page.locator('div').filter({ hasText: tempUser }).locator('button, [class*="trash"]').first();

    // 点击删除按钮
    await deleteButton.click();
    await page.waitForTimeout(1000);

    // 确认删除
    const confirmButton = page.locator('button:has-text("确认"), button:has-text("删除")');
    await confirmButton.first().click();
    await page.waitForTimeout(2000);

    // 验证用户已删除
    const userExists = await adminPage.elementExists(`text=${tempUser}`, 2000);
    expect(userExists, '被删除的用户不应在列表中').toBe(false);
  });

  /**
   * 测试场景 8: 无法删除当前登录用户
   * E2E-USER-008
   */
  test('不应显示当前登录用户的删除按钮', async ({ page }) => {
    await appPage.openAdminPanel();
    await adminPage.goToUsersTab();

    // 查找 admin 用户的删除按钮（不应该存在）
    const adminUserCard = page.locator('div').filter({ hasText: 'admin' });
    const deleteButtonCount = await adminUserCard.locator('button, [class*="trash"]').count();

    // Admin 用户的删除按钮应该不显示或禁用
    expect(deleteButtonCount).toBe(0);
  });

  /**
   * 测试场景 9: 返回聊天功能
   * E2E-USER-009
   */
  test('应能从管理面板返回聊天', async ({ page }) => {
    await appPage.openAdminPanel();

    const backSuccess = await adminPage.backToChat();
    expect(backSuccess, '应能返回聊天界面').toBe(true);

    // 验证回到了聊天界面
    const hasWorkbench = await adminPage.elementExists('text=AI工作台', 3000);
    expect(hasWorkbench, '应显示 AI 工作台').toBe(true);
  });

  /**
   * 测试场景 10: LLM 模型管理标签
   * E2E-USER-010
   */
  test('应能访问 LLM 模型管理标签', async ({ page }) => {
    await appPage.openAdminPanel();

    const switched = await adminPage.goToModelsTab();
    expect(switched, '应能切换到模型管理标签').toBe(true);

    await page.waitForTimeout(1000);
    await adminPage.screenshot('model_management_tab');
  });
});
