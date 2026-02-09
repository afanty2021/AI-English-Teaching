"""
并发控制工具模块测试

测试 ExportConcurrencyController 的功能：
- 初始化和配置
- 槽位获取和释放
- 并发限制
- 超时处理
- 统计信息
"""

import asyncio
import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import get_settings
from app.utils.concurrency import (
    ExportConcurrencyController,
    get_export_concurrency_controller,
    reset_export_concurrency_controller,
    with_concurrency_control,
)


class TestExportConcurrencyController:
    """测试 ExportConcurrencyController 类"""

    def test_init_with_default_config(self):
        """测试使用默认配置初始化"""
        controller = ExportConcurrencyController()

        settings = get_settings()
        assert controller.max_concurrent == settings.MAX_CONCURRENT_EXPORTS
        assert controller.active_count == 0
        assert controller.available_slots == controller.max_concurrent
        assert not controller.is_full
        assert controller.completed_count == 0
        assert controller.rejected_count == 0

    def test_init_with_custom_config(self):
        """测试使用自定义配置初始化"""
        controller = ExportConcurrencyController(max_concurrent=3)

        assert controller.max_concurrent == 3
        assert controller.available_slots == 3

    def test_get_status(self):
        """测试获取控制器状态"""
        controller = ExportConcurrencyController(max_concurrent=5)

        status = controller.get_status()

        assert status["max_concurrent"] == 5
        assert status["active_count"] == 0
        assert status["available_slots"] == 5
        assert status["is_full"] is False
        assert status["completed_count"] == 0
        assert status["rejected_count"] == 0
        assert status["utilization"] == "0.0%"

    @pytest.mark.asyncio
    async def test_acquire_and_release_slot(self):
        """测试槽位获取和释放"""
        controller = ExportConcurrencyController(max_concurrent=2)

        # 获取第一个槽位
        task_id = str(uuid.uuid4())
        acquired = await controller.acquire_slot(task_id)

        assert acquired is True
        assert controller.active_count == 1
        assert controller.available_slots == 1
        assert not controller.is_full

        # 释放槽位
        controller.release_slot(task_id)

        assert controller.active_count == 0
        assert controller.available_slots == 2
        assert controller.completed_count == 1

    @pytest.mark.asyncio
    async def test_acquire_slot_without_task_id(self):
        """测试不带任务ID获取槽位"""
        controller = ExportConcurrencyController(max_concurrent=2)

        acquired = await controller.acquire_slot()

        assert acquired is True
        assert controller.active_count == 0  # 没有task_id时不计入active_tasks

        controller.release_slot()
        # 没有task_id时不计入completed_count
        assert controller.completed_count == 0

    @pytest.mark.asyncio
    async def test_context_manager_acquire(self):
        """测试使用上下文管理器获取槽位"""
        controller = ExportConcurrencyController(max_concurrent=2)

        task_id = str(uuid.uuid4())

        async with controller.acquire(task_id) as acquired:
            assert acquired is True
            assert controller.active_count == 1

        # 退出上下文后槽位应该释放
        assert controller.active_count == 0
        assert controller.completed_count == 1

    @pytest.mark.asyncio
    async def test_context_manager_timeout(self):
        """测试上下文管理器超时"""
        controller = ExportConcurrencyController(max_concurrent=1)

        # 获取唯一的槽位
        task_id_1 = str(uuid.uuid4())
        await controller.acquire_slot(task_id_1)

        # 尝试获取第二个槽位（应该超时）
        task_id_2 = str(uuid.uuid4())
        async with controller.acquire(task_id_2, timeout=0.1) as acquired:
            assert acquired is False
            assert controller.rejected_count == 1

    @pytest.mark.asyncio
    async def test_concurrent_limit_enforcement(self):
        """测试并发限制是否生效"""
        controller = ExportConcurrencyController(max_concurrent=3)

        active_tasks = []
        task_ids = [str(uuid.uuid4()) for _ in range(5)]

        # 用于跟踪哪些任务正在执行
        executing = set()

        async def mock_task(task_id: str, delay: float = 0.1):
            """模拟一个耗时任务"""
            async with controller.acquire(task_id) as acquired:
                if acquired:
                    executing.add(task_id)
                    # 验证并发限制
                    assert len(executing) <= 3, "并发限制未生效"
                    await asyncio.sleep(delay)
                    executing.remove(task_id)
                    return True
                return False

        # 启动5个任务，但只有3个能同时执行
        results = await asyncio.gather(*[mock_task(tid) for tid in task_ids])

        # 所有任务都应该完成
        assert all(results)
        assert controller.completed_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_limit_with_gather(self):
        """测试使用 asyncio.gather 的并发控制"""
        controller = ExportConcurrencyController(max_concurrent=2)

        execution_log = []

        async def mock_task(task_id: str, duration: float):
            """模拟任务并记录执行时间"""
            start_time = time.time()
            async with controller.acquire(task_id) as acquired:
                if acquired:
                    execution_log.append(
                        {"task": task_id, "start": start_time, "status": "started"}
                    )
                    await asyncio.sleep(duration)
                    execution_log.append(
                        {"task": task_id, "end": time.time(), "status": "completed"}
                    )

        # 启动4个任务，每个耗时0.1秒
        task_ids = [str(uuid.uuid4()) for _ in range(4)]
        await asyncio.gather(*[mock_task(tid, 0.1) for tid in task_ids])

        # 验证执行顺序：前2个应该先开始
        started_tasks = [log for log in execution_log if log["status"] == "started"]
        assert len(started_tasks) == 4

        # 验证并发限制：分析任务开始时间
        # 找出最先开始的两个任务（应该在几乎同一时间开始）
        started_tasks_sorted = sorted(started_tasks, key=lambda x: x["start"])

        # 前两个任务应该几乎同时开始（时间差<0.1秒）
        first_batch_time_diff = started_tasks_sorted[1]["start"] - started_tasks_sorted[0]["start"]
        assert first_batch_time_diff < 0.1, "前两个任务应该几乎同时开始"

        # 第三和第四个任务应该在前两个完成后才开始
        # 所以它们的开始时间应该接近前两个任务的结束时间
        # 每个任务耗时0.1秒，所以第三/四个任务应该在约0.1秒后开始
        third_task_start = started_tasks_sorted[2]["start"]
        first_task_end = next(
            log["end"] for log in execution_log
            if log["task"] == started_tasks_sorted[0]["task"] and log["status"] == "completed"
        )

        time_diff = third_task_start - first_task_end
        assert time_diff < 0.1, "第三个任务应该在前两个任务完成后立即开始"

    @pytest.mark.asyncio
    async def test_wait_for_available_slot(self):
        """测试等待可用槽位"""
        controller = ExportConcurrencyController(max_concurrent=1)

        # 获取唯一的槽位
        task_id_1 = str(uuid.uuid4())
        await controller.acquire_slot(task_id_1)

        # 在另一个协程中等待槽位
        wait_task = asyncio.create_task(
            controller.wait_for_available_slot(timeout=1.0)
        )

        # 等待一小段时间确保wait_task开始等待
        await asyncio.sleep(0.05)

        # 释放槽位
        controller.release_slot(task_id_1)

        # wait_task应该完成
        result = await wait_task
        assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_available_slot_timeout(self):
        """测试等待可用槽位超时"""
        controller = ExportConcurrencyController(max_concurrent=1)

        # 获取唯一的槽位
        task_id_1 = str(uuid.uuid4())
        await controller.acquire_slot(task_id_1)

        # 等待槽位（应该超时）
        result = await controller.wait_for_available_slot(timeout=0.1)

        assert result is False

    def test_reject_task(self):
        """测试拒绝任务"""
        controller = ExportConcurrencyController()

        task_id = str(uuid.uuid4())
        controller.reject_task(task_id)

        assert controller.rejected_count == 1

    def test_reset_statistics(self):
        """测试重置统计信息"""
        controller = ExportConcurrencyController()

        # 添加一些统计
        controller._completed_count = 10
        controller._rejected_count = 2

        controller.reset_statistics()

        assert controller.completed_count == 0
        assert controller.rejected_count == 0


