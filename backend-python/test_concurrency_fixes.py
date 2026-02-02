#!/usr/bin/env python3
"""
并发修复验证测试
Concurrency Fixes Verification Test

验证 Agent 模块的 4 个关键并发问题修复：
1. AGENT-CRITICAL-001: 浏览器实例并发竞争
2. AGENT-CRITICAL-002: Agent 执行状态数据库竞态
3. AGENT-CRITICAL-003: LangGraph 状态污染
4. AGENT-HIGH-001: 数据库连接泄漏
"""
import asyncio
import time
import logging
from typing import List
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.tools.browser_tool import browser_tool, close_browser
from app.agents.agent_service import AgentService, get_agent_service
from app.models.agent import Agent
from app.core.database import SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResults:
    """测试结果收集"""
    def __init__(self):
        self.results = {}

    def add(self, test_name: str, passed: bool, message: str = ""):
        self.results[test_name] = {
            "passed": passed,
            "message": message
        }

    def print_summary(self):
        print("\n" + "=" * 80)
        print("并发修复验证测试总结")
        print("=" * 80)

        passed_count = sum(1 for r in self.results.values() if r["passed"])
        total_count = len(self.results)

        for test_name, result in self.results.items():
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"{status} - {test_name}")
            if result["message"]:
                print(f"    {result['message']}")

        print("-" * 80)
        print(f"总计: {passed_count}/{total_count} 测试通过")
        print("=" * 80)

        return passed_count == total_count


async def test_browser_concurrency():
    """测试1: 浏览器实例并发竞争修复"""
    print("\n" + "=" * 80)
    print("测试1: 浏览器实例并发竞争 (AGENT-CRITICAL-001)")
    print("=" * 80)

    results = TestResults()

    try:
        # 并发测试：多个协程同时调用浏览器工具
        logger.info("启动 10 个并发浏览器任务...")

        async def browser_task(task_id: int):
            """并发浏览器任务"""
            start_time = time.time()
            try:
                result = await browser_tool(
                    action="navigate",
                    url="https://www.example.com",
                    wait_time=1000
                )
                duration = time.time() - start_time
                logger.info(f"任务 {task_id} 完成，耗时: {duration:.2f}秒，成功: {result.get('success')}")
                return result.get("success", False)
            except Exception as e:
                logger.error(f"任务 {task_id} 失败: {e}")
                return False

        # 并发执行 10 个任务
        start_time = time.time()
        tasks = [browser_task(i) for i in range(10)]
        task_results = await asyncio.gather(*tasks)
        total_duration = time.time() - start_time

        success_count = sum(1 for r in task_results if r)
        logger.info(f"并发测试完成: {success_count}/10 成功，总耗时: {total_duration:.2f}秒")

        # 验证结果
        if success_count >= 8:  # 允许少量失败
            results.add(
                "浏览器并发竞争",
                True,
                f"10个并发任务中{success_count}个成功，总耗时{total_duration:.2f}秒"
            )
        else:
            results.add(
                "浏览器并发竞争",
                False,
                f"10个并发任务中仅{success_count}个成功，成功率过低"
            )

    except Exception as e:
        logger.error(f"测试失败: {e}")
        results.add("浏览器并发竞争", False, str(e))

    finally:
        # 清理浏览器
        await close_browser()

    return results


