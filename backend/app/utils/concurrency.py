"""
并发控制工具模块

提供导出任务的并发控制机制，使用 asyncio.Semaphore 限制同时执行的任务数量。
确保系统资源不被耗尽，特别是对于 CPU 密集型的文档生成操作。
"""
import asyncio
import logging
from typing import Optional

from app.core.config import get_settings
from app.metrics import set_queued_tasks

logger = logging.getLogger(__name__)


class ExportConcurrencyController:
    """
    导出任务并发控制器

    使用 asyncio.Semaphore 实现导出任务的并发控制：
    - 限制同时处理的导出任务数量
    - 任务按请求顺序排队（FIFO）
    - 提供：队列状态查询、等待任务统计

    使用示例：
        ```python
        controller = ExportConcurrencyController()

        async with controller.acquire():
            # 执行导出任务
            await process_export_task(...)
        ```

    线程安全：此控制器设计为单例模式，在事件循环中共享。
    """

    def __init__(self, max_concurrent: Optional[int] = None):
        """
        初始化并发控制器

        Args:
            max_concurrent: 最大并发数（默认从配置读取）
        """
        settings = get_settings()
        self._max_concurrent = max_concurrent or settings.MAX_CONCURRENT_EXPORTS

        # 创建信号量（内部计数器，最大值为 max_concurrent）
        self._semaphore = asyncio.Semaphore(self._max_concurrent)

        # 统计信息
        self._active_tasks: set[str] = set()
        self._completed_count: int = 0
        self._rejected_count: int = 0

        logger.info(
            f"导出并发控制器初始化完成: max_concurrent={self._max_concurrent}"
        )

    @property
    def max_concurrent(self) -> int:
        """获取最大并发数"""
        return self._max_concurrent

    @property
    def active_count(self) -> int:
        """当前活动任务数"""
        return len(self._active_tasks)

    @property
    def available_slots(self) -> int:
        """可用槽位数"""
        return self._max_concurrent - self.active_count

    @property
    def is_full(self) -> bool:
        """是否已满载（所有槽位被占用）"""
        return self.available_slots == 0

    @property
    def completed_count(self) -> int:
        """已完成任务总数"""
        return self._completed_count

    @property
    def rejected_count(self) -> int:
        """被拒绝任务总数（超时或其他原因）"""
        return self._rejected_count

    def get_status(self) -> dict:
        """
        获取控制器状态

        Returns:
            dict: 包含并发控制状态的字典
        """
        return {
            "max_concurrent": self._max_concurrent,
            "active_count": self.active_count,
            "available_slots": self.available_slots,
            "is_full": self.is_full,
            "completed_count": self.completed_count,
            "rejected_count": self.rejected_count,
            "utilization": f"{(self.active_count / self._max_concurrent * 100):.1f}%",
        }

    def acquire(self, task_id: Optional[str] = None, timeout: Optional[float] = None):
        """
        获取并发槽位（上下文管理器）

        Args:
            task_id: 任务ID（可选，用于统计）
            timeout: 超时时间（秒），None表示无限等待

        Returns:
            异步上下文管理器

        Raises:
            asyncio.TimeoutError: 超时未获得槽位

        使用示例：
            ```python
            async with controller.acquire(task_id="task-123") as acquired:
                if acquired:
                    # 执行导出任务
                    await process_export_task(...)
            ```
        """
        return _AcquireContextManager(self, task_id, timeout)

    async def acquire_slot(self, task_id: Optional[str] = None) -> bool:
        """
        获取并发槽位（直接调用）

        尝试获取一个并发槽位。如果没有可用槽位，将等待直到有槽位释放。

        Args:
            task_id: 任务ID（可选，用于统计）

        Returns:
            bool: 是否成功获取槽位（通常为True，除非被取消）

        使用示例：
            ```python
            if await controller.acquire_slot(task_id="task-123"):
                try:
                    # 执行导出任务
                    await process_export_task(...)
                finally:
                    controller.release_slot(task_id)
            ```
        """
        # 检查是否需要排队
        was_full = self.is_full
        if was_full:
            # 更新排队指标
            set_queued_tasks(1)

        # 等待获取信号量
        await self._semaphore.acquire()

        # 记录活动任务
        if task_id:
            self._active_tasks.add(task_id)

        # 如果之前是满的，现在获取到了槽位，更新排队指标
        if was_full:
            set_queued_tasks(0)

        logger.debug(
            f"导出任务获得槽位: task_id={task_id}, "
            f"active={self.active_count}/{self.max_concurrent}"
        )

        return True

    def release_slot(self, task_id: Optional[str] = None) -> None:
        """
        释放并发槽位

        Args:
            task_id: 任务ID（可选，用于统计）

        注意：
            必须在成功获取槽位后调用，否则会导致信号量计数器错误
        """
        # 从活动任务中移除并增加完成计数
        if task_id:
            self._active_tasks.discard(task_id)
            self._completed_count += 1

        # 释放信号量
        self._semaphore.release()

        logger.debug(
            f"导出任务释放槽位: task_id={task_id}, "
            f"active={self.active_count}/{self.max_concurrent}, "
            f"completed={self._completed_count}"
        )

    def reject_task(self, task_id: Optional[str] = None) -> None:
        """
        记录被拒绝的任务

        当任务超时或其他原因导致无法处理时调用。

        Args:
            task_id: 任务ID（可选）
        """
        self._rejected_count += 1
        logger.warning(f"导出任务被拒绝: task_id={task_id}, rejected={self._rejected_count}")

    async def wait_for_available_slot(self, timeout: Optional[float] = None) -> bool:
        """
        等待可用槽位

        Args:
            timeout: 超时时间（秒），None表示无限等待

        Returns:
            bool: 是否成功获得可用槽位

        Raises:
            asyncio.TimeoutError: 超时
        """
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=timeout)
            self._semaphore.release()  # 立即释放，只是检查
            return True
        except asyncio.TimeoutError:
            logger.warning(f"等待可用槽位超时: timeout={timeout}s")
            return False

    async def wait_for_all_completed(self, timeout: Optional[float] = None) -> bool:
        """
        等待所有活动任务完成

        Args:
            timeout: 超时时间（秒），None表示无限等待

        Returns:
            bool: 是否所有任务都已完成

        注意:
            这将阻塞直到所有活动任务完成，仅用于测试或维护
        """
        if self.active_count == 0:
            return True

        # 使用轮询方式等待
        start_time = asyncio.get_event_loop().time()

        while self.active_count > 0:
            if timeout is not None:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= timeout:
                    logger.warning(f"等待任务完成超时: remaining={self.active_count}")
                    return False
                remaining_timeout = timeout - elapsed
            else:
                remaining_timeout = 0.1  # 默认轮询间隔

            try:
                await asyncio.sleep(0.05)  # 短暂休眠避免忙等待
            except asyncio.CancelledError:
                logger.warning(f"等待任务完成被取消: remaining={self.active_count}")
                return False

        return True

    def reset_statistics(self) -> None:
        """
        重置统计信息

        用于测试或维护，清空计数器。
        注意：不影响当前活动任务。
        """
        self._completed_count = 0
        self._rejected_count = 0
        logger.info("导出并发控制器统计已重置")


