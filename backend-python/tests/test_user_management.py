"""
用户管理模块测试
User Management Module Tests

测试 admin 用户的完整 CRUD 功能
Test complete CRUD functionality for admin users
"""
import requests
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://localhost:8080/api/v1"


def get_admin_token():
    """获取 admin 用户的 token"""
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "pwd123"
    })
    assert resp.status_code == 200, f"登录失败: {resp.text}"
    return resp.json()["token"]


def get_auth_headers(token):
    """获取认证头"""
    return {"Authorization": f"Bearer {token}"}


def test_list_users():
    """测试：获取用户列表"""
    print("\n[测试] 获取用户列表...")
    token = get_admin_token()
    response = requests.get(
        f"{BASE_URL}/admin/users",
        headers=get_auth_headers(token)
    )
    assert response.status_code == 200, f"获取用户列表失败: {response.text}"
    users = response.json()
    assert isinstance(users, list), "用户列表应该是数组"
    assert len(users) >= 1, "至少应该有一个用户"
    print(f"✅ 成功获取 {len(users)} 个用户")
    for user in users:
        print(f"   - {user['username']} ({user['role']})")
    return users


def test_create_user():
    """测试：创建新用户"""
    print("\n[测试] 创建新用户...")
    token = get_admin_token()

    # 生成唯一用户名（避免重复）
    import time
    unique_username = f"testuser_{int(time.time())}"

    response = requests.post(
        f"{BASE_URL}/admin/users",
        headers=get_auth_headers(token),
        json={
            "username": unique_username,
            "password": "test123",
            "role": "user"
        }
    )
    assert response.status_code == 200, f"创建用户失败: {response.text}"
    data = response.json()
    assert data["username"] == unique_username, "用户名不匹配"
    assert data["role"] == "user", "角色不匹配"
    assert "id" in data, "缺少用户 ID"
    print(f"✅ 成功创建用户: {data['username']} (ID: {data['id']})")
    return data


def test_duplicate_user():
    """测试：创建重复用户应该失败"""
    print("\n[测试] 创建重复用户...")
    token = get_admin_token()

    # 创建第一个用户
    import time
    username = f"dup_test_{int(time.time())}"
    requests.post(
        f"{BASE_URL}/admin/users",
        headers=get_auth_headers(token),
        json={"username": username, "password": "pass", "role": "user"}
    )

    # 尝试创建重复用户
    response = requests.post(
        f"{BASE_URL}/admin/users",
        headers=get_auth_headers(token),
        json={"username": username, "password": "pass", "role": "user"}
    )
    # 期望失败（400 或 409）
    assert response.status_code in [400, 409], f"重复用户应该失败: {response.text}"
    print(f"✅ 成功拒绝重复用户 (状态码: {response.status_code})")


def test_update_user():
    """测试：更新用户信息"""
    print("\n[测试] 更新用户信息...")
    token = get_admin_token()

    # 先创建一个测试用户
    import time
    response = requests.post(
        f"{BASE_URL}/admin/users",
        headers=get_auth_headers(token),
        json={"username": f"toupdate_{int(time.time())}", "password": "pass", "role": "user"}
    )
    user = response.json()
    user_id = user["id"]

    # 更新用户
    response = requests.put(
        f"{BASE_URL}/admin/users/{user_id}",
        headers=get_auth_headers(token),
        json={"username": "updated_user", "role": "admin"}
    )
    assert response.status_code == 200, f"更新用户失败: {response.text}"
    updated_user = response.json()
    assert updated_user["username"] == "updated_user", "用户名未更新"
    assert updated_user["role"] == "admin", "角色未更新"
    print(f"✅ 成功更新用户: {updated_user['username']} (角色: {updated_user['role']})")


def test_delete_user():
    """测试：删除用户"""
    print("\n[测试] 删除用户...")
    token = get_admin_token()

    # 创建测试用户
    import time
    response = requests.post(
        f"{BASE_URL}/admin/users",
        headers=get_auth_headers(token),
        json={"username": f"todelete_{int(time.time())}", "password": "pass", "role": "user"}
    )
    user = response.json()
    user_id = user["id"]

    # 删除用户
    response = requests.delete(
        f"{BASE_URL}/admin/users/{user_id}",
        headers=get_auth_headers(token)
    )
    assert response.status_code == 200, f"删除用户失败: {response.text}"

    # 验证用户已删除（再次获取应该失败）
    response = requests.get(
        f"{BASE_URL}/admin/users/{user_id}",
        headers=get_auth_headers(token)
    )
    assert response.status_code == 404, "删除后用户应该不存在"
    print(f"✅ 成功删除用户 (ID: {user_id})")


def test_unauthorized_access():
    """测试：普通用户无法访问用户管理"""
    print("\n[测试] 普通用户权限控制...")

    # 创建普通用户
    token = get_admin_token()
    import time
    username = f"normaluser_{int(time.time())}"
    requests.post(
        f"{BASE_URL}/admin/users",
        headers=get_auth_headers(token),
        json={"username": username, "password": "pass", "role": "user"}
    )

    # 用普通用户登录
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": "pass"
    })
    user_token = resp.json()["token"]

    # 尝试访问用户管理（应该失败）
    response = requests.get(
        f"{BASE_URL}/admin/users",
        headers=get_auth_headers(user_token)
    )
    assert response.status_code == 403, f"普通用户不应该访问用户管理: {response.text}"
    print(f"✅ 成功拒绝普通用户访问 (状态码: {response.status_code})")


def test_get_user_by_id():
    """测试：通过 ID 获取用户"""
    print("\n[测试] 通过 ID 获取用户...")
    token = get_admin_token()

    # 获取用户列表
    users = requests.get(
        f"{BASE_URL}/admin/users",
        headers=get_auth_headers(token)
    ).json()

    # 获取第一个用户
    user_id = users[0]["id"]
    response = requests.get(
        f"{BASE_URL}/admin/users/{user_id}",
        headers=get_auth_headers(token)
    )
    assert response.status_code == 200, f"获取用户详情失败: {response.text}"
    user = response.json()
    assert user["id"] == user_id, "用户 ID 不匹配"
    print(f"✅ 成功获取用户详情: {user['username']}")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始用户管理模块测试")
    print("=" * 60)

    tests = [
        ("获取用户列表", test_list_users),
        ("创建新用户", test_create_user),
        ("重复用户检查", test_duplicate_user),
        ("更新用户信息", test_update_user),
        ("删除用户", test_delete_user),
        ("权限控制", test_unauthorized_access),
        ("获取用户详情", test_get_user_by_id),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"❌ 测试失败: {name}")
            print(f"   错误: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ 测试异常: {name}")
            print(f"   异常: {e}")

    print("\n" + "=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
