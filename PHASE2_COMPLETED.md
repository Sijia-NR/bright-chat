# 阶段二完成：用户管理模块

## 执行时间
完成时间：2026-01-28 09:00

## 修改的文件

### 1. backend-python/minimal_api.py

#### 添加的模型：
```python
class UserUpdate(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None
```

#### 修复的端点（添加认证和权限检查）：
1. **GET /api/v1/admin/users** - 获取用户列表（admin only）
2. **GET /api/v1/admin/users/{user_id}** - 获取单个用户（新增，admin only）
3. **POST /api/v1/admin/users** - 创建用户（admin only）
4. **PUT /api/v1/admin/users/{user_id}** - 更新用户（admin only）
5. **DELETE /api/v1/admin/users/{user_id}** - 删除用户（admin only）

所有端点现在都：
- ✅ 要求用户认证（`get_current_user`）
- ✅ 检查 admin 权限（`current_user.role != UserRole.ADMIN`）
- ✅ 返回正确的 HTTP 状态码

### 2. backend-python/tests/test_user_management.py（新建）

创建完整的测试套件：
- test_list_users - 获取用户列表
- test_create_user - 创建新用户
- test_duplicate_user - 重复用户检查
- test_update_user - 更新用户信息
- test_delete_user - 删除用户
- test_unauthorized_access - 权限控制
- test_get_user_by_id - 获取用户详情

## 测试结果

### ✅ 所有测试通过（7/7）

```
[测试] 获取用户列表...
✅ 成功获取 6 个用户

[测试] 创建新用户...
✅ 成功创建用户: testuser_1769562073

[测试] 创建重复用户...
✅ 成功拒绝重复用户 (状态码: 400)

[测试] 更新用户信息...
✅ 成功更新用户: updated_user (角色: admin)

[测试] 删除用户...
✅ 成功删除用户

[测试] 普通用户权限控制...
✅ 成功拒绝普通用户访问 (状态码: 403)

[测试] 通过 ID 获取用户...
✅ 成功获取用户详情
```

## API 端点总览

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | /api/v1/admin/users | Admin | 获取所有用户 |
| GET | /api/v1/admin/users/{id} | Admin | 获取单个用户 |
| POST | /api/v1/admin/users | Admin | 创建用户 |
| PUT | /api/v1/admin/users/{id} | Admin | 更新用户 |
| DELETE | /api/v1/admin/users/{id} | Admin | 删除用户 |

## 验收标准

- ✅ admin 可以查看用户列表
- ✅ 可以创建新用户
- ✅ 可以更新用户信息
- ✅ 可以删除用户
- ✅ user 角色无法访问用户管理（返回 403）
- ✅ 所有测试通过

## 前端测试

### AdminPanel 组件检查

需要确保 `frontend/components/AdminPanel.tsx` 中的用户管理功能与 API 匹配：
- 用户列表显示
- 创建用户表单
- 编辑用户功能
- 删除用户确认

### API 调用示例

```typescript
// 获取用户列表
const users = await fetch('http://localhost:8080/api/v1/admin/users', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// 创建用户
const newUser = await fetch('http://localhost:8080/api/v1/admin/users', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'newuser',
    password: 'pass123',
    role: 'user'
  })
}).then(r => r.json());

// 更新用户
await fetch(`http://localhost:8080/api/v1/admin/users/${userId}`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'updated_user',
    role: 'admin'
  })
});

// 删除用户
await fetch(`http://localhost:8080/api/v1/admin/users/${userId}`, {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

## 下一步

进入**阶段三：知识库模块**
- Track A: 知识库基础功能（前端 + 后端 API）
- Track B: 文档处理与向量化（后端核心）

## 备注

1. **UserUpdate 模型**：不包含 password 字段，密码应该通过专门的端点更新（安全性考虑）
2. **权限检查**：所有 /api/v1/admin/* 端点现在都要求 admin 角色
3. **测试覆盖率**：7 个测试用例覆盖所有 CRUD 操作和权限控制
