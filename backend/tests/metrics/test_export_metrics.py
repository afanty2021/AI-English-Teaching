"""
Prometheus 监控指标测试套件

测试导出功能的 Prometheus 指标收集。
"""
import asyncio

import pytest
from prometheus_client import Counter, Gauge, Histogram

from app.metrics.export_metrics import (
    decrement_active_tasks,
    export_errors_total,
    export_storage_bytes,
    export_task_duration_seconds,
    export_tasks_active,
    export_tasks_queued,
    export_tasks_total,
    increment_active_tasks,
    record_export_task_completed,
    record_export_task_failed,
    record_export_task_started,
    set_queued_tasks,
    update_storage_metrics,
)

# ==================== 辅助函数 ====================

def _get_sample_value(metric, sample_name: str, labels: dict | None = None) -> float:
    """
    从指标中获取特定样本的值。

    Args:
        metric: Prometheus 指标对象
        sample_name: 样本名称（如 "export_tasks_total", "export_tasks_active" 等）
        labels: 标签字典，用于筛选样本

    Returns:
        样本的值，如果找不到则返回 0.0
    """
    # 注意：不要提前调用 metric.labels()，否则 collect() 时标签信息会丢失
    samples = list(metric.collect())[0].samples
    for sample in samples:
        # 检查样本名称是否匹配
        if sample.name == sample_name:
            # 如果没有指定标签，直接返回第一个匹配的样本
            if labels is None:
                return sample.value
            # 检查标签是否匹配（标签值在 Prometheus 中都是字符串）
            if all(sample.labels.get(k) == str(v) for k, v in labels.items()):
                return sample.value
    return 0.0


def _get_histogram_count(metric, labels: dict | None = None) -> float:
    """
    获取 Histogram 的观察次数。

    Args:
        metric: Histogram 指标对象
        labels: 标签字典

    Returns:
        观察次数
    """
    # 注意：不要提前调用 metric.labels()，否则 collect() 时标签信息会丢失
    samples = list(metric.collect())[0].samples
    for sample in samples:
        if sample.name.endswith("_count"):
            if labels is None or all(sample.labels.get(k) == str(v) for k, v in labels.items()):
                return sample.value
    return 0.0


# ==================== Fixtures ====================

@pytest.fixture(autouse=True)
def ensure_clean_metrics() -> None:
    """
    确保每个测试前指标是干净的。

    不使用重新导入的方式，而是确保测试之间的隔离。
    """
    yield

    # 测试后不清理，避免影响其他测试
    # 每个测试应该使用不同的标签组合来避免污染


# ==================== 测试类: 指标初始化 ====================

class TestExportMetrics:
    """测试指标初始化和基本属性。"""

    def test_export_tasks_total_is_counter(self) -> None:
        """验证 export_tasks_total 是 Counter 类型。"""
        assert isinstance(export_tasks_total, Counter)

    def test_export_task_duration_seconds_is_histogram(self) -> None:
        """验证 export_task_duration_seconds 是 Histogram 类型。"""
        assert isinstance(export_task_duration_seconds, Histogram)

    def test_export_tasks_active_is_gauge(self) -> None:
        """验证 export_tasks_active 是 Gauge 类型。"""
        assert isinstance(export_tasks_active, Gauge)

    def test_export_tasks_queued_is_gauge(self) -> None:
        """验证 export_tasks_queued 是 Gauge 类型。"""
        assert isinstance(export_tasks_queued, Gauge)

    def test_export_storage_bytes_is_gauge(self) -> None:
        """验证 export_storage_bytes 是 Gauge 类型。"""
        assert isinstance(export_storage_bytes, Gauge)

    def test_export_errors_total_is_counter(self) -> None:
        """验证 export_errors_total 是 Counter 类型。"""
        assert isinstance(export_errors_total, Counter)

    def test_export_tasks_total_labels(self) -> None:
        """验证 export_tasks_total 有正确的标签名称。"""
        assert export_tasks_total._labelnames == ("status", "format")

    def test_export_task_duration_seconds_labels(self) -> None:
        """验证 export_task_duration_seconds 有正确的标签名称。"""
        assert export_task_duration_seconds._labelnames == ("format",)

    def test_export_task_duration_seconds_buckets(self) -> None:
        """验证 Histogram 桶配置正确。"""
        upper_bounds = export_task_duration_seconds._upper_bounds
        expected_values = [1, 5, 10, 20, 30, 60, 120, 300, 600, float("inf")]
        assert len(upper_bounds) == len(expected_values)
        for expected, actual in zip(expected_values, upper_bounds):
            assert actual == expected


# ==================== 测试类: 指标操作 ====================

class TestMetricOperations:
    """测试指标的基本操作。"""

    def test_counter_increment(self) -> None:
        """测试 Counter 递增功能。"""
        # 使用唯一的标签组合避免污染其他测试
        labels = {"status": "test_inc", "format": "test1"}

        # 递增两次
        export_tasks_total.labels(**labels).inc()
        export_tasks_total.labels(**labels).inc()

        # 获取值
        value = _get_sample_value(export_tasks_total, "export_tasks_total", labels)

        assert value == 2.0

    def test_gauge_increment(self) -> None:
        """测试 Gauge 递增功能。"""
        # 先增加几次确保有值
        increment_active_tasks()
        increment_active_tasks()

        # 获取值
        value = _get_sample_value(export_tasks_active, "export_tasks_active")
        assert value >= 2.0

    def test_gauge_decrement(self) -> None:
        """测试 Gauge 递减功能。"""
        # 先增加
        increment_active_tasks()
        increment_active_tasks()

        # 获取增加后的值
        value_after_inc = _get_sample_value(export_tasks_active, "export_tasks_active")

        # 再减少
        decrement_active_tasks()

        # 获取减少后的值
        value_after_dec = _get_sample_value(export_tasks_active, "export_tasks_active")

        assert value_after_dec == value_after_inc - 1

    def test_gauge_set(self) -> None:
        """测试 Gauge 设置功能。"""
        set_queued_tasks(42)
        value = _get_sample_value(export_tasks_queued, "export_tasks_queued")
        assert value == 42

    def test_histogram_observe(self) -> None:
        """测试 Histogram 观察功能。"""
        labels = {"format": "test_hist_observe"}
        export_task_duration_seconds.labels(**labels).observe(5.5)

        count = _get_histogram_count(export_task_duration_seconds, labels)
        assert count == 1


