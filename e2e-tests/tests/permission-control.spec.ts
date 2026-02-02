import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { AppPage } from '../pages/AppPage';
import { AdminPage } from '../pages/AdminPage';

/**
 * 权限控制测试套件
 *
 * 测试场景：
 * 1. 普通 user 角色无法访问管理面板
 * 2. Admin 角色可以访问管理面板
 * 3. API 端点权限控制
 * 4. 角色显示正确
 */

test.describe('权限控制测试', () => {
  const ADMIN_CREDENTIALS = { username: 'admin', password: 'pwd123' };

  /**
   * 测试场景 1: Admin 用户可以看到管理面板按钮
   * E2E-PERM-001
   */
  test('Admin 用户应看到管理面板按钮', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    // 使用 admin 登录
    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);

    // 检查是否有管理面板按钮
    const hasAdminButton = await appPage.elementExists('button[title="系统管理"], button:has-text("管理面板")', 3000);

    expect(hasAdminButton, 'Admin 用户应看到管理面板按钮').toBe(true);

    await appPage.screenshot('admin_has_management_button');
  });

  /**
   * 测试场景 2: Admin 用户可以打开管理面板
   * E2E-PERM-002
   */
  test('Admin 用户应能打开管理面板', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);
    const adminPage = new AdminPage(page);

    // 使用 admin 登录
    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);

    // 打开管理面板
    const opened = await appPage.openAdminPanel();

    expect(opened, 'Admin 用户应能打开管理面板').toBe(true);

    const isAdminVisible = await adminPage.isAdminPanelVisible();
    expect(isAdminVisible, '应显示管理面板').toBe(true);

    await adminPage.screenshot('admin_panel_accessible_by_admin');
  });

  /**
   * 测试场景 3: 用户角色标签显示正确
   * E2E-PERM-003
   */
  test('Admin 用户应显示 Admin 角色标签', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    // 使用 admin 登录
    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);

    // 检查用户信息区域的 Admin 标签
    const hasAdminLabel = await appPage.elementExists('aside:has-text("admin")', 3000);
    const hasRoleLabel = await appPage.elementExists('aside:has-text("Admin")', 3000);

    expect(hasAdminLabel || hasRoleLabel, '应显示 Admin 角色标签').toBe(true);

    await appPage.screenshot('admin_role_displayed');
  });

  /**
   * 测试场景 4: 登录状态持久化
   * E2E-PERM-004
   */
  test('刷新页面后应保持登录状态', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    // 登录
    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);

    // 刷新页面
    await page.reload();
    await page.waitForTimeout(2000);

    // 验证仍然登录
    const isLoggedIn = await loginPage.isLoggedIn();
    expect(isLoggedIn, '刷新后应保持登录').toBe(true);
  });

  /**
   * 测试场景 5: API 权限 - 未认证无法访问
   * E2E-PERM-005
   */
  test('未认证用户无法访问受保护的 API', async ({ request }) => {
    // 不带 token 访问受保护端点
    const response = await request.get('http://localhost:8080/api/v1/sessions/');

    // 应返回 401 或 403
    expect([401, 403, 422]).toContain(response.status());
  });

  /**
   * 测试场景 6: API 权限 - 认证后可访问
   * E2E-PERM-006
   */
  test('认证后可访问受保护的 API', async ({ request }) => {
    // 先登录获取 token
    const loginResponse = await request.post('http://localhost:8080/api/v1/auth/login', {
      data: {
        username: 'admin',
        password: 'pwd123'
      }
    });

    expect(loginResponse.ok()).toBe(true);

    const loginData = await loginResponse.json();
    const token = loginData.access_token || loginData.token;

    expect(token).toBeDefined();

    // 使用 token 访问受保护端点
    const response = await request.get('http://localhost:8080/api/v1/sessions/', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    // 应返回成功
    expect([200, 404]).toContain(response.status());
  });

  /**
   * 测试场景 7: 登出后无法访问管理面板
   * E2E-PERM-007
   */
  test('登出后应返回登录页', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    // 登录
    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);

    // 登出
    await appPage.logout();

    // 验证返回登录页
    const isLoginFormVisible = await loginPage.isLoginFormVisible();
    expect(isLoginFormVisible, '登出后应显示登录表单').toBe(true);

    // 验证无法直接访问管理面板
    await page.goto('/admin');
    await page.waitForTimeout(1000);

    const stillOnLogin = await loginPage.isLoginFormVisible();
    expect(stillOnLogin, '仍应在登录页').toBe(true);
  });

  /**
   * 测试场景 8: 登录 API 错误处理
   * E2E-PERM-008
   */
  test('登录 API 应正确处理错误凭据', async ({ request }) => {
    const response = await request.post('http://localhost:8080/api/v1/auth/login', {
      data: {
        username: 'wronguser',
        password: 'wrongpass'
      }
    });

    // 应返回错误状态
    expect([400, 401, 422]).toContain(response.status());
  });

  /**
   * 测试场景 9: Token 过期处理
   * E2E-PERM-009
   */
  test('应正确处理无效 token', async ({ request }) => {
    // 使用无效 token
    const response = await request.get('http://localhost:8080/api/v1/sessions/', {
      headers: {
        'Authorization': 'Bearer invalid_token_12345'
      }
    });

    // 应返回未授权错误
    expect([401, 403]).toContain(response.status());
  });

  /**
   * 测试场景 10: 管理面板选项卡访问
   * E2E-PERM-010
   */
  test('Admin 用户可以访问所有管理面板选项卡', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);
    const adminPage = new AdminPage(page);

    // 登录
    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);

    // 打开管理面板
    await appPage.openAdminPanel();

    // 测试用户管理标签
    const usersTabOk = await adminPage.goToUsersTab();
    expect(usersTabOk, '应能访问用户管理').toBe(true);

    // 测试模型管理标签
    const modelsTabOk = await adminPage.goToModelsTab();
    expect(modelsTabOk, '应能访问模型管理').toBe(true);

    // 测试 Agent 管理标签
    const agentsTabOk = await adminPage.goToAgentsTab();
    expect(agentsTabOk, '应能访问 Agent 管理').toBe(true);

    await adminPage.screenshot('all_admin_tabs_accessible');
  });
});
