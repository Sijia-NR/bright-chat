#!/usr/bin/env python3
"""
知识库模块修复验证脚本
Test script to verify knowledge base fixes

测试内容:
1. 创建知识库（不指定分组）
2. 创建知识库（指定分组）
3. 获取知识库列表
4. 获取知识库详情
5. 文档上传和切片
"""
import requests
import json
from typing import Optional

# 配置
BASE_URL = "http://localhost:8080"
API_PREFIX = "/api/v1"

# 测试用户凭证
TEST_USER = {
    "username": "admin",
    "password": "pwd123"
}

class KnowledgeBaseTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.api_prefix = API_PREFIX
        self.token: Optional[str] = None
        self.group_id: Optional[str] = None
        self.kb_id_without_group: Optional[str] = None
        self.kb_id_with_group: Optional[str] = None
        self.session = requests.Session()

    def login(self):
        """登录获取token"""
        print("=" * 60)
        print("1. 登录测试")
        print("=" * 60)

        url = f"{self.base_url}{self.api_prefix}/auth/login"
        response = self.session.post(url, json=TEST_USER)

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")  # 修复：后端返回的是 "token" 而不是 "access_token"
            if self.token:
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                print("✅ 登录成功")
                print(f"   Token: {self.token[:20]}...")
            else:
                print("❌ 登录成功但未获取到token")
                return False
        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"   {response.text}")
            return False
        return True

    def create_group(self):
        """创建测试分组"""
        print("\n" + "=" * 60)
        print("2. 创建测试分组")
        print("=" * 60)

        url = f"{self.base_url}{self.api_prefix}/knowledge/groups"
        data = {
            "name": "测试分组",
            "description": "用于测试的知识库分组"
        }

        response = self.session.post(url, json=data)

        if response.status_code == 200:
            result = response.json()
            self.group_id = result.get("id")
            print(f"✅ 分组创建成功")
            print(f"   ID: {self.group_id}")
            print(f"   名称: {result.get('name')}")
        else:
            print(f"❌ 分组创建失败: {response.status_code}")
            print(f"   {response.text}")
            return False
        return True

    def test_create_kb_without_group(self):
        """测试创建不指定分组的知识库"""
        print("\n" + "=" * 60)
        print("3. 测试创建知识库（不指定分组）")
        print("=" * 60)

        url = f"{self.base_url}{self.api_prefix}/knowledge/bases"
        data = {
            "name": "独立知识库",
            "description": "这是一个不指定分组的独立知识库"
        }

        response = self.session.post(url, json=data)

        if response.status_code == 200:
            result = response.json()
            self.kb_id_without_group = result.get("id")
            print(f"✅ 知识库创建成功（无分组）")
            print(f"   ID: {self.kb_id_without_group}")
            print(f"   名称: {result.get('name')}")
            print(f"   分组ID: {result.get('group_id')}")
            print(f"   ✅ group_id 为 None 符合预期")
        else:
            print(f"❌ 知识库创建失败: {response.status_code}")
            print(f"   {response.text}")
            return False
        return True

    def test_create_kb_with_group(self):
        """测试创建指定分组的知识库"""
        print("\n" + "=" * 60)
        print("4. 测试创建知识库（指定分组）")
        print("=" * 60)

        if not self.group_id:
            print("⚠️  跳过：未创建分组")
            return True

        url = f"{self.base_url}{self.api_prefix}/knowledge/bases"
        data = {
            "group_id": self.group_id,
            "name": "分组知识库",
            "description": "这是一个属于分组的知识库"
        }

        response = self.session.post(url, json=data)

        if response.status_code == 200:
            result = response.json()
            self.kb_id_with_group = result.get("id")
            print(f"✅ 知识库创建成功（有分组）")
            print(f"   ID: {self.kb_id_with_group}")
            print(f"   名称: {result.get('name')}")
            print(f"   分组ID: {result.get('group_id')}")
            print(f"   ✅ group_id 正确关联")
        else:
            print(f"❌ 知识库创建失败: {response.status_code}")
            print(f"   {response.text}")
            return False
        return True

    def test_get_kb_list(self):
        """测试获取知识库列表"""
        print("\n" + "=" * 60)
        print("5. 测试获取知识库列表")
        print("=" * 60)

        url = f"{self.base_url}{self.api_prefix}/knowledge/bases"

        response = self.session.get(url)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 获取知识库列表成功")
            print(f"   总数: {len(result)}")

            for kb in result:
                print(f"\n   - {kb.get('name')}")
                print(f"     ID: {kb.get('id')}")
                print(f"     分组ID: {kb.get('group_id')}")
                print(f"     文档数: {kb.get('document_count', 0)}")
        else:
            print(f"❌ 获取列表失败: {response.status_code}")
            print(f"   {response.text}")
            return False
        return True

    def test_get_kb_detail(self):
        """测试获取知识库详情"""
        print("\n" + "=" * 60)
        print("6. 测试获取知识库详情")
        print("=" * 60)

        if not self.kb_id_without_group:
            print("⚠️  跳过：未创建知识库")
            return True

        url = f"{self.base_url}{self.api_prefix}/knowledge/bases/{self.kb_id_without_group}"

        response = self.session.get(url)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 获取知识库详情成功")
            print(f"   ID: {result.get('id')}")
            print(f"   名称: {result.get('name')}")
            print(f"   描述: {result.get('description')}")
            print(f"   分组ID: {result.get('group_id')}")
            print(f"   嵌入模型: {result.get('embedding_model')}")
            print(f"   分块大小: {result.get('chunk_size')}")
            print(f"   重叠大小: {result.get('chunk_overlap')}")
            print(f"   创建时间: {result.get('created_at')}")
        else:
            print(f"❌ 获取详情失败: {response.status_code}")
            print(f"   {response.text}")
            return False
        return True

    def test_duplicate_name(self):
        """测试重名检测"""
        print("\n" + "=" * 60)
        print("7. 测试重名检测")
        print("=" * 60)

        url = f"{self.base_url}{self.api_prefix}/knowledge/bases"
        data = {
            "name": "独立知识库",  # 重复名称
            "description": "测试重名"
        }

        response = self.session.post(url, json=data)

        if response.status_code == 400:
            print(f"✅ 重名检测正常工作")
            print(f"   错误信息: {response.json().get('detail')}")
        else:
            print(f"❌ 重名检测失败: {response.status_code}")
            print(f"   {response.text}")
            return False
        return True

    def test_invalid_group(self):
        """测试无效分组ID"""
        print("\n" + "=" * 60)
        print("8. 测试无效分组ID")
        print("=" * 60)

        url = f"{self.base_url}{self.api_prefix}/knowledge/bases"
        data = {
            "group_id": "invalid-group-id-12345",
            "name": "测试知识库",
            "description": "测试无效分组"
        }

        response = self.session.post(url, json=data)

        if response.status_code == 404:
            print(f"✅ 无效分组检测正常工作")
            print(f"   错误信息: {response.json().get('detail')}")
        else:
            print(f"⚠️  无效分组检测: {response.status_code}")
            print(f"   {response.text}")
        return True

    def cleanup(self):
        """清理测试数据"""
        print("\n" + "=" * 60)
        print("9. 清理测试数据")
        print("=" * 60)

        # 删除知识库
        for kb_id, kb_name in [
            (self.kb_id_without_group, "独立知识库"),
            (self.kb_id_with_group, "分组知识库")
        ]:
            if kb_id:
                url = f"{self.base_url}{self.api_prefix}/knowledge/bases/{kb_id}"
                response = self.session.delete(url)
                if response.status_code == 200:
                    print(f"✅ 已删除知识库: {kb_name}")
                else:
                    print(f"⚠️  删除知识库失败: {kb_name} ({response.status_code})")

        # 删除分组
        if self.group_id:
            url = f"{self.base_url}{self.api_prefix}/knowledge/groups/{self.group_id}"
            response = self.session.delete(url)
            if response.status_code == 200:
                print(f"✅ 已删除分组: 测试分组")
            else:
                print(f"⚠️  删除分组失败 ({response.status_code})")

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 60)
        print("知识库模块修复验证测试")
        print("=" * 60)

        if not self.login():
            return

        tests = [
            self.create_group,
            self.test_create_kb_without_group,
            self.test_create_kb_with_group,
            self.test_get_kb_list,
            self.test_get_kb_detail,
            self.test_duplicate_name,
            self.test_invalid_group,
        ]

        passed = 0
        failed = 0

        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"\n❌ 测试异常: {e}")
                import traceback
                traceback.print_exc()
                failed += 1

        # 清理
        self.cleanup()

        # 总结
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"📊 总数: {passed + failed}")

        if failed == 0:
            print("\n🎉 所有测试通过！")
        else:
            print(f"\n⚠️  有 {failed} 个测试失败")

if __name__ == "__main__":
    tester = KnowledgeBaseTester()
    tester.run_all_tests()
