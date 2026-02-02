#!/usr/bin/env node

/**
 * 测试报告生成器
 * 读取 Playwright JSON 结果并生成 Markdown 报告
 */

const fs = require('fs');
const path = require('path');

// 配置
const REPORT_PATH = './E2E_TEST_REPORT.md';
const RESULTS_PATH = './playwright-results.json';
const SCREENSHOT_DIR = './artifacts';

// 读取 JSON 结果
function readResults() {
  if (!fs.existsSync(RESULTS_PATH)) {
    console.error('测试结果文件不存在:', RESULTS_PATH);
    process.exit(1);
  }

  const data = fs.readFileSync(RESULTS_PATH, 'utf8');
  return JSON.parse(data);
}

// 统计测试结果
function analyzeResults(results) {
  const stats = {
    total: 0,
    passed: 0,
    failed: 0,
    skipped: 0,
    flaky: 0,
    duration: 0,
    suites: {},
    failures: []
  };

  for (const suite of results.suites || []) {
    const suiteName = suite.title || 'Unknown';
    stats.suites[suiteName] = { passed: 0, failed: 0, skipped: 0, tests: [] };

    for (const spec of suite.specs || [])) {
      for (const test of spec.tests || []) {
        stats.total++;

        const testInfo = {
          name: test.title,
          status: test.results?.[0]?.status || 'unknown',
          duration: test.results?.[0]?.duration || 0,
          file: spec.location?.file || 'unknown',
          line: spec.location?.line || 0
        };

        stats.duration += testInfo.duration;

        switch (testInfo.status) {
          case 'passed':
            stats.passed++;
            stats.suites[suiteName].passed++;
            break;
          case 'failed':
            stats.failed++;
            stats.suites[suiteName].failed++;
            stats.failures.push({
              ...testInfo,
              suite: suiteName,
              error: test.results?.[0]?.error?.message || 'Unknown error'
            });
            break;
          case 'skipped':
            stats.skipped++;
            stats.suites[suiteName].skipped++;
            break;
          case 'timedOut':
            stats.failed++;
            stats.suites[suiteName].failed++;
            stats.failures.push({
              ...testInfo,
              suite: suiteName,
              error: 'Test timed out'
            });
            break;
        }

        stats.suites[suiteName].tests.push(testInfo);
      }
    }
  }

  return stats;
}