class TestGlobalController:
    """测试全局并发控制器单例"""

    @pytest.mark.asyncio
    async def test_get_singleton(self):
        """测试获取全局单例"""
        # 重置控制器
        reset_export_concurrency_controller()

        controller1 = get_export_concurrency_controller()
        controller2 = get_export_concurrency_controller()

        # 应该是同一个实例
        assert controller1 is controller2

    @pytest.mark.asyncio
    async def test_reset_controller(self):
        """测试重置控制器"""
        # 获取控制器并修改状态
        controller1 = get_export_concurrency_controller()
        controller1._completed_count = 10

        # 重置
        new_controller = reset_export_concurrency_controller()

        # 应该是新实例
        assert new_controller is not controller1
        assert new_controller.completed_count == 0


class TestWithConcurrencyControl:
    """测试并发控制便捷函数"""

    @pytest.mark.asyncio
    async def test_with_concurrency_control(self):
        """测试便捷函数"""
        task_id = str(uuid.uuid4())

        async with with_concurrency_control(task_id=task_id) as acquired:
            assert acquired is True

            controller = get_export_concurrency_controller()
            assert controller.active_count == 1

        # 退出后应该释放
        controller = get_export_concurrency_controller()
        assert controller.active_count == 0

    @pytest.mark.asyncio
    async def test_with_custom_controller(self):
        """测试使用自定义控制器"""
        custom_controller = ExportConcurrencyController(max_concurrent=1)
        task_id = str(uuid.uuid4())

        async with with_concurrency_control(
            task_id=task_id, controller=custom_controller
        ) as acquired:
            assert acquired is True
            assert custom_controller.active_count == 1