class _AcquireContextManager:
    """
    异步上下文管理器（内部使用）

    支持异步 with 语法，自动获取和释放槽位。
    """

    def __init__(
        self,
        controller: ExportConcurrencyController,
        task_id: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        """
        初始化上下文管理器

        Args:
            controller: 并发控制器实例
            task_id: 任务ID（可选）
            timeout: 超时时间（秒）
        """
        self._controller = controller
        self._task_id = task_id
        self._timeout = timeout
        self._acquired = False

    async def __aenter__(self) -> bool:
        """进入上下文，获取槽位"""
        try:
            await asyncio.wait_for(
                self._controller._semaphore.acquire(),
                timeout=self._timeout
            )

            if self._task_id:
                self._controller._active_tasks.add(self._task_id)

            self._acquired = True
            return True

        except asyncio.TimeoutError:
            self._controller.reject_task(self._task_id)
            return False

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，释放槽位"""
        if self._acquired:
            if self._task_id:
                self._controller._active_tasks.discard(self._task_id)
                self._controller._completed_count += 1

            self._controller._semaphore.release()


# ==================== 全局单例 ====================

# 全局并发控制器实例
_concurrency_controller: Optional[ExportConcurrencyController] = None


def get_export_concurrency_controller() -> ExportConcurrencyController:
    """
    获取全局并发控制器单例

    Returns:
        ExportConcurrencyController: 并发控制器实例

    使用示例：
        ```python
        controller = get_export_concurrency_controller()

        async with controller.acquire(task_id="task-123"):
            # 执行导出任务
            await process_export_task(...)
        ```
    """
    global _concurrency_controller
    if _concurrency_controller is None:
        _concurrency_controller = ExportConcurrencyController()
    return _concurrency_controller


def reset_export_concurrency_controller() -> ExportConcurrencyController:
    """
    重置全局并发控制器

    主要用于测试，在生产环境中谨慎使用。

    Returns:
        ExportConcurrencyController: 新的并发控制器实例
    """
    global _concurrency_controller
    _concurrency_controller = ExportConcurrencyController()
    return _concurrency_controller


# ==================== 辅助函数 ====================

def with_concurrency_control(
    task_id: Optional[str] = None,
    timeout: Optional[float] = None,
    controller: Optional[ExportConcurrencyController] = None
):
    """
    并发控制上下文管理器（便捷函数）

    Args:
        task_id: 任务ID（可选）
        timeout: 超时时间（秒）
        controller: 并发控制器（可选，默认使用全局单例）

    Returns:
        异步上下文管理器

    使用示例：
        ```python
        async with with_concurrency_control(task_id="task-123"):
            # 执行导出任务
            await process_export_task(...)
        ```
    """
    if controller is None:
        controller = get_export_concurrency_controller()
    return controller.acquire(task_id, timeout)
