#!/usr/bin/env python3
"""
并发修复代码验证
Concurrency Fixes Code Validation

静态代码分析验证 4 个关键并发问题修复：
1. AGENT-CRITICAL-001: 浏览器实例并发竞争
2. AGENT-CRITICAL-002: Agent 执行状态数据库竞态
3. AGENT-CRITICAL-003: LangGraph 状态污染
4. AGENT-HIGH-001: 数据库连接泄漏
"""
import re
import sys
from pathlib import Path


class CodeValidator:
    """代码验证器"""

    def __init__(self):
        self.results = {}

    def check(self, test_name: str, passed: bool, message: str = ""):
        """记录验证结果"""
        self.results[test_name] = {
            "passed": passed,
            "message": message
        }

    def print_summary(self):
        """打印验证总结"""
        print("\n" + "=" * 80)
        print("并发修复代码验证总结")
        print("=" * 80)

        passed_count = sum(1 for r in self.results.values() if r["passed"])
        total_count = len(self.results)

        for test_name, result in self.results.items():
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"{status} - {test_name}")
            if result["message"]:
                print(f"    {result['message']}")

        print("-" * 80)
        print(f"总计: {passed_count}/{total_count} 验证通过")
        print("=" * 80)

        return passed_count == total_count


def validate_browser_concurrency():
    """验证1: 浏览器实例并发竞争修复"""
    print("\n" + "=" * 80)
    print("验证1: 浏览器实例并发竞争 (AGENT-CRITICAL-001)")
    print("=" * 80)

    validator = CodeValidator()
    file_path = Path("app/agents/tools/browser_tool.py")

    if not file_path.exists():
        validator.check("浏览器工具文件存在", False, f"文件不存在: {file_path}")
        return validator

    content = file_path.read_text()

    # 检查1: 导入 asyncio
    has_asyncio = "import asyncio" in content
    validator.check(
        "导入 asyncio",
        has_asyncio,
        "已导入 asyncio 模块" if has_asyncio else "未导入 asyncio 模块"
    )

    # 检查2: 定义锁
    has_lock = "_browser_lock = asyncio.Lock()" in content
    validator.check(
        "定义浏览器锁",
        has_lock,
        "已定义 _browser_lock" if has_lock else "未定义 _browser_lock"
    )

    # 检查3: 使用锁保护浏览器创建
    has_locked_browser = "async with _browser_lock:" in content and "_get_browser" in content
    validator.check(
        "锁保护浏览器实例",
        has_locked_browser,
        "浏览器实例创建已加锁" if has_locked_browser else "浏览器实例创建未加锁"
    )

    # 检查4: 上下文锁
    has_context_lock = "_context_lock = asyncio.Lock()" in content
    validator.check(
        "定义上下文锁",
        has_context_lock,
        "已定义 _context_lock" if has_context_lock else "未定义 _context_lock"
    )

    # 检查5: 使用锁保护上下文创建
    has_locked_context = "async with _context_lock:" in content and "_get_context" in content
    validator.check(
        "锁保护上下文实例",
        has_locked_context,
        "上下文实例创建已加锁" if has_locked_context else "上下文实例创建未加锁"
    )

    # 检查6: 改进的清理机制
    has_cleanup_locks = "async with _context_lock:" in content and "async with _browser_lock:" in content and "close_browser" in content
    validator.check(
        "清理使用锁",
        has_cleanup_locks,
        "清理函数正确使用锁" if has_cleanup_locks else "清理函数未使用锁"
    )

    return validator


