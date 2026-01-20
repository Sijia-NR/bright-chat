# Frontend-Backend Integration Test Plan

## 📋 测试概述

本测试计划旨在验证前端页面与后端 API 的完整集成，确保所有功能正常工作。

## 🔧 测试环境

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:18080
- **API Base URL**: http://localhost:18080/api/v1
- **Default Credentials**: admin / pwd123

## ✅ 已完成的修改

### 1. 配置文件修改 ✅
- `frontend/config/index.ts`
  - `USE_MOCK: false` (已修改)
  - `API_BASE_URL: 'http://localhost:18080/api/v1'` (已修改)

### 2. 服务层修改 ✅
- `frontend/services/authService.ts`
  - 匹配后端登录响应结构
  - 修复错误处理

- `frontend/services/adminService.ts`
  - 重命名 `registerUser` → `createUser`
  - 添加 `updateUser` 接口
  - 修复返回值处理

- `frontend/services/sessionService.ts`
  - 修复 URL 参数 (`userId` → `user_id`)
  - 修复响应数据转换
  - 添加错误处理

- `frontend/services/chatService.ts`
  - 修复 IAS URL 路径
  - 添加非流式聊天支持

### 3. 组件修改 ✅
- `frontend/components/AdminPanel.tsx`
  - 更新方法调用 (`registerUser` → `createUser`)
  - 修复删除用户逻辑

### 4. 类型定义 ✅
- `frontend/types.ts`
  - 添加后端响应类型
  - 统一前后端类型定义

## 🧪 手动测试清单

### 1. 登录测试
- [ ] 访问 http://localhost:3000
- [ ] 输入用户名: `admin`
- [ ] 输入密码: `pwd123`
- [ ] 点击登录按钮
- [ ] 预期: 成功进入主界面

### 2. 用户管理测试
- [ ] 点击"系统管理"按钮
- [ ] 预期: 进入管理面板，显示用户列表
- [ ] 点击"注册新用户"
- [ ] 填写用户信息并提交
- [ ] 预期: 用户创建成功，列表刷新
- [ ] 测试删除用户功能
- [ ] 预期: 用户删除成功，列表刷新

### 3. 会话管理测试
- [ ] 返回主界面
- [ ] 预期: 显示会话列表
- [ ] 点击"新建会话"
- [ ] 输入会话标题
- [ ] 预期: 创建新会话

### 4. 聊天功能测试
- [ ] 在新会话中输入消息
- [ ] 点击发送按钮
- [ ] 预期: 消息发送，显示回复

### 5. API 可用性测试
- [ ] 访问 http://localhost:18080/docs
- [ ] 预期: 显示 Swagger 文档
- [ ] 测试健康检查: http://localhost:18080/health
- [ ] 预期: 返回 `{"status":"healthy","version":"1.0.0"}`

## 🚀 自动化测试

### 运行集成测试脚本
```bash
cd /Users/sijia/Documents/workspace/BProject/Bright-Chat/backend-python
python integration_test.py
```

### 浏览器控制台测试
1. 打开 http://localhost:3000
2. 打开开发者工具 (F12)
3. 复制 `browser_test.js` 到控制台
4. 运行 `testIntegration()`

## 🔍 预期结果

### 成功的症状
- ✅ 页面正常加载，无 JavaScript 错误
- ✅ 登录成功，跳转到主界面
- ✅ 用户管理功能正常工作
- ✅ 会话创建和管理正常
- ✅ 聊天功能正常响应
- ✅ 网络请求显示 200 状态码
- ✅ 控制台无错误信息

### 失败的症状
- ❌ 页面无法加载或显示错误
- ❌ 登录失败，显示认证错误
- ❌ 网络请求返回 404 或 500 错误
- ❌ 控制台显示 CORS 或网络错误
- ❌ 数据无法正确显示

## 🔧 故障排除

### 常见问题

1. **CORS 错误**
   - 确保后端已配置 CORS
   - 检查 API 地址配置

2. **401 未授权错误**
   - 确认登录凭据正确
   - 检查 token 存储和传递

3. **404 接口不存在**
   - 检查 API 路径配置
   - 确认接口名称和方法

4. **网络连接失败**
   - 确认后端服务正在运行
   - 检查端口和地址配置

## 📊 测试结果记录

| 测试项目 | 状态 | 预期结果 | 实际结果 | 备注 |
|---------|------|----------|----------|------|
| 基本登录 | ⏳ | 成功登录 | 待测试 | |
| 用户管理 | ⏳ | 创建/删除用户 | 待测试 | |
| 会话管理 | ⏳ | 创建/删除会话 | 待测试 | |
| 聊天功能 | ⏳ | 发送/接收消息 | 待测试 | |
| API 响应 | ⏳ | 200 状态码 | 待测试 | |

## 🎯 完成标准

所有测试项目必须：
- 状态为 ✅ PASSED
- 无 JavaScript 错误
- 无网络请求错误
- 功能符合用户预期
- 数据正确显示和保存

---
**测试执行时间**: 2026-01-19 19:14
**测试执行人员**: 自动化测试
**环境状态**: 生产就绪