# ==================== 测试类: 上下文管理器 ====================

@pytest.mark.asyncio
class TestMetricContextManager:
    """测试上下文管理器功能。"""

    async def test_context_manager_increments_active(self) -> None:
        """测试上下文管理器增加活跃任务计数。"""
        # 获取初始值
        initial = _get_sample_value(export_tasks_active, "export_tasks_active")

        async with record_export_task_started("test_format_cm1"):
            # 在上下文中，活跃任务应该增加
            value_during = _get_sample_value(export_tasks_active, "export_tasks_active")
            assert value_during >= initial + 1

        # 退出后应该恢复
        value_after = _get_sample_value(export_tasks_active, "export_tasks_active")
        assert value_after == initial

    async def test_context_manager_records_duration(self) -> None:
        """测试上下文管理器记录任务耗时。"""
        format_label = "test_format_cm_duration"

        async with record_export_task_started(format_label):
            # 模拟一些工作
            await asyncio.sleep(0.01)

        # 检查是否记录了观察
        count = _get_histogram_count(export_task_duration_seconds, {"format": format_label})
        assert count == 1

    async def test_context_manager_handles_exception(self) -> None:
        """测试上下文管理器正确处理异常。"""
        initial = _get_sample_value(export_tasks_active, "export_tasks_active")

        with pytest.raises(ValueError):
            async with record_export_task_started("test_format_cm3"):
                raise ValueError("Test error")

        # 即使有异常，活跃任务计数也应该恢复
        value_after = _get_sample_value(export_tasks_active, "export_tasks_active")
        assert value_after == initial

    async def test_context_manager_with_task_id(self) -> None:
        """测试带任务ID的上下文管理器（功能测试）。"""
        # 这个测试主要是验证代码不会崩溃
        async with record_export_task_started("test_format_cm4", task_id="test-123"):
            await asyncio.sleep(0.001)

        # 如果执行到这里，说明没有异常
        assert True


# ==================== 测试类: 标签组合 ====================

class TestMetricLabelCombinations:
    """测试不同标签组合。"""

    def test_record_export_task_completed_all_formats(self) -> None:
        """测试所有格式的任务完成记录。"""
        formats = ["test_pdf", "test_markdown", "test_word"]

        for fmt in formats:
            record_export_task_completed(fmt)

        # 验证每个格式都有记录
        samples = list(export_tasks_total.collect())[0].samples
        success_samples = [
            s for s in samples
            if s.name == "export_tasks_total"
            and s.labels.get("status") == "success"
            and s.labels.get("format") in formats
        ]
        assert len(success_samples) == len(formats)

    def test_record_export_task_failed_all_error_types(self) -> None:
        """测试所有错误类型的失败记录。"""
        error_types = ["test_validation_err", "test_generation_err", "test_storage_err", "test_timeout_err"]

        for error_type in error_types:
            record_export_task_failed(error_type, "test_format_err")

        # 验证每个错误类型都有记录
        # 注意：Counter 会有 _total 和 _created 两个指标，我们需要筛选 _total
        samples = list(export_errors_total.collect()[0].samples)
        error_samples = [
            s for s in samples
            if s.labels.get("error_type") in error_types and s.name == "export_errors_total"
        ]
        assert len(error_samples) == len(error_types)

    def test_multiple_status_labels(self) -> None:
        """测试多个状态标签。"""
        record_export_task_completed("test_format_status1", "success")
        record_export_task_failed("test_error_type", "test_format_status1")

        samples = list(export_tasks_total.collect()[0].samples)

        # 筛选我们感兴趣的标签组合
        relevant_samples = [
            s for s in samples
            if s.labels.get("format") == "test_format_status1"
        ]

        # 应该有成功和失败的记录
        status_values = {s.labels.get("status") for s in relevant_samples}
        assert "success" in status_values
        assert "failed" in status_values

    def test_storage_metrics_both_types(self) -> None:
        """测试存储指标的两个类型。"""
        update_storage_metrics(used_bytes=1000000, available_bytes=5000000)

        samples = list(export_storage_bytes.collect()[0].samples)

        type_values = {s.labels.get("type") for s in samples}
        assert "used" in type_values
        assert "available" in type_values

        # 验证值是否正确
        used_sample = next(s for s in samples if s.labels.get("type") == "used")
        available_sample = next(s for s in samples if s.labels.get("type") == "available")

        assert used_sample.value == 1000000
        assert available_sample.value == 5000000

    def test_histogram_multiple_formats(self) -> None:
        """测试多个格式的 Histogram 记录。"""
        formats = ["test_hist_pdf", "test_hist_md", "test_hist_word"]

        for fmt in formats:
            export_task_duration_seconds.labels(format=fmt).observe(10.0)

        samples = list(export_task_duration_seconds.collect()[0].samples)
        # 每个格式应该有计数
        count_samples = [
            s for s in samples
            if s.name == "export_task_duration_seconds_count"
            and s.labels.get("format") in formats
        ]
        assert len(count_samples) == len(formats)
