#!/usr/bin/env python3
"""
性能测试运行脚本

运行所有性能测试并生成报告。
"""
import asyncio
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import List

# 添加tests目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from performance_analyzer import PerformanceAnalyzer, save_report_json, save_report_markdown
from performance_config import PerformanceThresholds


def run_command(cmd: List[str], description: str) -> tuple[bool, str, float]:
    """
    运行命令并捕获输出

    Returns:
        (成功状态, 输出文本, 执行时间秒)
    """
    import time

    print(f"🚀 运行: {description}")
    print(f"   命令: {' '.join(cmd)}")

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )

        duration = time.time() - start
        success = result.returncode == 0

        if success:
            print(f"✅ 完成 ({duration:.2f}s)")
        else:
            print(f"❌ 失败 ({duration:.2f}s)")
            print(f"   错误: {result.stderr[:500]}")

        return success, result.stdout, duration

    except subprocess.TimeoutExpired:
        print(f"⏱️ 超时 (>600s)")
        return False, "", 600
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False, "", 0


def run_db_tests() -> List[dict]:
    """运行数据库性能测试"""
    print("\n" + "=" * 60)
    print("📊 数据库性能测试")
    print("=" * 60)

    cmd = [
        "pytest",
        "tests/performance/test_db_performance.py",
        "-v",
        "-m", "performance",
        "--tb=short"
    ]

    success, output, duration = run_command(cmd, "数据库性能测试")

    return [{
        "name": "Database Performance Tests",
        "success": success,
        "output": output,
        "duration": duration
    }]


def run_api_load_tests() -> List[dict]:
    """运行API负载测试"""
    print("\n" + "=" * 60)
    print("🌐 API负载测试")
    print("=" * 60)

    cmd = [
        "pytest",
        "tests/performance/test_api_load.py",
        "-v",
        "-m", "performance",
        "--tb=short"
    ]

    success, output, duration = run_command(cmd, "API负载测试")

    return [{
        "name": "API Load Tests",
        "success": success,
        "output": output,
        "duration": duration
    }]


def run_resource_tests() -> List[dict]:
    """运行资源测试"""
    print("\n" + "=" * 60)
    print("💾 资源使用测试")
    print("=" * 60)

    cmd = [
        "pytest",
        "tests/performance/test_memory_cpu.py",
        "-v",
        "-m", "performance",
        "--tb=short"
    ]

    success, output, duration = run_command(cmd, "资源使用测试")

    return [{
        "name": "Resource Usage Tests",
        "success": success,
        "output": output,
        "duration": duration
    }]


def run_locust_tests(users: int = 100, spawn_rate: float = 10, duration: int = 60):
    """运行Locust压力测试"""
    print("\n" + "=" * 60)
    print(f"📍 Locust压力测试 ({users} 用户, {duration}秒)")
    print("=" * 60)

    cmd = [
        "locust",
        "-f", "tests/performance/locustfile.py",
        "--headless",
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", f"{duration}s",
        "--host", "http://localhost:8000",
        "--html", "test_results/locust_report.html"
    ]

    success, output, duration = run_command(cmd, "Locust压力测试")

    return [{
        "name": "Locust Load Test",
        "success": success,
        "output": output,
        "duration": duration,
        "metrics": {
            "users": users,
            "spawn_rate": spawn_rate,
            "target_duration": duration
        }
    }]


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="运行性能测试套件")
    parser.add_argument("--skip-db", action="store_true", help="跳过数据库测试")
    parser.add_argument("--skip-api", action="store_true", help="跳过API负载测试")
    parser.add_argument("--skip-resource", action="store_true", help="跳过资源测试")
    parser.add_argument("--skip-locust", action="store_true", help="跳过Locust测试")
    parser.add_argument("--locust-users", type=int, default=100, help="Locust用户数")
    parser.add_argument("--locust-duration", type=int, default=60, help="Locust测试时长（秒）")
    parser.add_argument("--output-dir", default="test_results", help="输出目录")

    args = parser.parse_args()

    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("🚀 AI英语教学系统 - 性能测试套件")
    print("=" * 60)
    print(f"输出目录: {output_dir.absolute()}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 收集所有测试结果
    all_results = []
    total_start = datetime.now()

    # 运行各项测试
    if not args.skip_db:
        all_results.extend(run_db_tests())

    if not args.skip_api:
        all_results.extend(run_api_load_tests())

    if not args.skip_resource:
        all_results.extend(run_resource_tests())

    if not args.skip_locust:
        all_results.extend(run_locust_tests(args.locust_users, 10, args.locust_duration))

    total_duration = (datetime.now() - total_start).total_seconds()

    # 生成摘要
    print("\n" + "=" * 60)
    print("📊 测试摘要")
    print("=" * 60)

    for result in all_results:
        status_icon = "✅" if result["success"] else "❌"
        print(f"{status_icon} {result['name']}: {result['duration']:.2f}s")

    total_passed = sum(1 for r in all_results if r["success"])
    print(f"\n总计: {len(all_results)} 测试, {total_passed} 通过, {len(all_results) - total_passed} 失败")
    print(f"总耗时: {total_duration:.2f}s")

    # 生成测试报告
    analyzer = PerformanceAnalyzer()

    # 添加模拟结果（实际应从测试输出解析）
    # TODO: 解析实际测试输出并添加到报告

    report = analyzer.finalize_report()

    # 保存报告
    report_path = output_dir / "performance_report.md"
    json_path = output_dir / "performance_report.json"

    save_report_markdown(report, str(report_path))
    save_report_json(report, str(json_path))

    print(f"\n📄 报告已保存:")
    print(f"   Markdown: {report_path}")
    print(f"   JSON: {json_path}")

    # 根据测试结果返回适当的退出码
    sys.exit(0 if total_passed == len(all_results) else 1)


if __name__ == "__main__":
    main()
