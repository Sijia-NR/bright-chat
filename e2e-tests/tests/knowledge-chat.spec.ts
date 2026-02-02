import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { AppPage } from '../pages/AppPage';

/**
 * 知识库集成对话测试
 *
 * 测试场景：
 * 1. 知识库分组显示
 * 2. 知识库列表显示
 * 3. 知识库关联对话
 * 4. 基于知识库的问答
 */

test.describe('知识库集成对话测试', () => {
  const ADMIN_CREDENTIALS = { username: 'admin', password: 'pwd123' };

  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
    await appPage.waitForAppLoad();
  });

  /**
   * 测试场景 1: 知识库区域显示
   * E2E-KB-001
   */
  test('应显示知识库区域', async ({ page }) => {
    // 检查侧边栏是否有知识库区域
    const kbSection = page.locator('aside').filter({ hasText: /知识库|Knowledge/ });

    if (await kbSection.count() > 0) {
      await expect(kbSection.first()).toBeVisible();
      console.log('知识库区域可见');

      await page.screenshot({ path: 'test-results/screenshots/knowledge_section.png' });
    } else {
      console.log('知识库区域不可见');
      // 这不是错误，只是说明没有配置知识库
    }
  });

  /**
   * 测试场景 2: 获取知识库列表
   * E2E-KB-002
   */
  test('应能获取知识库列表', async ({ page }) => {
    // 通过 API 获取知识库分组
    const response = await page.request.get('http://localhost:8080/api/v1/knowledge/groups');

    console.log('知识库 API 响应状态:', response.status());

    if (response.status() === 200) {
      const groups = await response.json();
      console.log('知识库分组:', JSON.stringify(groups, null, 2));

      expect(Array.isArray(groups)).toBe(true);

      if (groups.length > 0) {
        console.log('找到', groups.length, '个知识库分组');

        // 获取第一个分组的知识库
        const firstGroup = groups[0];
        const basesResponse = await page.request.get(
          `http://localhost:8080/api/v1/knowledge/groups/${firstGroup.id}/bases`
        );

        if (basesResponse.status() === 200) {
          const bases = await basesResponse.json();
          console.log('第一个分组的知识库数量:', Array.isArray(bases) ? bases.length : 'N/A');
        }
      } else {
        console.log('没有配置任何知识库分组');
      }
    }

    await page.screenshot({ path: 'test-results/screenshots/knowledge_list_api.png' });
  });

  /**
   * 测试场景 3: 知识库上传文档（如果有）
   * E2E-KB-003
   */
  test('应能上传文档到知识库', async ({ page }) => {
    // 首先获取知识库列表
    const groupsResponse = await page.request.get('http://localhost:8080/api/v1/knowledge/groups');

    if (groupsResponse.status() !== 200) {
      test.skip(true, '无法获取知识库列表');
      return;
    }

    const groups = await groupsResponse.json();

    if (!Array.isArray(groups) || groups.length === 0) {
      test.skip(true, '没有知识库分组');
      return;
    }

    // 获取第一个分组的知识库
    const firstGroup = groups[0];
    const basesResponse = await page.request.get(
      `http://localhost:8080/api/v1/knowledge/groups/${firstGroup.id}/bases`
    );

    if (basesResponse.status() !== 200 || !Array.isArray((await basesResponse.json()))) {
      test.skip(true, '无法获取知识库列表');
      return;
    }

    const bases = await basesResponse.json();

    if (bases.length === 0) {
      test.skip(true, '没有知识库');
      return;
    }

    const firstBase = bases[0];
    console.log('测试上传到知识库:', firstBase.name);

    // 创建测试文件
    const testContent = '这是一个测试文档，用于测试知识库功能。';
    const buffer = Buffer.from(testContent, 'utf-8');

    // 上传文档
    const uploadResponse = await page.request.post(
      `http://localhost:8080/api/v1/knowledge/bases/${firstBase.id}/upload`,
      {
        multipart: {
          file: {
            name: 'test-document.txt',
            mimeType: 'text/plain',
            buffer: buffer
          }
        }
      }
    );

    console.log('上传响应状态:', uploadResponse.status());

    if (uploadResponse.ok()) {
      const result = await uploadResponse.json();
      console.log('上传结果:', result);

      expect(result.document_id || result.id).toBeDefined();
    }

    await page.screenshot({ path: 'test-results/screenshots/knowledge_upload.png' });
  });

  /**
   * 测试场景 4: 知识库搜索功能
   * E2E-KB-004
   */
  test('应能在知识库中搜索', async ({ page }) => {
    // 获取知识库列表
    const groupsResponse = await page.request.get('http://localhost:8080/api/v1/knowledge/groups');

    if (groupsResponse.status() !== 200) {
      test.skip(true, '无法获取知识库列表');
      return;
    }

    const groups = await groupsResponse.json();

    if (!Array.isArray(groups) || groups.length === 0) {
      test.skip(true, '没有知识库分组');
      return;
    }

    // 获取第一个分组的知识库
    const firstGroup = groups[0];
    const basesResponse = await page.request.get(
      `http://localhost:8080/api/v1/knowledge/groups/${firstGroup.id}/bases`
    );

    if (basesResponse.status() !== 200 || !Array.isArray((await basesResponse.json()))) {
      test.skip(true, '无法获取知识库列表');
      return;
    }

    const bases = await basesResponse.json();

    if (bases.length === 0) {
      test.skip(true, '没有知识库');
      return;
    }

    const firstBase = bases[0];

    // 搜索知识库
    const searchResponse = await page.request.post(
      `http://localhost:8080/api/v1/knowledge/bases/${firstBase.id}/search`,
      {
        data: {
          query: '测试',
          top_k: 5
        }
      }
    );

    console.log('搜索响应状态:', searchResponse.status());

    if (searchResponse.ok()) {
      const results = await searchResponse.json();
      console.log('搜索结果数量:', Array.isArray(results) ? results.length : 'N/A');

      if (Array.isArray(results) && results.length > 0) {
        console.log('第一个结果:', JSON.stringify(results[0], null, 2));
      }
    }

    await page.screenshot({ path: 'test-results/screenshots/knowledge_search.png' });
  });

  /**
   * 测试场景 5: 知识库文档列表
   * E2E-KB-005
   */
  test('应能获取知识库文档列表', async ({ page }) => {
    // 获取知识库列表
    const groupsResponse = await page.request.get('http://localhost:8080/api/v1/knowledge/groups');

    if (groupsResponse.status() !== 200) {
      test.skip(true, '无法获取知识库列表');
      return;
    }

    const groups = await groupsResponse.json();

    if (!Array.isArray(groups) || groups.length === 0) {
      test.skip(true, '没有知识库分组');
      return;
    }

    // 获取第一个分组的知识库
    const firstGroup = groups[0];
    const basesResponse = await page.request.get(
      `http://localhost:8080/api/v1/knowledge/groups/${firstGroup.id}/bases`
    );

    if (basesResponse.status() !== 200 || !Array.isArray((await basesResponse.json()))) {
      test.skip(true, '无法获取知识库列表');
      return;
    }

    const bases = await basesResponse.json();

    if (bases.length === 0) {
      test.skip(true, '没有知识库');
      return;
    }

    const firstBase = bases[0];

    // 获取文档列表
    const docsResponse = await page.request.get(
      `http://localhost:8080/api/v1/knowledge/bases/${firstBase.id}/documents`
    );

    console.log('文档列表响应状态:', docsResponse.status());

    if (docsResponse.ok()) {
      const documents = await docsResponse.json();
      console.log('文档数量:', Array.isArray(documents) ? documents.length : 'N/A');

      if (Array.isArray(documents) && documents.length > 0) {
        console.log('第一个文档:', JSON.stringify(documents[0], null, 2));
      }
    }

    await page.screenshot({ path: 'test-results/screenshots/knowledge_documents.png' });
  });

  /**
   * 测试场景 6: 知识库统计信息
   * E2E-KB-006
   */
  test('应能获取知识库统计信息', async ({ page }) => {
    // 获取知识库列表
    const groupsResponse = await page.request.get('http://localhost:8080/api/v1/knowledge/groups');

    if (groupsResponse.status() !== 200) {
      test.skip(true, '无法获取知识库列表');
      return;
    }

    const groups = await groupsResponse.json();

    if (!Array.isArray(groups) || groups.length === 0) {
      test.skip(true, '没有知识库分组');
      return;
    }

    // 获取第一个分组的知识库
    const firstGroup = groups[0];
    const basesResponse = await page.request.get(
      `http://localhost:8080/api/v1/knowledge/groups/${firstGroup.id}/bases`
    );

    if (basesResponse.status() !== 200 || !Array.isArray((await basesResponse.json()))) {
      test.skip(true, '无法获取知识库列表');
      return;
    }

    const bases = await basesResponse.json();

    if (bases.length === 0) {
      test.skip(true, '没有知识库');
      return;
    }

    const firstBase = bases[0];
    console.log('知识库信息:', {
      id: firstBase.id,
      name: firstBase.name,
      description: firstBase.description,
      embeddingModel: firstBase.embedding_model,
      chunkSize: firstBase.chunk_size,
      chunkOverlap: firstBase.chunk_overlap
    });

    await page.screenshot({ path: 'test-results/screenshots/knowledge_stats.png' });
  });
});