async def test_agent_state_immutability():
    """测试3: LangGraph 状态污染修复"""
    print("\n" + "=" * 80)
    print("测试3: LangGraph 状态污染 (AGENT-CRITICAL-003)")
    print("=" * 80)

    results = TestResults()

    try:
        agent_service = get_agent_service()

        # 创建测试 Agent
        db = SessionLocal()
        try:
            agent = Agent(
                name="test_concurrent_agent",
                display_name="Test Concurrent Agent",
                description="Test agent for concurrency",
                agent_type="tool",
                tools=["calculator", "datetime"],
                config={"max_steps": 5},
                created_by="test_user"
            )
            db.add(agent)
            db.commit()
            agent_id = agent.id
            logger.info(f"创建测试 Agent: {agent_id}")
        finally:
            db.close()

        # 并发执行多个 Agent 任务
        logger.info("启动 5 个并发 Agent 任务...")

        async def agent_task(task_id: int):
            """并发 Agent 任务"""
            try:
                step_count = 0
                async for event in agent_service.execute(
                    agent=agent,
                    query=f"任务{task_id}: 1 + 1 等于多少？",
                    user_id="test_user",
                    session_id=None
                ):
                    if event.get("type") == "step":
                        step_count += 1

                logger.info(f"Agent 任务 {task_id} 完成，执行了 {step_count} 步")
                return True, step_count
            except Exception as e:
                logger.error(f"Agent 任务 {task_id} 失败: {e}")
                return False, 0

        # 并发执行 5 个任务
        start_time = time.time()
        tasks = [agent_task(i) for i in range(5)]
        task_results = await asyncio.gather(*tasks)
        total_duration = time.time() - start_time

        success_count = sum(1 for success, _ in task_results if success)
        total_steps = sum(steps for _, steps in task_results)

        logger.info(f"并发测试完成: {success_count}/5 成功，总步数: {total_steps}，总耗时: {total_duration:.2f}秒")

        # 验证每个任务都有独立的步数（没有状态污染）
        steps_list = [steps for _, steps in task_results]
        unique_steps = len(set(steps_list))

        if success_count >= 4 and unique_steps >= 3:
            results.add(
                "LangGraph 状态不可变性",
                True,
                f"5个并发任务中{success_count}个成功，步数分布: {steps_list}（状态独立）"
            )
        else:
            results.add(
                "LangGraph 状态不可变性",
                False,
                f"状态可能被污染: {steps_list}"
            )

        # 清理测试 Agent
        db = SessionLocal()
        try:
            test_agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if test_agent:
                db.delete(test_agent)
                db.commit()
                logger.info(f"删除测试 Agent: {agent_id}")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        results.add("LangGraph 状态不可变性", False, str(e))

    return results


async def test_database_connection_management():
    """测试4: 数据库连接泄漏修复"""
    print("\n" + "=" * 80)
    print("测试4: 数据库连接泄漏 (AGENT-HIGH-001)")
    print("=" * 80)

    results = TestResults()

    try:
        from app.core.database import engine
        from sqlalchemy import text

        # 记录初始连接数
        def get_connection_count():
            """获取当前连接数"""
            try:
                with engine.connect() as conn:
                    result = conn.execute(text("SHOW STATUS LIKE 'Threads_connected'"))
                    row = result.fetchone()
                    return int(row[1]) if row else 0
            except:
                # 如果查询失败，使用 pool 的 size
                return engine.pool.size()

        initial_connections = get_connection_count()
        logger.info(f"初始连接数: {initial_connections}")

        # 模拟多个 Agent 执行（使用短事务）
        agent_service = get_agent_service()

        db = SessionLocal()
        try:
            agent = Agent(
                name="test_db_leak",
                display_name="Test DB Leak",
                description="Test agent for DB leaks",
                agent_type="tool",
                tools=["calculator"],
                config={"max_steps": 3},
                created_by="test_user"
            )
            db.add(agent)
            db.commit()
            agent_id = agent.id
        finally:
            db.close()

        # 执行多个任务
        logger.info("执行 20 个连续任务...")

        for i in range(20):
            try:
                async for event in agent_service.execute(
                    agent=agent,
                    query=f"{i} + 1",
                    user_id="test_user",
                    session_id=None
                ):
                    if event.get("type") in ["complete", "error"]:
                        break
            except Exception as e:
                logger.warning(f"任务 {i} 失败: {e}")

        # 等待连接池稳定
        await asyncio.sleep(2)

        # 检查最终连接数
        final_connections = get_connection_count()
        connection_increase = final_connections - initial_connections

        logger.info(f"最终连接数: {final_connections}")
        logger.info(f"连接增加: {connection_increase}")

        # 验证连接没有显著增加
        if connection_increase <= 5:  # 允许少量增加
            results.add(
                "数据库连接管理",
                True,
                f"20个任务后连接增加{connection_increase}个（正常范围）"
            )
        else:
            results.add(
                "数据库连接管理",
                False,
                f"20个任务后连接增加{connection_increase}个（可能存在泄漏）"
            )

        # 清理
        db = SessionLocal()
        try:
            test_agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if test_agent:
                db.delete(test_agent)
                db.commit()
        finally:
            db.close()

    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        results.add("数据库连接管理", False, str(e))

    return results