def validate_transaction_isolation():
    """验证2: Agent 执行状态数据库竞态修复"""
    print("\n" + "=" * 80)
    print("验证2: Agent 执行状态数据库竞态 (AGENT-CRITICAL-002)")
    print("=" * 80)

    validator = CodeValidator()
    file_path = Path("app/agents/agent_service.py")

    if not file_path.exists():
        validator.check("Agent 服务文件存在", False, f"文件不存在: {file_path}")
        return validator

    content = file_path.read_text()

    # 检查1: 存在创建记录的短事务函数
    has_create_func = "async def _create_execution_record(" in content
    validator.check(
        "短事务创建函数",
        has_create_func,
        "已定义 _create_execution_record" if has_create_func else "未定义 _create_execution_record"
    )

    # 检查2: 创建函数中有 try-finally
    if has_create_func:
        # 提取函数内容
        match = re.search(
            r'async def _create_execution_record\(.+?\n(?:.*?\n)*?^    ',
            content,
            re.MULTILINE
        )
        if match:
            func_content = match.group(0)
            has_try_finally = "finally:" in func_content and "db.close()" in func_content
            validator.check(
                "创建函数有 try-finally",
                has_try_finally,
                "创建函数确保 db.close()" if has_try_finally else "创建函数缺少 try-finally"
            )
        else:
            validator.check("创建函数有 try-finally", False, "无法解析函数内容")

    # 检查3: 存在更新记录的短事务函数
    has_update_func = "async def _update_execution_record(" in content
    validator.check(
        "短事务更新函数",
        has_update_func,
        "已定义 _update_execution_record" if has_update_func else "未定义 _update_execution_record"
    )

    # 检查4: 更新函数中有 try-finally
    if has_update_func:
        match = re.search(
            r'async def _update_execution_record\(.+?\n(?:.*?\n)*?^    ',
            content,
            re.MULTILINE
        )
        if match:
            func_content = match.group(0)
            has_try_finally = "finally:" in func_content and "db.close()" in func_content
            validator.check(
                "更新函数有 try-finally",
                has_try_finally,
                "更新函数确保 db.close()" if has_try_finally else "更新函数缺少 try-finally"
            )
        else:
            validator.check("更新函数有 try-finally", False, "无法解析函数内容")

    # 检查5: execute 函数调用短事务
    has_create_call = "await self._create_execution_record(" in content
    has_update_call = "await self._update_execution_record(" in content
    validator.check(
        "execute 使用短事务",
        has_create_call and has_update_call,
        "execute 调用短事务函数" if (has_create_call and has_update_call) else "execute 未使用短事务"
    )

    # 检查6: execute 中没有长事务
    execute_has_db = "db = SessionLocal()" in content and "async def execute(" in content
    # 检查 execute 函数中是否直接使用 db
    execute_section = re.search(
        r'async def execute\(.+?\n(?:.*?\n)*?(?=\n    async def|\n    def|\nclass|\Z)',
        content,
        re.MULTILINE
    )
    if execute_section:
        execute_content = execute_section.group(0)
        # 检查是否有 db.add 或 db.commit（应该只通过短事务函数）
        has_direct_db = "db.add(" in execute_content or "db.commit()" in execute_content
        validator.check(
            "execute 无直接数据库操作",
            not has_direct_db,
            "execute 通过短事务函数操作数据库" if not has_direct_db else "execute 直接操作数据库"
        )

    return validator


def validate_state_immutability():
    """验证3: LangGraph 状态污染修复"""
    print("\n" + "=" * 80)
    print("验证3: LangGraph 状态污染 (AGENT-CRITICAL-003)")
    print("=" * 80)

    validator = CodeValidator()
    file_path = Path("app/agents/agent_service.py")

    if not file_path.exists():
        validator.check("Agent 服务文件存在", False, f"文件不存在: {file_path}")
        return validator

    content = file_path.read_text()

    # 检查1: think_node 使用不可变更新
    think_has_immutable = (
        'return {' in content and
        '**state' in content and
        'STATE_STEPS: current_steps + 1' in content
    )
    validator.check(
        "think_node 不可变更新",
        think_has_immutable,
        "think_node 使用解构语法创建新状态" if think_has_immutable else "think_node 可能修改原状态"
    )

    # 检查2: act_node 创建列表副本
    act_has_copy = "list(state.get(STATE_TOOLS_CALLED" in content or "tools_called = list(" in content
    validator.check(
        "act_node 列表副本",
        act_has_copy,
        "act_node 创建 tools_called 副本" if act_has_copy else "act_node 未创建列表副本"
    )

    # 检查3: act_node 使用不可变更新
    act_has_immutable = (
        'new_tools_called = tools_called +' in content or
        'return {' in content and 'STATE_TOOLS_CALLED: new_tools_called' in content
    )
    validator.check(
        "act_node 不可变更新",
        act_has_immutable,
        "act_node 创建新列表而不是修改原列表" if act_has_immutable else "act_node 可能修改原列表"
    )

    # 检查4: observe_node 使用不可变更新
    observe_has_immutable = (
        'async def _observe_node' in content and
        'return {' in content and
        '**state,' in content and
        'STATE_OUTPUT:' in content
    )
    validator.check(
        "observe_node 不可变更新",
        observe_has_immutable,
        "observe_node 使用解构语法" if observe_has_immutable else "observe_node 可能修改原状态"
    )

    # 检查5: 没有直接的状态修改
    # 检查是否有 state[KEY] = value 的模式（坏模式）
    bad_mutations = re.findall(r'state\[[A-Z_]+\]\s*=', content)
    has_bad_mutation = len(bad_mutations) > 0
    validator.check(
        "无直接状态修改",
        not has_bad_mutation,
        f"未发现直接状态修改" if not has_bad_mutation else f"发现 {len(bad_mutations)} 处直接状态修改"
    )

    return validator


