#!/usr/bin/env python3
"""
测试运行脚本
Test Runner Script

运行所有测试并生成报告
"""
import os
import sys
import subprocess
import argparse
from datetime import datetime
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """运行命令并返回是否成功"""
    print(f"\n{'='*60}")
    print(f"运行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print('='*60)

    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

    return result.returncode == 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行BrightChat测试")
    parser.add_argument(
        "--unit",
        action="store_true",
        help="只运行单元测试"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="只运行集成测试"
    )
    parser.add_argument(
        "--rag",
        action="store_true",
        help="只运行RAG模块测试"
    )
    parser.add_argument(
        "--agent",
        action="store_true",
        help="只运行Agent模块测试"
    )
    parser.add_argument(
        "--skip-slow",
        action="store_true",
        help="跳过慢速测试"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="详细输出"
    )
    parser.add_argument(
        "--report",
        choices=["html", "json", "term"],
        default="term",
        help="报告格式"
    )

    args = parser.parse_args()

    # 构建pytest命令
    pytest_cmd = ["python3", "-m", "pytest"]

    # 添加测试路径
    if args.unit:
        pytest_cmd.extend(["-m", "unit"])
    elif args.integration:
        pytest_cmd.extend(["-m", "integration"])
    elif args.rag:
        pytest_cmd.extend(["-m", "rag"])
    elif args.agent:
        pytest_cmd.extend(["-m", "agent"])

    # 跳过慢速测试
    if args.skip_slow:
        pytest_cmd.extend(["-m", "not slow"])

    # 添加详细输出
    if args.verbose:
        pytest_cmd.extend(["-vv", "-s"])

    # 添加报告格式
    if args.report == "html":
        pytest_cmd.extend(["--html=reports/pytest_report.html"])
        pytest_cmd.extend(["--self-contained-html"])
    elif args.report == "json":
        pytest_cmd.extend(["--json-report"])
        pytest_cmd.extend(["--json-report-file=reports/pytest_report.json"])

    # 创建报告目录
    Path("reports").mkdir(exist_ok=True)

    # 运行测试
    start_time = datetime.now()
    success = run_command(pytest_cmd, "运行测试套件")

    # 计算耗时
    duration = (datetime.now() - start_time).total_seconds()

    # 打印总结
    print(f"\n{'='*60}")
    print("测试总结")
    print('='*60)
    print(f"状态: {'✅ 成功' if success else '❌ 失败'}")
    print(f"耗时: {duration:.2f} 秒")
    print('='*60)

    # 如果测试HTML报告生成，显示路径
    if args.report == "html":
        report_path = Path("reports/pytest_report.html").absolute()
        if report_path.exists():
            print(f"\n📊 测试报告: file://{report_path}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
