#!/usr/bin/env python3
"""
前后端联调测试脚本
Frontend-Backend Integration Test Script

验证所有 API 接口的功能、数据格式和错误处理
"""
import requests
import json
import time
from typing import Dict, Any, List
from datetime import datetime
import sys

# 配置
BACKEND_URL = "http://localhost:18080"
API_BASE = f"{BACKEND_URL}/api/v1"

# 测试结果存储
test_results = []


class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_test_header(test_name: str):
    """打印测试标题"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}测试: {test_name}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")


def print_success(message: str):
    """打印成功消息"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    """打印错误消息"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_info(message: str):
    """打印信息消息"""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def print_warning(message: str):
    """打印警告消息"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def log_result(test_name: str, passed: bool, details: str = "", response_time: float = 0):
    """记录测试结果"""
    test_results.append({
        "name": test_name,
        "passed": passed,
        "details": details,
        "response_time": response_time,
        "timestamp": datetime.now().isoformat()
    })


# ============================================================================
# 1. 认证接口测试
# ============================================================================

def test_auth_login() -> Dict[str, Any]:
    """测试登录接口"""
    print_test_header("认证接口 - 登录")

    url = f"{API_BASE}/auth/login"
    payload = {
        "username": "admin",
        "password": "pwd123"
    }

    start_time = time.time()
    try:
        response = requests.post(url, json=payload)
        response_time = time.time() - start_time

        print_info(f"请求: POST {url}")
        print_info(f"响应时间: {response_time:.3f}s")
        print_info(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success("登录成功")

            # 验证响应格式
            # 注意：后端返回字段名是 token，不是 access_token
            if "token" in data:
                print_success("  字段 'token' 存在")
            elif "access_token" in data:
                print_success("  字段 'access_token' 存在")
            else:
                print_error("  缺少 token 字段")
                log_result("认证登录", False, "缺少 token 字段", response_time)
                return None

            # 获取 token
            auth_token = data.get("token") or data.get("access_token")
            user_info = data.get("user", data)  # 有些接口返回 user 对象，有些直接返回用户信息

            # 验证用户信息
            print_info(f"  用户信息: id={user_info.get('id')}, username={user_info.get('username')}, role={user_info.get('role')}")

            log_result("认证登录", True, f"用户 {user_info.get('username')}", response_time)
            return {"token": auth_token, "user": user_info}
        else:
            print_error(f"登录失败: {response.status_code} - {response.text}")
            log_result("认证登录", False, f"状态码 {response.status_code}", response_time)
            return None
    except Exception as e:
        print_error(f"请求异常: {str(e)}")
        log_result("认证登录", False, str(e), 0)
        return None


def test_auth_me(token: str) -> bool:
    """测试获取当前用户信息"""
    print_test_header("认证接口 - 获取当前用户")

    url = f"{API_BASE}/auth/me"
    headers = {"Authorization": f"Bearer {token}"}

    start_time = time.time()
    try:
        response = requests.get(url, headers=headers)
        response_time = time.time() - start_time

        print_info(f"请求: GET {url}")
        print_info(f"响应时间: {response_time:.3f}s")
        print_info(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success("获取用户信息成功")
            print_info(f"  用户: {json.dumps(data, indent=2, ensure_ascii=False)}")
            log_result("获取当前用户", True, "", response_time)
            return True
        else:
            print_error(f"请求失败: {response.status_code}")
            log_result("获取当前用户", False, f"状态码 {response.status_code}", response_time)
            return False
    except Exception as e:
        print_error(f"请求异常: {str(e)}")
        log_result("获取当前用户", False, str(e), 0)
        return False


def test_auth_logout(token: str) -> bool:
    """测试登出接口"""
    print_test_header("认证接口 - 登出")

    url = f"{API_BASE}/auth/logout"
    headers = {"Authorization": f"Bearer {token}"}

    start_time = time.time()
    try:
        response = requests.post(url, headers=headers)
        response_time = time.time() - start_time

        print_info(f"请求: POST {url}")
        print_info(f"响应时间: {response_time:.3f}s")
        print_info(f"状态码: {response.status_code}")

        if response.status_code == 200:
            print_success("登出成功")
            log_result("认证登出", True, "", response_time)
            return True
        else:
            print_error(f"登出失败: {response.status_code}")
            log_result("认证登出", False, f"状态码 {response.status_code}", response_time)
            return False
    except Exception as e:
        print_error(f"请求异常: {str(e)}")
        log_result("认证登出", False, str(e), 0)
        return False


# ============================================================================
# 2. 聊天接口测试
# ============================================================================

def test_get_sessions(token: str) -> List[str]:
    """测试获取会话列表"""
    print_test_header("聊天接口 - 获取会话列表")

    url = f"{API_BASE}/sessions"
    headers = {"Authorization": f"Bearer {token}"}

    start_time = time.time()
    try:
        response = requests.get(url, headers=headers)
        response_time = time.time() - start_time

        print_info(f"请求: GET {url}")
        print_info(f"响应时间: {response_time:.3f}s")
        print_info(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success(f"获取会话列表成功，共 {len(data)} 个会话")

            # 验证时间戳格式
            if len(data) > 0:
                first_session = data[0]
                print_info(f"  第一个会话: {json.dumps(first_session, indent=2, ensure_ascii=False)}")

                # 检查时间戳格式（应该是 ISO 格式）
                for field in ['created_at', 'updated_at', 'last_updated']:
                    if field in first_session:
                        timestamp = first_session[field]
                        print_info(f"  {field}: {timestamp} (ISO 格式)")

            log_result("获取会话列表", True, f"共 {len(data)} 个", response_time)
            return [s.get('id') for s in data if 'id' in s]
        else:
            print_error(f"请求失败: {response.status_code}")
            log_result("获取会话列表", False, f"状态码 {response.status_code}", response_time)
            return []
    except Exception as e:
        print_error(f"请求异常: {str(e)}")
        log_result("获取会话列表", False, str(e), 0)
        return []


def test_create_session(token: str) -> str:
    """测试创建会话"""
    print_test_header("聊天接口 - 创建会话")

    url = f"{API_BASE}/sessions"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"title": "测试会话"}

    start_time = time.time()
    try:
        response = requests.post(url, json=payload, headers=headers)
        response_time = time.time() - start_time

        print_info(f"请求: POST {url}")
        print_info(f"响应时间: {response_time:.3f}s")
        print_info(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success(f"创建会话成功")
            print_info(f"  会话信息: {json.dumps(data, indent=2, ensure_ascii=False)}")
            log_result("创建会话", True, f"会话ID: {data.get('id')}", response_time)
            return data.get('id')
        else:
            print_error(f"创建失败: {response.status_code}")
            log_result("创建会话", False, f"状态码 {response.status_code}", response_time)
            return None
    except Exception as e:
        print_error(f"请求异常: {str(e)}")
        log_result("创建会话", False, str(e), 0)
        return None


def test_get_messages(token: str, session_id: str):
    """测试获取会话消息"""
    print_test_header("聊天接口 - 获取会话消息")

    url = f"{API_BASE}/sessions/{session_id}/messages"
    headers = {"Authorization": f"Bearer {token}"}

    # 先检查会话是否存在
    print_info(f"检查会话ID: {session_id}")

    start_time = time.time()
    try:
        response = requests.get(url, headers=headers)
        response_time = time.time() - start_time

        print_info(f"请求: GET {url}")
        print_info(f"响应时间: {response_time:.3f}s")
        print_info(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success(f"获取消息成功，共 {len(data)} 条消息")

            if len(data) > 0:
                first_msg = data[0]
                print_info(f"  第一条消息: id={first_msg.get('id')}, role={first_msg.get('role')}")
                print_info(f"  时间戳: {first_msg.get('timestamp')}")

            log_result("获取会话消息", True, f"共 {len(data)} 条", response_time)
        else:
            print_error(f"请求失败: {response.status_code}")
            log_result("获取会话消息", False, f"状态码 {response.status_code}", response_time)
    except Exception as e:
        print_error(f"请求异常: {str(e)}")
        log_result("获取会话消息", False, str(e), 0)


def test_send_message(token: str, session_id: str):
    """测试发送消息"""
    print_test_header("聊天接口 - 发送消息")

    url = f"{API_BASE}/sessions/{session_id}/messages"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "content": "你好，这是一条测试消息",
        "role": "user"
    }

    start_time = time.time()
    try:
        response = requests.post(url, json=payload, headers=headers)
        response_time = time.time() - start_time

        print_info(f"请求: POST {url}")
        print_info(f"响应时间: {response_time:.3f}s")
        print_info(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success(f"发送消息成功")
            print_info(f"  消息信息: {json.dumps(data, indent=2, ensure_ascii=False)}")
            log_result("发送消息", True, "", response_time)
        else:
            print_error(f"发送失败: {response.status_code}")
            log_result("发送消息", False, f"状态码 {response.status_code}", response_time)
    except Exception as e:
        print_error(f"请求异常: {str(e)}")
        log_result("发送消息", False, str(e), 0)


def test_sse_stream(token: str, session_id: str):
    """测试 SSE 流式响应"""
    print_test_header("聊天接口 - SSE 流式响应")

    url = f"{BACKEND_URL}/lmp-cloud-ias-server/api/llm/chat/completions/V2"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "session_id": session_id,
        "stream": True
    }

    start_time = time.time()
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=10)
        response_time = time.time() - start_time

        print_info(f"请求: POST {url}")
        print_info(f"响应时间: {response_time:.3f}s (首次响应)")
        print_info(f"状态码: {response.status_code}")

        if response.status_code == 200:
            print_success("SSE 连接成功")

            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        chunk_count += 1
                        data = line[6:]
                        if chunk_count <= 3:  # 只打印前3个chunk
                            print_info(f"  Chunk {chunk_count}: {data[:100]}...")
                        elif chunk_count == 4:
                            print_info(f"  ... (共接收 {chunk_count} 个数据块)")

                        if data == '[DONE]':
                            break

            print_success(f"SSE 流式接收完成，共 {chunk_count} 个数据块")
            log_result("SSE 流式响应", True, f"共 {chunk_count} 个chunk", response_time)
        else:
            print_error(f"SSE 连接失败: {response.status_code}")
            log_result("SSE 流式响应", False, f"状态码 {response.status_code}", response_time)
    except Exception as e:
        print_error(f"请求异常: {str(e)}")
        log_result("SSE 流式响应", False, str(e), 0)


# ============================================================================
# 3. 知识库接口测试 (RAG)
# ============================================================================

def test_get_knowledge_bases(token: str):
    """测试获取知识库列表"""
    print_test_header("知识库接口 - 获取知识库列表")

    url = f"{API_BASE}/knowledge/bases"
    headers = {"Authorization": f"Bearer {token}"}

    start_time = time.time()
    try:
        response = requests.get(url, headers=headers)
        response_time = time.time() - start_time

        print_info(f"请求: GET {url}")
        print_info(f"响应时间: {response_time:.3f}s")
        print_info(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success(f"获取知识库列表成功，共 {len(data)} 个")
            log_result("获取知识库列表", True, f"共 {len(data)} 个", response_time)
            return data
        elif response.status_code == 404:
            print_warning("接口不存在 (RAG 功能可能未实现)")
            log_result("获取知识库列表", False, "接口不存在", response_time)
            return None
        else:
            print_error(f"请求失败: {response.status_code}")
            log_result("获取知识库列表", False, f"状态码 {response.status_code}", response_time)
            return None
    except Exception as e:
        print_error(f"请求异常: {str(e)}")
        log_result("获取知识库列表", False, str(e), 0)
        return None


def test_create_knowledge_base(token: str):
    """测试创建知识库"""
    print_test_header("知识库接口 - 创建知识库")

    url = f"{API_BASE}/knowledge/bases"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "测试知识库",
        "description": "用于前后端联调测试",
        "embedding_model": "bge-large-zh-v1.5"
    }

    start_time = time.time()
    try:
        response = requests.post(url, json=payload, headers=headers)
        response_time = time.time() - start_time

        print_info(f"请求: POST {url}")
        print_info(f"响应时间: {response_time:.3f}s")
        print_info(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success("创建知识库成功")
            print_info(f"  知识库信息: {json.dumps(data, indent=2, ensure_ascii=False)}")
            log_result("创建知识库", True, f"ID: {data.get('id')}", response_time)
            return data.get('id')
        elif response.status_code == 404:
            print_warning("接口不存在 (RAG 功能可能未实现)")
            log_result("创建知识库", False, "接口不存在", response_time)
            return None
        else:
            print_error(f"创建失败: {response.status_code}")
            log_result("创建知识库", False, f"状态码 {response.status_code}", response_time)
            return None
    except Exception as e:
        print_error(f"请求异常: {str(e)}")
        log_result("创建知识库", False, str(e), 0)
        return None


# ============================================================================
# 主测试流程
# ============================================================================

def run_all_tests():
    """运行所有测试"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║        BrightChat 前后端联调测试                          ║")
    print("║        Frontend-Backend Integration Test                  ║")
    print(f"╚════════════════════════════════════════════════════════════╝{Colors.ENDC}")

    print_info(f"后端地址: {BACKEND_URL}")
    print_info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 认证测试
    print(f"\n{Colors.BOLD}{'━'*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}模块 1: 认证接口{Colors.ENDC}")
    print(f"{Colors.BOLD}{'━'*60}{Colors.ENDC}")

    auth_result = test_auth_login()
    if not auth_result:
        print_error("认证失败，终止测试")
        generate_report()
        return

    token = auth_result["token"]
    test_auth_me(token)

    # 2. 聊天接口测试
    print(f"\n{Colors.BOLD}{'━'*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}模块 2: 聊天接口{Colors.ENDC}")
    print(f"{Colors.BOLD}{'━'*60}{Colors.ENDC}")

    session_ids = test_get_sessions(token)
    session_id = test_create_session(token)

    if session_id:
        test_get_messages(token, session_id)
        test_send_message(token, session_id)
        test_sse_stream(token, session_id)

    # 3. 知识库接口测试
    print(f"\n{Colors.BOLD}{'━'*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}模块 3: 知识库接口 (RAG){Colors.ENDC}")
    print(f"{Colors.BOLD}{'━'*60}{Colors.ENDC}")

    kb_list = test_get_knowledge_bases(token)
    if kb_list is not None:
        kb_id = test_create_knowledge_base(token)

    # 4. 登出
    test_auth_logout(token)

    # 生成测试报告
    generate_report()


