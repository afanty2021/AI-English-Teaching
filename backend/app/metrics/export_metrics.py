"""
Prometheus 监控指标定义

为教案导出功能提供完整的 Prometheus 指标收集。

指标类型:
- Counter: 计数器，单调递增
- Gauge: 仪表，可增可减
- Histogram: 直方图，记录分布情况
"""
import contextlib
import logging
import time
from typing import AsyncGenerator, Optional

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# ==================== 指标定义 ====================

# 任务总数（按状态和格式分类）
export_tasks_total = Counter(
    "export_tasks_total",
    "导出任务总数",
    ["status", "format"]  # status: success/failed, format: pdf/markdown/word
)

# 任务耗时分布（按格式分类）
export_task_duration_seconds = Histogram(
    "export_task_duration_seconds",
    "导出任务耗时（秒）",
    ["format"],  # format: pdf/markdown/word
    buckets=(1, 5, 10, 20, 30, 60, 120, 300, 600, float("inf"))  # 1s到10min+
)

# 当前活跃任务数
export_tasks_active = Gauge(
    "export_tasks_active",
    "当前正在执行的导出任务数"
)

# 当前排队任务数
export_tasks_queued = Gauge(
    "export_tasks_queued",
    "当前排队等待的导出任务数"
)

# 存储使用情况（按类型分类）
export_storage_bytes = Gauge(
    "export_storage_bytes",
    "导出存储使用情况（字节）",
    ["type"]  # type: used/available
)

# 错误总数（按错误类型分类）
export_errors_total = Counter(
    "export_errors_total",
    "导出任务错误总数",
    ["error_type"]  # error_type: validation/generation/storage/timeout
)


# ==================== 辅助函数 ====================

@contextlib.asynccontextmanager
async def record_export_task_started(
    format: str,
    task_id: Optional[str] = None
) -> AsyncGenerator[None, None]:
    """
    记录导出任务开始和完成的上下文管理器。

    自动记录：
    1. 任务开始时增加活跃任务计数
    2. 任务结束时减少活跃任务计数
    3. 记录任务耗时到 Histogram

    Args:
        format: 导出格式 (pdf/markdown/word)
        task_id: 可选的任务ID，用于日志记录

    Example:
        >>> async with record_export_task_started("pdf", task_id="123"):
        ...     await generate_pdf()

    Yields:
        None
    """
    start_time = time.time()
    increment_active_tasks()

    if task_id:
        logger.debug(f"开始记录导出任务 {task_id}，格式: {format}")

    try:
        yield
    finally:
        # 记录耗时
        duration = time.time() - start_time
        export_task_duration_seconds.labels(format=format).observe(duration)

        # 减少活跃任务计数
        decrement_active_tasks()

        if task_id:
            logger.debug(
                f"导出任务 {task_id} 完成，耗时: {duration:.2f}秒"
            )


def record_export_task_completed(format: str, status: str = "success") -> None:
    """
    记录导出任务完成。

    Args:
        format: 导出格式 (pdf/markdown/word)
        status: 任务状态 (success/failed)，默认为 success
    """
    export_tasks_total.labels(status=status, format=format).inc()
    logger.debug(f"记录任务完成: 格式={format}, 状态={status}")


def record_export_task_failed(error_type: str, format: str) -> None:
    """
    记录导出任务失败。

    同时更新：
    1. 任务总数计数器（status=failed）
    2. 错误计数器（按错误类型）

    Args:
        error_type: 错误类型 (validation/generation/storage/timeout)
        format: 导出格式 (pdf/markdown/word)
    """
    export_tasks_total.labels(status="failed", format=format).inc()
    export_errors_total.labels(error_type=error_type).inc()
    logger.warning(
        f"记录任务失败: 格式={format}, 错误类型={error_type}"
    )


def increment_active_tasks() -> None:
    """增加活跃任务计数。"""
    export_tasks_active.inc()
    logger.debug("活跃任务计数 +1")


def decrement_active_tasks() -> None:
    """减少活跃任务计数。"""
    export_tasks_active.dec()
    logger.debug("活跃任务计数 -1")


def set_queued_tasks(count: int) -> None:
    """
    设置排队任务数。

    Args:
        count: 排队任务数量
    """
    export_tasks_queued.set(count)
    logger.debug(f"排队任务数设置为: {count}")


def update_storage_metrics(
    used_bytes: int,
    available_bytes: int
) -> None:
    """
    更新存储使用指标。

    Args:
        used_bytes: 已使用存储（字节）
        available_bytes: 可用存储（字节）
    """
    export_storage_bytes.labels(type="used").set(used_bytes)
    export_storage_bytes.labels(type="available").set(available_bytes)
    logger.debug(
        f"存储指标更新: 已用={used_bytes}字节, 可用={available_bytes}字节"
    )
