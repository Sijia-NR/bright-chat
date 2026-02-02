#!/usr/bin/env python3
"""
知识库模块完整功能测试脚本

测试范围:
1. 知识库 CRUD 操作
2. 文档上传功能
3. 文档切片查看
4. API 错误处理

运行方式:
    python test_knowledge_complete.py
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional

# 配置
API_BASE = "http://localhost:8080/api/v1"
USERNAME = "admin"
PASSWORD = "pwd123"

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg: str):
    """打印错误消息"""
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg: str):
    """打印信息"""
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_warning(msg: str):
    """打印警告"""
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_section(msg: str):
    """打印章节标题"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

class KnowledgeBaseTester:
    """知识库测试器"""

    def __init__(self):
        self.token: Optional[str] = None
        self.test_kb_id: Optional[str] = None
        self.test_doc_id: Optional[str] = None
        self.session = requests.Session()

    def login(self) -> bool:
        """登录并获取 token"""
        print_section("测试 1: 用户登录")

        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json={"username": USERNAME, "password": PASSWORD}
            )
            response.raise_for_status()
            data = response.json()

            if "token" in data:
                self.token = data["token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                print_success("登录成功")
                print_info(f"Token: {self.token[:50]}...")
                return True
            else:
                print_error("登录响应中没有 token")
                return False

        except Exception as e:
            print_error(f"登录失败: {e}")
            return False

    def test_get_knowledge_bases(self) -> bool:
        """测试获取知识库列表"""
        print_section("测试 2: 获取知识库列表")

        try:
            response = self.session.get(f"{API_BASE}/knowledge/bases")
            response.raise_for_status()
            data = response.json()

            print_success(f"获取成功，共 {len(data)} 个知识库")
            for kb in data[:5]:  # 只显示前 5 个
                print_info(f"  - {kb['name']}: {kb.get('description', '无描述')}")

            return True

        except Exception as e:
            print_error(f"获取知识库列表失败: {e}")
            return False

    def test_create_knowledge_base(self) -> bool:
        """测试创建知识库"""
        print_section("测试 3: 创建知识库")

        kb_data = {
            "name": "自动化测试知识库",
            "description": "用于自动化测试的知识库"
        }

        try:
            response = self.session.post(
                f"{API_BASE}/knowledge/bases",
                json=kb_data
            )
            response.raise_for_status()
            data = response.json()

            self.test_kb_id = data.get("id")
            print_success(f"创建成功: {data['name']}")
            print_info(f"知识库 ID: {self.test_kb_id}")
            print_info(f"描述: {data.get('description', '无')}")

            return True

        except Exception as e:
            print_error(f"创建知识库失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print_error(f"响应内容: {e.response.text}")
            return False

    def test_get_knowledge_base_detail(self) -> bool:
        """测试获取知识库详情"""
        print_section("测试 4: 获取知识库详情")

        if not self.test_kb_id:
            print_warning("没有可用的测试知识库 ID")
            return False

        try:
            response = self.session.get(f"{API_BASE}/knowledge/bases/{self.test_kb_id}")
            response.raise_for_status()
            data = response.json()

            print_success("获取知识库详情成功")
            print_info(f"名称: {data['name']}")
            print_info(f"描述: {data.get('description', '无')}")
            print_info(f"创建时间: {data.get('created_at', '未知')}")

            return True

        except Exception as e:
            print_error(f"获取知识库详情失败: {e}")
            return False

    def test_upload_document(self) -> bool:
        """测试上传文档"""
        print_section("测试 5: 上传文档")

        if not self.test_kb_id:
            print_warning("没有可用的测试知识库 ID")
            return False

        # 创建测试文件
        test_file_path = "/tmp/test_knowledge.txt"
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("这是一个测试文档。\n" * 100)

        try:
            with open(test_file_path, "rb") as f:
                files = {"file": ("test.txt", f, "text/plain")}
                response = self.session.post(
                    f"{API_BASE}/knowledge/bases/{self.test_kb_id}/documents",
                    files=files
                )

            response.raise_for_status()
            data = response.json()

            self.test_doc_id = data.get("id")
            print_success("文档上传成功")
            print_info(f"文档 ID: {self.test_doc_id}")
            print_info(f"文件名: {data.get('filename', '未知')}")
            print_info(f"状态: {data.get('upload_status', '未知')}")

            # 等待文档处理
            print_info("等待文档处理...")
            time.sleep(3)

            return True

        except Exception as e:
            print_error(f"文档上传失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print_error(f"响应内容: {e.response.text}")
            return False

    def test_get_documents(self) -> bool:
        """测试获取文档列表"""
        print_section("测试 6: 获取文档列表")

        if not self.test_kb_id:
            print_warning("没有可用的测试知识库 ID")
            return False

        try:
            response = self.session.get(
                f"{API_BASE}/knowledge/bases/{self.test_kb_id}/documents"
            )
            response.raise_for_status()
            data = response.json()

            print_success(f"获取文档列表成功，共 {len(data)} 个文档")
            for doc in data:
                print_info(f"  - {doc['filename']}: {doc.get('chunk_count', 0)} 个切片")

            return True

        except Exception as e:
            print_error(f"获取文档列表失败: {e}")
            return False

    def test_get_document_chunks(self) -> bool:
        """测试获取文档切片"""
        print_section("测试 7: 获取文档切片")

        if not self.test_doc_id:
            print_warning("没有可用的测试文档 ID")
            return False

        try:
            response = self.session.get(
                f"{API_BASE}/knowledge/bases/{self.test_kb_id}/documents/{self.test_doc_id}/chunks"
            )
            response.raise_for_status()
            data = response.json()

            chunks = data.get("chunks", [])
            print_success(f"获取文档切片成功，共 {len(chunks)} 个切片")

            # 显示前 3 个切片
            for i, chunk in enumerate(chunks[:3]):
                print_info(f"\n切片 #{chunk.get('chunk_index', i)}:")
                content = chunk.get("content", "")[:100]
                print(f"  {content}...")

            return True

        except Exception as e:
            print_error(f"获取文档切片失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print_error(f"响应内容: {e.response.text}")
            return False

    def test_delete_document(self) -> bool:
        """测试删除文档"""
        print_section("测试 8: 删除文档")

        if not self.test_doc_id:
            print_warning("没有可用的测试文档 ID")
            return False

        try:
            response = self.session.delete(
                f"{API_BASE}/knowledge/bases/{self.test_kb_id}/documents/{self.test_doc_id}"
            )
            response.raise_for_status()

            print_success("文档删除成功")
            return True

        except Exception as e:
            print_error(f"删除文档失败: {e}")
            return False

    def test_delete_knowledge_base(self) -> bool:
        """测试删除知识库"""
        print_section("测试 9: 删除知识库")

        if not self.test_kb_id:
            print_warning("没有可用的测试知识库 ID")
            return False

        try:
            response = self.session.delete(
                f"{API_BASE}/knowledge/bases/{self.test_kb_id}"
            )
            response.raise_for_status()

            print_success("知识库删除成功")
            return True

        except Exception as e:
            print_error(f"删除知识库失败: {e}")
            return False

    def test_search(self) -> bool:
        """测试知识库搜索"""
        print_section("测试 10: 知识库搜索")

        try:
            response = self.session.get(
                f"{API_BASE}/knowledge/search",
                params={
                    "query": "测试",
                    "top_k": 5
                }
            )
            response.raise_for_status()
            data = response.json()

            print_success("搜索功能正常")
            print_info(f"找到 {len(data)} 个结果")

            return True

        except Exception as e:
            print_error(f"搜索失败: {e}")
            return False

    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print(f"\n{Colors.BOLD}开始知识库模块完整功能测试{Colors.END}\n")

        tests = [
            ("用户登录", self.login),
            ("获取知识库列表", self.test_get_knowledge_bases),
            ("创建知识库", self.test_create_knowledge_base),
            ("获取知识库详情", self.test_get_knowledge_base_detail),
            ("上传文档", self.test_upload_document),
            ("获取文档列表", self.test_get_documents),
            ("获取文档切片", self.test_get_document_chunks),
            ("删除文档", self.test_delete_document),
            ("删除知识库", self.test_delete_knowledge_base),
            ("知识库搜索", self.test_search),
        ]

        results = []

        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))

                if not result:
                    print_warning(f"测试 '{test_name}' 失败，继续执行其他测试")

            except Exception as e:
                print_error(f"测试 '{test_name}' 发生异常: {e}")
                results.append((test_name, False))

        # 打印测试结果汇总
        print_section("测试结果汇总")

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = f"{Colors.GREEN}通过{Colors.END}" if result else f"{Colors.RED}失败{Colors.END}"
            print(f"{test_name}: {status}")

        print(f"\n{Colors.BOLD}总计: {passed}/{total} 通过{Colors.END}\n")

        return passed == total

def main():
    """主函数"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}知识库模块完整功能测试{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

    tester = KnowledgeBaseTester()
    success = tester.run_all_tests()

    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过！{Colors.END}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  部分测试失败{Colors.END}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