class TestConcurrencyIntegration:
    """集成测试：并发控制器在真实场景中的表现"""

    @pytest.mark.asyncio
    async def test_sequential_task_processing(self):
        """测试顺序任务处理"""
        controller = ExportConcurrencyController(max_concurrent=2)

        results = []

        async def process_task(task_id: str, value: int):
            """模拟处理任务"""
            async with controller.acquire(task_id) as acquired:
                if acquired:
                    await asyncio.sleep(0.05)
                    results.append(value)
                    return True
                return False

        # 顺序处理4个任务
        task_ids = [str(uuid.uuid4()) for _ in range(4)]
        await asyncio.gather(*[process_task(tid, i) for i, tid in enumerate(task_ids)])

        # 所有任务都应该完成
        assert len(results) == 4
        assert controller.completed_count == 4

    @pytest.mark.asyncio
    async def test_rapid_task_submission(self):
        """测试快速提交大量任务"""
        controller = ExportConcurrencyController(max_concurrent=3)

        completed = []

        async def quick_task(task_id: str):
            """快速任务"""
            async with controller.acquire(task_id) as acquired:
                if acquired:
                    await asyncio.sleep(0.01)
                    completed.append(task_id)

        # 快速提交20个任务
        task_ids = [str(uuid.uuid4()) for _ in range(20)]
        await asyncio.gather(*[quick_task(tid) for tid in task_ids])

        # 验证所有任务都完成
        assert len(completed) == 20
        assert controller.completed_count == 20

    @pytest.mark.asyncio
    async def test_task_with_different_durations(self):
        """测试不同持续时间的任务"""
        controller = ExportConcurrencyController(max_concurrent=2)

        durations = [0.05, 0.1, 0.02, 0.08]
        task_ids = [str(uuid.uuid4()) for _ in durations]

        async def variable_task(task_id: str, duration: float):
            """不同持续时间的任务"""
            start_time = time.time()
            async with controller.acquire(task_id) as acquired:
                if acquired:
                    await asyncio.sleep(duration)
                    return time.time() - start_time
            return 0

        results = await asyncio.gather(
            *[variable_task(tid, dur) for tid, dur in zip(task_ids, durations)]
        )

        # 验证所有任务都完成
        assert all(r > 0 for r in results)
        assert controller.completed_count == 4

        # 验证执行时间合理（考虑并发限制）
        # 前2个任务应该几乎同时开始，总时间应该接近最长的任务
        total_time = max(results) + min(results)
        assert total_time < sum(durations), "并发控制没有减少总执行时间"


class TestConcurrencyEdgeCases:
    """边界情况测试"""

    @pytest.mark.asyncio
    async def test_release_without_acquire(self):
        """测试未获取就释放（应该不影响计数器）"""
        controller = ExportConcurrencyController(max_concurrent=2)

        # 直接释放（未获取）
        controller.release_slot(str(uuid.uuid4()))

        # 信号量内部计数器会增加（这是asyncio.Semaphore的行为）
        # 但active_count应该还是0
        assert controller.active_count == 0

    @pytest.mark.asyncio
    async def test_multiple_releases(self):
        """测试多次释放同一个槽位"""
        controller = ExportConcurrencyController(max_concurrent=2)

        task_id = str(uuid.uuid4())
        await controller.acquire_slot(task_id)

        # 第一次释放
        controller.release_slot(task_id)
        assert controller.active_count == 0

        # 第二次释放（应该只是减少active_tasks，不会变成负数）
        controller.release_slot(task_id)
        assert controller.active_count == 0

    @pytest.mark.asyncio
    async def test_zero_timeout(self):
        """测试零超时（立即失败）"""
        controller = ExportConcurrencyController(max_concurrent=1)

        # 获取槽位
        await controller.acquire_slot(str(uuid.uuid4()))

        # 尝试获取第二个槽位，超时为0
        result = await controller.wait_for_available_slot(timeout=0)

        assert result is False

    @pytest.mark.asyncio
    async def test_task_cancellation(self):
        """测试任务取消时的槽位释放"""
        controller = ExportConcurrencyController(max_concurrent=1)

        task_id = str(uuid.uuid4())

        async def cancellable_task():
            """可取消的任务"""
            async with controller.acquire(task_id) as acquired:
                if acquired:
                    await asyncio.sleep(0.5)
                    return True
            return False

        # 启动任务
        task = asyncio.create_task(cancellable_task())

        # 等待任务获取槽位
        await asyncio.sleep(0.05)

        # 取消任务
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        # 槽位应该被释放（上下文管理器的__aexit__会被调用）
        assert controller.active_count == 0