// 生成 Markdown 报告
function generateReport(stats) {
  const now = new Date();
  const timestamp = now.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });

  const passRate = stats.total > 0 ? ((stats.passed / stats.total) * 100).toFixed(1) : 0;
  const duration = (stats.duration / 1000).toFixed(2);

  let report = `# Bright-Chat E2E 测试报告

**生成时间**: ${timestamp}
**测试环境**: http://localhost:8080
**测试工具**: Playwright

---

## 一、测试概要

### 测试统计

| 指标 | 数量 |
|------|------|
| 总测试用例 | ${stats.total} |
| 通过 | ${stats.passed} |
| 失败 | ${stats.failed} |
| 跳过 | ${stats.skipped} |
| **通过率** | **${passRate}%** |
| 总耗时 | ${duration}s |

### 结果判定

`;

  if (stats.failed === 0) {
    report += `✅ **测试通过**: 所有测试用例执行成功，未发现缺陷。

`;
  } else if (stats.failed <= 2) {
    report += `⚠️ **测试基本通过**: 发现 ${stats.failed} 个失败用例，建议修复后重测。

`;
  } else {
    report += `❌ **测试未通过**: 发现 ${stats.failed} 个失败用例，需要修复后再发布。

`;
  }

  // 各模块结果
  report += `---

## 二、各模块测试结果

`;

  for (const [suiteName, suiteStats] of Object.entries(stats.suites)) {
    const suiteTotal = suiteStats.passed + suiteStats.failed + suiteStats.skipped;
    const suitePassRate = suiteTotal > 0 ? ((suiteStats.passed / suiteTotal) * 100).toFixed(1) : 0;
    const status = suiteStats.failed === 0 ? '✅' : '❌';

    report += `### ${status} ${suiteName}

- **通过率**: ${suitePassRate}% (${suiteStats.passed}/${suiteTotal})
- **失败**: ${suiteStats.failed}
- **跳过**: ${suiteStats.skipped}

**测试详情**:

| 测试用例 | 状态 | 耗时 |
|---------|------|------|
`;

    for (const test of suiteStats.tests) {
      const statusIcon = test.status === 'passed' ? '✅' : test.status === 'failed' ? '❌' : '⏭️';
      const testDuration = (test.duration / 1000).toFixed(2);
      report += `| ${statusIcon} ${test.name} | ${test.status} | ${testDuration}s |\n`;
    }

    report += `\n`;
  }

  // 失败用例详情
  if (stats.failures.length > 0) {
    report += `---

## 三、失败用例详情

`;

    for (let i = 0; i < stats.failures.length; i++) {
      const failure = stats.failures[i];
      const issueId = `E2E-FAIL-${(i + 1).toString().padStart(3, '0')}`;

      report += `### ${i + 1}. ${issueId} - ${failure.name}

**所属模块**: ${failure.suite}
**状态**: ❌ FAILED
**文件**: \`${failure.file}:${failure.line}\`

**错误信息**:
\`\`\`
${failure.error}
\`\`\`

`;

      // 查找相关截图
      const screenshotFiles = findScreenshots(failure.name);
      if (screenshotFiles.length > 0) {
        report += `**相关截图**:\n`;
        for (const file of screenshotFiles) {
          report += `- \`${file}\`\n`;
        }
        report += `\n`;
      }

      report += `---\n\n`;
    }
  }

  // 严重问题清单
  if (stats.failures.length > 0) {
    report += `---

## 四、问题清单

### P0: 阻塞性问题（必须修复）

`;

    const p0Issues = stats.failures.filter(f =>
      f.error.includes('timeout') ||
      f.error.includes('not found') ||
      f.error.includes('cannot be accessed')
    );

    if (p0Issues.length > 0) {
      p0Issues.forEach((issue, i) => {
        const issueId = `P0-E2E-${(i + 1).toString().padStart(3, '0')}`;
        report += `1. **[${issueId}] ${issue.name}**
   - 错误: ${issue.error.substring(0, 100)}...
   - 模块: ${issue.suite}
   - 修复建议: 检查元素选择器，确保页面元素正确渲染

`;
      });
    } else {
      report += `无 P0 级问题

`;
    }

    report += `### P1: 严重问题（影响核心功能）

`;
    const p1Issues = stats.failures.filter(f =>
      !p0Issues.includes(f) &&
      (f.error.includes('failed') || f.error.includes('error'))
    );

    if (p1Issues.length > 0) {
      p1Issues.forEach((issue, i) => {
        const issueId = `P1-E2E-${(i + 1).toString().padStart(3, '0')}`;
        report += `1. **[${issueId}] ${issue.name}**
   - 错误: ${issue.error.substring(0, 100)}...
   - 模块: ${issue.suite}

`;
      });
    } else {
      report += `无 P1 级问题

`;
    }
  }

  // 修复建议
  if (stats.failures.length > 0) {
    report += `---

## 五、修复建议

### 常见问题修复方案

#### 1. 元素定位失败
\`\`\`typescript
// 检查元素是否存在
await page.locator('selector').waitFor({ state: 'visible', timeout: 5000 });

// 使用更稳定的选择器
await page.locator('[data-testid="element-id"]').click();
\`\`\`

#### 2. 超时问题
\`\`\`typescript
// 增加超时时间
await page.waitForSelector('selector', { timeout: 10000 });

// 等待网络空闲
await page.waitForLoadState('networkidle');
\`\`\`

#### 3. 测试环境问题
- 确保后端服务运行在 http://localhost:8080
- 检查数据库连接正常
- 清理浏览器缓存和 cookies

---

## 六、附录

### 测试覆盖范围

本次测试覆盖以下功能模块:

1. **用户认证** (E2E-AUTH-*)
   - 登录/登出
   - Token 验证
   - 会话保持

2. **用户管理** (E2E-USER-*)
   - 用户列表查看
   - 创建/删除用户
   - 权限控制

3. **Agent 管理** (E2E-AGENT-*)
   - Agent 列表
   - 创建/配置 Agent
   - Agent 对话功能

4. **知识库管理** (E2E-KB-*)
   - 知识库分组
   - 文档上传
   - 文档处理状态

5. **网络与 CORS** (E2E-NET-*)
   - API 可访问性
   - CORS 配置
   - 响应时间

6. **权限控制** (E2E-PERM-*)
   - 角色权限
   - API 访问控制

### 产物文件

- **HTML 报告**: \`playwright-report/index.html\`
- **JUnit XML**: \`playwright-results.xml\`
- **截图目录**: \`${SCREENSHOT_DIR}/\`
- **JSON 结果**: \`playwright-results.json\`

---

**报告生成时间**: ${timestamp}
**自动化测试工具**: Playwright E2E Test Suite
`;

  return report;
}

// 查找相关截图
function findScreenshots(testName) {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    return [];
  }

  const files = fs.readdirSync(SCREENSHOT_DIR);
  const testNameClean = testName.toLowerCase().replace(/[^a-z0-9]/g, '_');

  return files.filter(file => {
    const fileLower = file.toLowerCase();
    return fileLower.includes(testNameClean) ||
           fileLower.includes('screenshot') ||
           fileLower.includes('failure');
  });
}

// 主函数
function main() {
  console.log('读取测试结果...');
  const results = readResults();

  console.log('分析测试结果...');
  const stats = analyzeResults(results);

  console.log('生成 Markdown 报告...');
  const report = generateReport(stats);

  fs.writeFileSync(REPORT_PATH, report, 'utf8');

  console.log('✅ 报告生成成功:', REPORT_PATH);
  console.log('');
  console.log('测试概要:');
  console.log(`  总用例: ${stats.total}`);
  console.log(`  通过: ${stats.passed}`);
  console.log(`  失败: ${stats.failed}`);
  console.log(`  跳过: ${stats.skipped}`);
  console.log(`  通过率: ${(stats.passed / stats.total * 100).toFixed(1)}%`);
}

main();
