"""
性能分析报告生成工具

从测试结果生成详细的性能分析报告。
"""
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from performance_config import PerformanceThresholds, check_response_time


@dataclass
class TestResult:
    """测试结果数据类"""
    name: str
    status: str  # passed, failed, warning
    duration_ms: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    details: str = ""


@dataclass
class PerformanceReport:
    """性能报告数据类"""
    timestamp: datetime
    environment: Dict[str, str]
    test_results: List[TestResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def add_result(self, result: TestResult):
        """添加测试结果"""
        self.test_results.append(result)

    def add_recommendation(self, recommendation: str):
        """添加优化建议"""
        self.recommendations.append(recommendation)

    def generate_summary(self):
        """生成摘要统计"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.status == "passed")
        failed = sum(1 for r in self.test_results if r.status == "failed")
        warnings = sum(1 for r in self.test_results if r.status == "warning")

        self.summary = {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "success_rate": (passed / total * 100) if total > 0 else 0
        }


class PerformanceAnalyzer:
    """
    性能分析器

    分析性能测试结果并生成报告。
    """

    def __init__(self, thresholds: PerformanceThresholds = None):
        self.thresholds = thresholds or PerformanceThresholds()
        self.report = PerformanceReport(
            timestamp=datetime.utcnow(),
            environment=self._get_environment_info()
        )

    def _get_environment_info(self) -> Dict[str, str]:
        """获取环境信息"""
        import platform
        import psutil

        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": str(psutil.cpu_count()),
            "memory_total_gb": f"{psutil.virtual_memory().total / 1024 / 1024 / 1024:.2f}",
        }

    def analyze_response_times(self, endpoint: str, response_times: List[float]) -> TestResult:
        """分析响应时间"""
        if not response_times:
            return TestResult(
                name=f"Response time analysis for {endpoint}",
                status="warning",
                duration_ms=0,
                details="No response times data"
            )

        sorted_times = sorted(response_times)
        avg = sum(response_times) / len(response_times)
        p50 = sorted_times[int(len(response_times) * 0.5)]
        p95 = sorted_times[int(len(response_times) * 0.95)]
        p99 = sorted_times[int(len(response_times) * 0.99)]
        min_t = sorted_times[0]
        max_t = sorted_times[-1]

        metrics = {
            "count": len(response_times),
            "avg_ms": avg,
            "min_ms": min_t,
            "max_ms": max_t,
            "p50_ms": p50,
            "p95_ms": p95,
            "p99_ms": p99
        }

        # 检查是否符合要求
        passed, message = check_response_time(endpoint, p95)

        # 根据P99判断状态
        if p99 > self.thresholds.API_P99_RESPONSE_TIME:
            status = "failed"
        elif p95 > self.thresholds.API_P95_RESPONSE_TIME:
            status = "warning"
        else:
            status = "passed"

        return TestResult(
            name=f"Response time: {endpoint}",
            status=status,
            duration_ms=avg,
            metrics=metrics,
            details=message
        )

    def analyze_throughput(self, requests_per_second: float, target: float) -> TestResult:
        """分析吞吐量"""
        metrics = {
            "actual_rps": requests_per_second,
            "target_rps": target,
            "percentage": (requests_per_second / target * 100) if target > 0 else 0
        }

        if requests_per_second >= target:
            status = "passed"
            details = f"Throughput ({requests_per_second:.2f} RPS) meets target ({target} RPS)"
        elif requests_per_second >= target * 0.9:
            status = "warning"
            details = f"Throughput ({requests_per_second:.2f} RPS) slightly below target ({target} RPS)"
        else:
            status = "failed"
            details = f"Throughput ({requests_per_second:.2f} RPS) below target ({target} RPS)"

        return TestResult(
            name="Throughput analysis",
            status=status,
            duration_ms=1000 / requests_per_second if requests_per_second > 0 else 0,
            metrics=metrics,
            details=details
        )

    def analyze_error_rate(self, total_requests: int, failed_requests: int) -> TestResult:
        """分析错误率"""
        error_rate = failed_requests / total_requests if total_requests > 0 else 0
        success_rate = 1 - error_rate

        metrics = {
            "total": total_requests,
            "failed": failed_requests,
            "success_rate": success_rate,
            "error_rate": error_rate
        }

        if success_rate >= self.thresholds.MIN_SUCCESS_RATE:
            status = "passed"
            details = f"Success rate ({success_rate * 100:.2f}%) meets threshold"
        elif success_rate >= 0.95:
            status = "warning"
            details = f"Success rate ({success_rate * 100:.2f}%) below threshold but acceptable"
        else:
            status = "failed"
            details = f"Success rate ({success_rate * 100:.2f}%) below threshold"

        return TestResult(
            name="Error rate analysis",
            status=status,
            duration_ms=0,
            metrics=metrics,
            details=details
        )

    def analyze_resource_usage(self, memory_mb: float, cpu_percent: float) -> TestResult:
        """分析资源使用"""
        metrics = {
            "memory_mb": memory_mb,
            "cpu_percent": cpu_percent,
            "memory_threshold_mb": self.thresholds.MAX_MEMORY_MB
        }

        issues = []
        if memory_mb > self.thresholds.MAX_MEMORY_MB:
            issues.append(f"Memory ({memory_mb:.2f} MB) exceeds threshold ({self.thresholds.MAX_MEMORY_MB} MB)")

        # CPU阈值动态判断（负载情况下允许更高）
        cpu_threshold = 80
        if cpu_percent > cpu_threshold:
            issues.append(f"CPU ({cpu_percent:.2f}%) exceeds threshold ({cpu_threshold}%)")

        if issues:
            status = "failed" if cpu_percent > 90 or memory_mb > self.thresholds.MAX_MEMORY_MB * 1.5 else "warning"
            details = "; ".join(issues)
        else:
            status = "passed"
            details = "Resource usage within acceptable limits"

        return TestResult(
            name="Resource usage analysis",
            status=status,
            duration_ms=0,
            metrics=metrics,
            details=details
        )

    def generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 分析所有测试结果
        for result in self.report.test_results:
            if result.status == "failed":
                if "Response time" in result.name:
                    if result.metrics.get("p99_ms", 0) > 1000:
                        recommendations.append(
                            "API响应时间过高。建议：1) 检查数据库查询优化；"
                            "2) 考虑添加缓存；3) 优化复杂计算逻辑。"
                        )

                if "Throughput" in result.name:
                    if result.metrics.get("percentage", 100) < 80:
                        recommendations.append(
                            "吞吐量不足。建议：1) 增加worker进程数；"
                            "2) 启用连接池复用；3) 考虑使用异步操作。"
                        )

                if "Resource usage" in result.name:
                    if result.metrics.get("memory_mb", 0) > 500:
                        recommendations.append(
                            "内存使用过高。建议：1) 检查内存泄漏；"
                            "2) 优化数据结构；3) 考虑使用内存分析工具。"
                        )

                    if result.metrics.get("cpu_percent", 0) > 80:
                        recommendations.append(
                            "CPU使用过高。建议：1) 优化算法复杂度；"
                            "2) 考虑使用缓存；3) 检查是否有死循环。"
                        )

                if "Error rate" in result.name:
                    if result.metrics.get("success_rate", 1) < 0.99:
                        recommendations.append(
                            "错误率过高。建议：1) 检查日志找出错误原因；"
                            "2) 优化错误处理；3) 增加重试机制。"
                        )

        return recommendations

    def finalize_report(self) -> PerformanceReport:
        """完成报告生成"""
        self.report.generate_summary()
        self.report.recommendations = self.generate_recommendations()
        return self.report


def save_report_json(report: PerformanceReport, filepath: str):
    """保存JSON格式报告"""
    data = {
        "timestamp": report.timestamp.isoformat(),
        "environment": report.environment,
        "summary": report.summary,
        "test_results": [
            {
                "name": r.name,
                "status": r.status,
                "duration_ms": r.duration_ms,
                "metrics": r.metrics,
                "details": r.details
            }
            for r in report.test_results
        ],
        "recommendations": report.recommendations
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_report_markdown(report: PerformanceReport) -> str:
    """生成Markdown格式报告"""
    lines = [
        "# 性能测试报告",
        "",
        f"**生成时间**: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 环境信息",
        "",
        "| 项目 | 值 |",
        "|------|-----|",
    ]

    for key, value in report.environment.items():
        lines.append(f"| {key} | {value} |")

    lines.extend([
        "",
        "## 测试摘要",
        "",
        f"- **总测试数**: {report.summary.get('total_tests', 0)}",
        f"- **通过**: {report.summary.get('passed', 0)}",
        f"- **失败**: {report.summary.get('failed', 0)}",
        f"- **警告**: {report.summary.get('warnings', 0)}",
        f"- **成功率**: {report.summary.get('success_rate', 0):.2f}%",
        "",
        "## 测试结果详情",
        "",
    ])

    # 按状态分组
    passed_results = [r for r in report.test_results if r.status == "passed"]
    failed_results = [r for r in report.test_results if r.status == "failed"]
    warning_results = [r for r in report.test_results if r.status == "warning"]

    if passed_results:
        lines.extend([
            "### ✅ 通过的测试",
            ""
        ])
        for result in passed_results:
            lines.extend([
                f"#### {result.name}",
                f"- **状态**: {result.status}",
                f"- **详情**: {result.details}",
                ""
            ])

    if warning_results:
        lines.extend([
            "### ⚠️ 警告的测试",
            ""
        ])
        for result in warning_results:
            lines.extend([
                f"#### {result.name}",
                f"- **状态**: {result.status}",
                f"- **详情**: {result.details}",
                ""
            ])

    if failed_results:
        lines.extend([
            "### ❌ 失败的测试",
            ""
        ])
        for result in failed_results:
            lines.extend([
                f"#### {result.name}",
                f"- **状态**: {result.status}",
                f"- **详情**: {result.details}",
                ""
            ])

            # 添加指标详情
            if result.metrics:
                lines.append("**指标**:")
                lines.append("| 指标 | 值 |")
                lines.append("|------|-----|")
                for key, value in result.metrics.items():
                    lines.append(f"| {key} | {value} |")
                lines.append("")

    # 添加优化建议
    if report.recommendations:
        lines.extend([
            "## 优化建议",
            ""
        ])
        for i, rec in enumerate(report.recommendations, 1):
            lines.extend([f"{i}. {rec}", ""])

    return "\n".join(lines)


def save_report_markdown(report: PerformanceReport, filepath: str):
    """保存Markdown格式报告"""
    content = generate_report_markdown(report)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == "__main__":
    # 示例：创建一个模拟报告
    analyzer = PerformanceAnalyzer()

    # 添加模拟测试结果
    analyzer.report.add_result(
        analyzer.analyze_response_times("/api/v1/auth/me", [50, 60, 55, 45, 70, 80, 65, 75])
    )

    analyzer.report.add_result(
        analyzer.analyze_throughput(150, 100)
    )

    analyzer.report.add_result(
        analyzer.analyze_error_rate(1000, 5)
    )

    analyzer.report.add_result(
        analyzer.analyze_resource_usage(256, 45)
    )

    # 完成报告
    report = analyzer.finalize_report()

    # 保存报告
    output_dir = Path("test_results")
    output_dir.mkdir(exist_ok=True)

    save_report_json(report, str(output_dir / "performance_report.json"))
    save_report_markdown(report, str(output_dir / "performance_report.md"))

    print(f"报告已保存到: {output_dir}")
