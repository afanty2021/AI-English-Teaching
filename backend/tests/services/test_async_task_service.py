"""
异步任务服务测试

测试 AsyncTaskService 的核心业务逻辑：
- 创建异步任务
- 更新任务状态
- 获取任务结果
- 任务失败处理
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import AsyncTaskStatus
from app.services.async_task_service import AsyncTaskService, get_async_task_service


class TestAsyncTaskService:
    """异步任务服务测试类"""

    @pytest.fixture
    def db_session(self):
        """模拟数据库会话"""
        session = AsyncMock()
        session.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None))),
            scalar=MagicMock(return_value=None),
        )
        session.commit = MagicMock()
        session.refresh = MagicMock()
        session.rollback = MagicMock()
        return session

    @pytest.fixture
    def async_task_service(self, db_session):
        """创建异步任务服务实例"""
        return AsyncTaskService(db_session)

    @pytest.fixture
    def sample_user_id(self):
        """示例用户ID"""
        return uuid.uuid4()

    @pytest.mark.asyncio
    async def test_create_task_success(self, async_task_service, sample_user_id):
        """测试成功创建异步任务"""
        # 准备测试数据
        task_type = "pdf_export"
        task_params = {"format": "pdf", "include_answers": True}

        # 模拟数据库保存
        mock_task = MagicMock()
        mock_task.id = uuid.uuid4()
        mock_task.user_id = sample_user_id
        mock_task.task_type = task_type
        mock_task.status = AsyncTaskStatus.PENDING.value
        async_task_service.db.add.return_value = mock_task

        # 执行测试
        result = await async_task_service.create_task(
            user_id=sample_user_id,
            task_type=task_type,
            params=task_params
        )

        # 验证结果
        assert result is not None
        assert result.user_id == sample_user_id
        assert result.task_type == task_type
        assert result.status == AsyncTaskStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_update_task_status_to_processing(self, async_task_service, sample_user_id):
        """测试更新任务状态为处理中"""
        task_id = uuid.uuid4()

        # 模拟数据库查询返回任务
        mock_task = MagicMock()
        mock_task.id = task_id
        mock_task.user_id = sample_user_id
        mock_task.status = AsyncTaskStatus.PENDING.value
        async_task_service.db.execute.return_value.scalar.return_value = mock_task

        # 执行测试
        result = await async_task_service.update_task_status(
            task_id=task_id,
            user_id=sample_user_id,
            new_status=AsyncTaskStatus.PROCESSING
        )

        # 验证结果
        assert result is not None
        assert result.status == AsyncTaskStatus.PROCESSING.value
        assert result.updated_at is not None

    @pytest.mark.asyncio
    async def test_update_task_status_to_completed(self, async_task_service, sample_user_id):
        """测试更新任务状态为已完成"""
        task_id = uuid.uuid4()
        result_data = {"url": "https://example.com/export.pdf"}

        # 模拟数据库查询返回任务
        mock_task = MagicMock()
        mock_task.id = task_id
        mock_task.user_id = sample_user_id
        mock_task.status = AsyncTaskStatus.PROCESSING.value
        async_task_service.db.execute.return_value.scalar.return_value = mock_task

        # 执行测试
        result = await async_task_service.update_task_status(
            task_id=task_id,
            user_id=sample_user_id,
            new_status=AsyncTaskStatus.COMPLETED,
            result_data=result_data
        )

        # 验证结果
        assert result is not None
        assert result.status == AsyncTaskStatus.COMPLETED.value
        assert result.result == result_data

    @pytest.mark.asyncio
    async def test_update_task_status_to_failed(self, async_task_service, sample_user_id):
        """测试更新任务状态为失败"""
        task_id = uuid.uuid4()
        error_message = "Export failed: invalid data format"

        # 模拟数据库查询返回任务
        mock_task = MagicMock()
        mock_task.id = task_id
        mock_task.user_id = sample_user_id
        async_task_service.db.execute.return_value.scalar.return_value = mock_task

        # 执行测试
        result = await async_task_service.update_task_status(
            task_id=task_id,
            user_id=sample_user_id,
            new_status=AsyncTaskStatus.FAILED,
            error_message=error_message
        )

        # 验证结果
        assert result is not None
        assert result.status == AsyncTaskStatus.FAILED.value
        assert result.error == error_message

    @pytest.mark.asyncio
    async def test_get_task_success(self, async_task_service, sample_user_id):
        """测试获取任务成功"""
        task_id = uuid.uuid4()

        # 模拟数据库查询返回任务
        mock_task = MagicMock()
        mock_task.id = task_id
        mock_task.user_id = sample_user_id
        mock_task.status = AsyncTaskStatus.COMPLETED.value
        mock_task.result = {"url": "https://example.com/file.pdf"}
        mock_task.progress = 100
        async_task_service.db.execute.return_value.scalar.return_value = mock_task

        # 执行测试
        result = await async_task_service.get_task(
            task_id=task_id,
            user_id=sample_user_id
        )

        # 验证结果
        assert result is not None
        assert result.id == task_id
        assert result.status == AsyncTaskStatus.COMPLETED.value
        assert result.progress == 100

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, async_task_service, sample_user_id):
        """测试获取不存在的任务"""
        task_id = uuid.uuid4()

        # 模拟数据库查询返回None
        async_task_service.db.execute.return_value.scalar.return_value = None

        # 执行测试
        result = await async_task_service.get_task(
            task_id=task_id,
            user_id=sample_user_id
        )

        # 验证结果
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_tasks(self, async_task_service, sample_user_id):
        """测试获取用户的任务列表"""
        # 模拟数据库查询返回任务列表
        mock_tasks = [
            MagicMock(
                id=uuid.uuid4(),
                task_type="pdf_export",
                status=AsyncTaskStatus.COMPLETED.value,
                created_at=datetime.utcnow()
            ),
            MagicMock(
                id=uuid.uuid4(),
                task_type="report_generation",
                status=AsyncTaskStatus.PROCESSING.value,
                created_at=datetime.utcnow()
            ),
        ]

        async_task_service.db.execute.return_value.scalars.return_value.all.return_value = mock_tasks

        # 执行测试
        tasks = await async_task_service.get_user_tasks(
            user_id=sample_user_id,
            limit=10
        )

        # 验证结果
        assert tasks is not None
        assert len(tasks) == 2
        assert tasks[0].task_type == "pdf_export"
        assert tasks[1].status == AsyncTaskStatus.PROCESSING.value

    @pytest.mark.asyncio
    async def test_update_task_progress(self, async_task_service, sample_user_id):
        """测试更新任务进度"""
        task_id = uuid.uuid4()
        progress = 50
        status_message = "Processing page 2 of 4"

        # 模拟数据库查询返回任务
        mock_task = MagicMock()
        mock_task.id = task_id
        mock_task.user_id = sample_user_id
        async_task_service.db.execute.return_value.scalar.return_value = mock_task

        # 执行测试
        result = await async_task_service.update_task_progress(
            task_id=task_id,
            user_id=sample_user_id,
            progress=progress,
            status_message=status_message
        )

        # 验证结果
        assert result is not None
        assert result.progress == progress
        assert result.status_message == status_message

    @pytest.mark.asyncio
    async def test_cleanup_old_tasks(self, async_task_service):
        """测试清理旧任务"""
        days_threshold = 30

        # 模拟数据库删除操作
        async_task_service.db.execute.return_value.rowcount = 5

        # 执行测试
        deleted_count = await async_task_service.cleanup_old_tasks(
            days_threshold=days_threshold
        )

        # 验证结果
        assert deleted_count == 5


class TestGetAsyncTaskService:
    """测试 get_async_task_service 工厂函数"""

    def test_get_async_task_service_returns_service(self):
        """测试 get_async_task_service 返回正确的服务实例"""
        mock_db = MagicMock()
        service = get_async_task_service(mock_db)

        assert service is not None
        assert isinstance(service, AsyncTaskService)
        assert service.db == mock_db
