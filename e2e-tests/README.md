# Bright-Chat E2E 测试套件

## 快速开始

### 安装依赖

```bash
npm install
npx playwright install chromium
```

### 运行测试

```bash
# 运行所有测试
npm test

# 运行特定测试文件
npm test tests/auth.spec.ts

# 查看测试报告
npm run report

# 调试模式（带浏览器）
npm run test:debug
```

## 测试结构

```
e2e-tests/
├── tests/              # 测试用例
│   ├── auth.spec.ts
│   ├── user-management.spec.ts
│   ├── agent-management.spec.ts
│   ├── knowledge-management.spec.ts
│   ├── cors-network.spec.ts
│   ├── chat-functionality.spec.ts
│   └── permission-control.spec.ts
├── pages/              # 页面对象模型
│   ├── BasePage.ts
│   ├── LoginPage.ts
│   ├── AppPage.ts
│   └── AdminPage.ts
├── artifacts/          # 测试截图
├── playwright-report/  # HTML 报告
└── E2E_TEST_REPORT.md # 测试报告
```

## 测试覆盖范围

- ✅ 用户认证 (登录/登出/Token)
- ✅ 用户管理 (CRUD/权限)
- ✅ Agent 管理 (创建/配置/删除)
- ✅ 知识库管理 (分组/文档)
- ✅ 网络与 CORS (API/响应时间)
- ✅ 聊天功能 (发送/接收)
- ✅ 权限控制 (角色/API)

## 当前测试结果

- **通过率**: 67.6%
- **总用例**: 68
- **通过**: 46
- **失败**: 22
- **跳过**: 2

## 常见问题

### 测试失败

1. 确保服务运行在正确端口:
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8080

2. 检查测试账号:
   - 用户名: admin
   - 密码: pwd123

### 查看截图

```bash
ls -la artifacts/
```

### 调试测试

```bash
# 使用 Playwright Inspector
npx playwright test --debug

# 使用 headed 模式（需要 X11）
npx playwright test --headed
```