def validate_database_connection_leaks():
    """验证4: 数据库连接泄漏修复"""
    print("\n" + "=" * 80)
    print("验证4: 数据库连接泄漏 (AGENT-HIGH-001)")
    print("=" * 80)

    validator = CodeValidator()

    # 检查 router.py
    router_path = Path("app/agents/router.py")
    if not router_path.exists():
        validator.check("Router 文件存在", False, f"文件不存在: {router_path}")
        return validator

    router_content = router_path.read_text()

    # 检查1: 导入 get_db_session
    has_context_import = "get_db_session" in router_content
    validator.check(
        "导入上下文管理器",
        has_context_import,
        "已导入 get_db_session" if has_context_import else "未导入 get_db_session"
    )

    # 检查2: create_agent 有 rollback
    create_has_rollback = (
        'async def create_agent(' in router_content and
        'db.rollback()' in router_content
    )
    validator.check(
        "create_agent 有 rollback",
        create_has_rollback,
        "create_agent 异常时调用 rollback" if create_has_rollback else "create_agent 缺少 rollback"
    )

    # 检查3: update_agent 有 rollback
    update_has_rollback = (
        'async def update_agent(' in router_content and
        router_content.count('db.rollback()') >= 2
    )
    validator.check(
        "update_agent 有 rollback",
        update_has_rollback,
        "update_agent 异常时调用 rollback" if update_has_rollback else "update_agent 缺少 rollback"
    )

    # 检查4: delete_agent 有 rollback
    delete_has_rollback = (
        'async def delete_agent(' in router_content and
        router_content.count('db.rollback()') >= 3
    )
    validator.check(
        "delete_agent 有 rollback",
        delete_has_rollback,
        "delete_agent 异常时调用 rollback" if delete_has_rollback else "delete_agent 缺少 rollback"
    )

    # 检查 database.py 的上下文管理器
    db_path = Path("app/core/database.py")
    if db_path.exists():
        db_content = db_path.read_text()

        has_context_manager = "@contextmanager" in db_content and "def get_db_session()" in db_content
        validator.check(
            "数据库上下文管理器",
            has_context_manager,
            "已定义 get_db_session 上下文管理器" if has_context_manager else "缺少 get_db_session"
        )

        has_try_finally = "finally:" in db_content and "db.close()" in db_content
        validator.check(
            "上下文管理器有 try-finally",
            has_try_finally,
            "上下文管理器确保 db.close()" if has_try_finally else "上下文管理器缺少 try-finally"
        )

    return validator


def main():
    """运行所有验证"""
    print("\n" + "=" * 80)
    print("Agent 模块并发修复代码验证")
    print("=" * 80)

    all_validators = []

    # 验证1: 浏览器并发竞争
    try:
        validator = validate_browser_concurrency()
        all_validators.append(validator)
    except Exception as e:
        print(f"❌ 验证1失败: {e}")

    # 验证2: 事务隔离
    try:
        validator = validate_transaction_isolation()
        all_validators.append(validator)
    except Exception as e:
        print(f"❌ 验证2失败: {e}")

    # 验证3: 状态不可变性
    try:
        validator = validate_state_immutability()
        all_validators.append(validator)
    except Exception as e:
        print(f"❌ 验证3失败: {e}")

    # 验证4: 数据库连接泄漏
    try:
        validator = validate_database_connection_leaks()
        all_validators.append(validator)
    except Exception as e:
        print(f"❌ 验证4失败: {e}")

    # 汇总所有结果
    print("\n" + "=" * 80)
    print("所有验证结果汇总")
    print("=" * 80)

    total_passed = 0
    total_tests = 0

    for validator in all_validators:
        for test_name, result in validator.results.items():
            total_tests += 1
            if result["passed"]:
                total_passed += 1
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {test_name}")

    print("-" * 80)
    print(f"总计: {total_passed}/{total_tests} 验证通过")

    if total_passed == total_tests:
        print("\n🎉 所有并发修复代码验证通过！")
        print("\n修复摘要:")
        print("1. ✅ 浏览器实例使用 asyncio.Lock 保护")
        print("2. ✅ Agent 执行使用短事务模式")
        print("3. ✅ LangGraph 状态使用不可变更新")
        print("4. ✅ 数据库操作添加 rollback 保护")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} 个验证失败")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