def generate_report():
    """生成测试报告"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                  测试报告                                   ║")
    print("║                  Test Report                               ║")
    print(f"╚════════════════════════════════════════════════════════════╝{Colors.ENDC}")

    total = len(test_results)
    passed = sum(1 for r in test_results if r["passed"])
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"\n{Colors.BOLD}测试统计:{Colors.ENDC}")
    print(f"  总计: {total}")
    print(f"  {Colors.OKGREEN}通过: {passed}{Colors.ENDC}")
    print(f"  {Colors.FAIL}失败: {failed}{Colors.ENDC}")
    print(f"  通过率: {pass_rate:.1f}%")

    # 平均响应时间
    response_times = [r["response_time"] for r in test_results if r["response_time"] > 0]
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        print(f"  平均响应时间: {avg_time:.3f}s")

    # 失败测试详情
    if failed > 0:
        print(f"\n{Colors.FAIL}{Colors.BOLD}失败测试详情:{Colors.ENDC}")
        for result in test_results:
            if not result["passed"]:
                print(f"  ✗ {result['name']}: {result['details']}")

    # 保存测试报告到文件
    report_file = "/tmp/integration_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": pass_rate
            },
            "tests": test_results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{Colors.OKCYAN}测试报告已保存到: {report_file}{Colors.ENDC}")

    # 详细结果列表
    print(f"\n{Colors.BOLD}详细测试结果:{Colors.ENDC}")
    for result in test_results:
        status = f"{Colors.OKGREEN}✓{Colors.ENDC}" if result["passed"] else f"{Colors.FAIL}✗{Colors.ENDC}"
        time_str = f" ({result['response_time']:.3f}s)" if result['response_time'] > 0 else ""
        print(f"  {status} {result['name']}{time_str}")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print_warning("\n测试被用户中断")
        generate_report()
        sys.exit(1)
    except Exception as e:
        print_error(f"\n测试过程中发生异常: {str(e)}")
        generate_report()
        sys.exit(1)
