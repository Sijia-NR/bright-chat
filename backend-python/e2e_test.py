#!/usr/bin/env python3
"""
End-to-End Frontend-Backend Integration Test
验证前端页面与后端的完整集成
"""

import requests
import json
import time
import subprocess
import os
import signal

class FrontendBackendTester:
    def __init__(self):
        self.base_url = "http://localhost:18080"
        self.frontend_url = "http://localhost:3000"
        self.processes = []

    def start_services(self):
        """启动前后端服务"""
        print("🚀 Starting services...")

        # 检查后端是否已运行
        try:
            requests.get(f"{self.base_url}/health", timeout=5)
            print("✅ Backend already running")
        except:
            print("❌ Backend not running, please start it first")
            return False

        # 检查前端是否已运行
        try:
            requests.get(self.frontend_url, timeout=5)
            print("✅ Frontend already running")
        except:
            print("❌ Frontend not running, please start it first")
            return False

        return True

    def test_backend_apis(self):
        """测试后端所有API接口"""
        print("\n🔧 Testing Backend APIs...")

        results = []

        # 1. 健康检查
        try:
            resp = requests.get(f"{self.base_url}/health")
            results.append(("Health Check", resp.status_code == 200))
        except:
            results.append(("Health Check", False))

        # 2. 登录测试
        try:
            resp = requests.post(f"{self.base_url}/api/v1/auth/login",
                              json={"username": "admin", "password": "pwd123"})
            results.append(("Login", resp.status_code == 200))
        except:
            results.append(("Login", False))

        # 3. 获取用户列表
        try:
            token = self.get_admin_token()
            resp = requests.get(f"{self.base_url}/api/v1/admin/users",
                              headers={"Authorization": f"Bearer {token}"})
            results.append(("List Users", resp.status_code == 200))
        except:
            results.append(("List Users", False))

        # 4. 创建用户
        try:
            token = self.get_admin_token()
            username = f"test_{int(time.time())}"
            resp = requests.post(f"{self.base_url}/api/v1/admin/users",
                              headers={"Authorization": f"Bearer {token}"},
                              json={"username": username, "password": "test123", "role": "user"})
            results.append(("Create User", resp.status_code == 200))
        except:
            results.append(("Create User", False))

        # 5. 获取会话列表
        try:
            token = self.get_admin_token()
            user_id = self.get_admin_id(token)
            resp = requests.get(f"{self.base_url}/api/v1/sessions?user_id={user_id}",
                              headers={"Authorization": f"Bearer {token}"})
            results.append(("List Sessions", resp.status_code == 200))
        except:
            results.append(("List Sessions", False))

        # 6. IAS代理
        try:
            token = self.get_admin_token()
            resp = requests.post(f"{self.base_url}/api/v1/lmp-cloud-ias-server/api/llm/chat/completions/V2",
                              headers={"Authorization": f"Bearer {token}"},
                              json={"model": "test", "messages": [{"role": "user", "content": "test"}], "stream": False})
            results.append(("IAS Proxy", resp.status_code == 200))
        except:
            results.append(("IAS Proxy", False))

        return results

    def get_admin_token(self):
        """获取管理员token"""
        resp = requests.post(f"{self.base_url}/api/v1/auth/login",
                          json={"username": "admin", "password": "pwd123"})
        if resp.status_code == 200:
            return resp.json()["token"]
        return None

    def get_admin_id(self, token):
        """获取管理员ID"""
        resp = requests.post(f"{self.base_url}/api/v1/auth/login",
                          json={"username": "admin", "password": "pwd123"})
        if resp.status_code == 200:
            return resp.json()["id"]
        return None

    def test_frontend_config(self):
        """测试前端配置"""
        print("\n🎨 Testing Frontend Configuration...")

        # 读取前端配置
        try:
            with open("/Users/sijia/Documents/workspace/BProject/Bright-Chat/frontend/config/index.ts", "r") as f:
                config_content = f.read()

            checks = []
            # 检查USE_MOCK设置
            checks.append(("USE_MOCK = false", "USE_MOCK: false" in config_content))
            # 检查API地址
            checks.append(("API_URL correct", "localhost:18080" in config_content))
            # 检查IAS URL
            checks.append(("IAS URL correct", "/lmp-cloud-ias-server" in config_content))

            return checks

        except Exception as e:
            print(f"❌ Error reading frontend config: {e}")
            return [("Config Read Error", False)]

    def test_frontend_services(self):
        """测试前端服务代码"""
        print("\n💻 Testing Frontend Service Code...")

        checks = []

        # 检查authService
        try:
            with open("/Users/sijia/Documents/workspace/BProject/Bright-Chat/frontend/services/authService.ts", "r") as f:
                auth_content = f.read()
            checks.append(("authService updated", "API_BASE_URL" in auth_content))
        except:
            checks.append(("authService", False))

        # 检查adminService
        try:
            with open("/Users/sijia/Documents/workspace/BProject/Bright-Chat/frontend/services/adminService.ts", "r") as f:
                admin_content = f.read()
            checks.append(("adminService updated", "createUser" in admin_content))
        except:
            checks.append(("adminService", False))

        # 检查sessionService
        try:
            with open("/Users/sijia/Documents/workspace/BProject/Bright-Chat/frontend/services/sessionService.ts", "r") as f:
                session_content = f.read()
            checks.append(("sessionService updated", "user_id" in session_content))
        except:
            checks.append(("sessionService", False))

        return checks

    def test_cors_headers(self):
        """测试CORS配置"""
        print("\n🌐 Testing CORS Configuration...")

        try:
            # 测试预检请求
            resp = requests.options(f"{self.base_url}/api/v1/auth/login",
                                 headers={"Origin": "http://localhost:3000"})

            # 检查CORS头
            cors_check = (
                resp.status_code == 200 and
                "Access-Control-Allow-Origin" in resp.headers
            )

            return [("CORS Headers", cors_check)]

        except Exception as e:
            return [("CORS Test", False)]

    def generate_report(self, api_results, config_results, service_results, cors_results):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 FRONTEND-BACKEND INTEGRATION TEST REPORT")
        print("="*60)

        # API测试结果
        print("\n🔧 Backend API Tests:")
        api_passed = 0
        for test, passed in api_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test:20} {status}")
            if passed:
                api_passed += 1

        # 前端配置结果
        print("\n🎨 Frontend Configuration Tests:")
        config_passed = 0
        for test, passed in config_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test:20} {status}")
            if passed:
                config_passed += 1

        # 前端服务结果
        print("\n💻 Frontend Service Tests:")
        service_passed = 0
        for test, passed in service_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test:20} {status}")
            if passed:
                service_passed += 1

        # CORS结果
        print("\n🌐 CORS Configuration Tests:")
        cors_passed = 0
        for test, passed in cors_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test:20} {status}")
            if passed:
                cors_passed += 1

        # 总结
        total_tests = len(api_results) + len(config_results) + len(service_results) + len(cors_results)
        total_passed = api_passed + config_passed + service_passed + cors_passed

        print(f"\n{'='*60}")
        print(f"🎯 TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests:  {total_tests}")
        print(f"Passed:       {total_passed}")
        print(f"Failed:       {total_tests - total_passed}")
        print(f"Success Rate:  {total_passed/total_tests*100:.1f}%")

        if api_passed == len(api_results) and config_passed == len(config_results) and \
           service_passed == len(service_results) and cors_passed == len(cors_results):
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"✅ Frontend-Backend integration is ready!")
            print(f"🚀 You can now use the application at {self.frontend_url}")
        else:
            print(f"\n⚠️  Some tests failed")
            print(f"🔧 Please check the failed tests above")

        print(f"\n{'='*60}")
        print(f"📍 Service Information")
        print(f"{'='*60}")
        print(f"Frontend: {self.frontend_url}")
        print(f"Backend:  {self.base_url}")
        print(f"API Docs: {self.base_url}/docs")
        print(f"Health:   {self.base_url}/health")

def main():
    tester = FrontendBackendTester()

    if not tester.start_services():
        print("❌ Services not ready")
        return

    # 运行所有测试
    api_results = tester.test_backend_apis()
    config_results = tester.test_frontend_config()
    service_results = tester.test_frontend_services()
    cors_results = tester.test_cors_headers()

    # 生成报告
    tester.generate_report(api_results, config_results, service_results, cors_results)

if __name__ == "__main__":
    main()