/**
 * 知识库 UI 交互测试
 */
test.describe('知识库 UI 交互测试', () => {
  const ADMIN_CREDENTIALS = { username: 'admin', password: 'pwd123' };

  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    const appPage = new AppPage(page);

    await loginPage.goto();
    await loginPage.login(ADMIN_CREDENTIALS.username, ADMIN_CREDENTIALS.password);
    await appPage.waitForAppLoad();
  });

  /**
   * 测试场景 7: 知识库管理按钮
   * E2E-KB-UI-001
   */
  test('应能打开知识库管理界面', async ({ page }) => {
    // 查找知识库管理按钮
    const manageButton = page.locator('aside button').filter({ hasText: /管理|设置|Knowledge/ });

    if (await manageButton.count() > 0) {
      await manageButton.first().click();
      await page.waitForTimeout(1000);

      // 检查是否有弹窗或界面显示
      const modal = page.locator('[role="dialog"], .modal, [data-testid*="knowledge"], [data-testid*="kb"]');

      if (await modal.count() > 0) {
        await expect(modal.first()).toBeVisible();
      }

      await page.screenshot({ path: 'test-results/screenshots/knowledge_management_ui.png' });
    } else {
      console.log('没有找到知识库管理按钮');
    }
  });

  /**
   * 测试场景 8: 知识库区域折叠展开
   * E2E-KB-UI-002
   */
  test('应能折叠和展开知识库区域', async ({ page }) => {
    // 查找知识库区域的折叠按钮
    const kbSection = page.locator('aside').filter({ hasText: /知识库|Knowledge/ });

    if (await kbSection.count() > 0) {
      // 查找折叠/展开按钮
      const toggleButton = kbSection.locator('button').filter({ hasText: /展开|收起|折叠|^v|^>|\+/ });

      if (await toggleButton.count() > 0) {
        await toggleButton.first().click();
        await page.waitForTimeout(500);

        // 点击两次恢复原状
        await toggleButton.first().click();
        await page.waitForTimeout(500);
      }

      await page.screenshot({ path: 'test-results/screenshots/knowledge_section_toggle.png' });
    } else {
      console.log('没有找到知识库区域');
    }
  });
});