async def test_transaction_isolation():
    """测试2: Agent 执行状态数据库竞态修复"""
    print("\n" + "=" * 80)
    print("测试2: Agent 执行状态数据库竞态 (AGENT-CRITICAL-002)")
    print("=" * 80)

    results = TestResults()

    try:
        from app.models.agent import AgentExecution

        agent_service = get_agent_service()

        # 创建测试 Agent
        db = SessionLocal()
        try:
            agent = Agent(
                name="test_transaction",
                display_name="Test Transaction",
                description="Test agent for transaction isolation",
                agent_type="tool",
                tools=["calculator"],
                config={"max_steps": 3},
                created_by="test_user"
            )
            db.add(agent)
            db.commit()
            agent_id = agent.id
        finally:
            db.close()

        # 并发执行多个 Agent 任务
        logger.info("启动 10 个并发 Agent 任务测试事务隔离...")

        async def transaction_task(task_id: int):
            """并发事务任务"""
            try:
                async for event in agent_service.execute(
                    agent=agent,
                    query=f"{task_id} + {task_id}",
                    user_id=f"user_{task_id}",
                    session_id=None
                ):
                    if event.get("type") == "complete":
                        return True
                    elif event.get("type") == "error":
                        return False
                return True
            except Exception as e:
                logger.error(f"事务任务 {task_id} 失败: {e}")
                return False

        # 并发执行
        start_time = time.time()
        tasks = [transaction_task(i) for i in range(10)]
        task_results = await asyncio.gather(*tasks)
        total_duration = time.time() - start_time

        success_count = sum(1 for success in task_results if success)
        logger.info(f"并发测试完成: {success_count}/10 成功，总耗时: {total_duration:.2f}秒")

        # 验证数据库中的执行记录
        db = SessionLocal()
        try:
            executions = db.query(AgentExecution).filter(
                AgentExecution.agent_id == agent_id
            ).all()

            logger.info(f"数据库中的执行记录数: {len(executions)}")

            # 检查状态一致性
            status_counts = {}
            for exec in executions:
                status = exec.status
                status_counts[status] = status_counts.get(status, 0) + 1

            logger.info(f"执行记录状态分布: {status_counts}")

            # 验证：没有"running"状态的记录（都已正确更新）
            running_count = status_counts.get("running", 0)

            if len(executions) >= 8 and running_count == 0:
                results.add(
                    "事务隔离和状态更新",
                    True,
                    f"10个并发任务，{len(executions)}条记录，无遗留running状态"
                )
            else:
                results.add(
                    "事务隔离和状态更新",
                    False,
                    f"记录数: {len(executions)}, running状态: {running_count}"
                )

        finally:
            db.close()

        # 清理测试数据
        db = SessionLocal()
        try:
            db.query(AgentExecution).filter(AgentExecution.agent_id == agent_id).delete()
            test_agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if test_agent:
                db.delete(test_agent)
            db.commit()
            logger.info(f"清理测试 Agent: {agent_id}")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        results.add("事务隔离和状态更新", False, str(e))

    return results


async def main():
    """运行所有并发测试"""
    print("\n" + "=" * 80)
    print("Agent 模块并发修复验证测试套件")
    print("=" * 80)

    all_results = []

    # 测试1: 浏览器并发竞争
    try:
        results = await test_browser_concurrency()
        all_results.append(results)
    except Exception as e:
        logger.error(f"测试1异常: {e}", exc_info=True)

    # 等待资源释放
    await asyncio.sleep(2)

    # 测试2: 事务隔离
    try:
        results = await test_transaction_isolation()
        all_results.append(results)
    except Exception as e:
        logger.error(f"测试2异常: {e}", exc_info=True)

    # 等待资源释放
    await asyncio.sleep(2)

    # 测试3: 状态不可变性
    try:
        results = await test_agent_state_immutability()
        all_results.append(results)
    except Exception as e:
        logger.error(f"测试3异常: {e}", exc_info=True)

    # 等待资源释放
    await asyncio.sleep(2)

    # 测试4: 数据库连接管理
    try:
        results = await test_database_connection_management()
        all_results.append(results)
    except Exception as e:
        logger.error(f"测试4异常: {e}", exc_info=True)

    # 汇总所有结果
    print("\n" + "=" * 80)
    print("所有测试结果汇总")
    print("=" * 80)

    total_passed = 0
    total_tests = 0

    for results in all_results:
        for test_name, result in results.results.items():
            total_tests += 1
            if result["passed"]:
                total_passed += 1
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {test_name}")

    print("-" * 80)
    print(f"总计: {total_passed}/{total_tests} 测试通过")

    if total_passed == total_tests:
        print("\n🎉 所有并发修复验证测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
