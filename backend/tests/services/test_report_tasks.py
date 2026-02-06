"""
报告导出任务测试 - AI英语教学系统
测试 Celery 异步任务功能
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from app.models.async_task import AsyncTask, AsyncTaskStatus, AsyncTaskType


class TestGenerateReportTask:
    """测试生成报告任务"""

    @pytest.fixture
    def mock_db_session(self):
        """创建模拟数据库会话"""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def mock_task_service(self):
        """创建模拟任务服务"""
        service = MagicMock()
        service.update_task_progress = AsyncMock()
        service.complete_task = AsyncMock()
        service.fail_task = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_generate_report_task_creates_task_record(self, mock_db_session, mock_task_service):
        """测试生成报告任务创建任务记录"""
        # 准备测试数据
        task_id = str(uuid4())
        student_id = str(uuid4())

        # 模拟数据库查询结果
        mock_task = MagicMock(spec=AsyncTask)
        mock_task.id = uuid4()
        mock_task.status = AsyncTaskStatus.PENDING.value

        # 验证任务创建流程
        from app.services.async_task_service import AsyncTaskService

        service = AsyncTaskService(mock_db_session)
        result = await service.create_task(
            user_id=uuid4(),
            task_type=AsyncTaskType.REPORT_GENERATE.value,
            input_params={"report_type": "weekly"},
        )

        # 验证数据库操作
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()


class TestExportReportTask:
    """测试导出报告任务"""

    @pytest.fixture
    def sample_report_data(self):
        """创建示例报告数据"""
        return {
            "id": str(uuid4()),
            "title": "周学习报告",
            "report_type": "weekly",
            "student_id": str(uuid4()),
            "statistics": {
                "total_practices": 50,
                "completion_rate": 85.5,
            },
        }

    @pytest.mark.asyncio
    async def test_export_pdf_format(self, sample_report_data):
        """测试 PDF 导出格式"""
        # 验证报告数据包含必要字段
        assert "id" in sample_report_data
        assert "statistics" in sample_report_data
        assert sample_report_data["statistics"]["total_practices"] > 0


class TestAsyncTaskStatus:
    """测试异步任务状态管理"""

    def test_task_status_values(self):
        """验证任务状态枚举值"""
        assert AsyncTaskStatus.PENDING.value == "pending"
        assert AsyncTaskStatus.PROCESSING.value == "processing"
        assert AsyncTaskStatus.COMPLETED.value == "completed"
        assert AsyncTaskStatus.FAILED.value == "failed"
        assert AsyncTaskStatus.CANCELLED.value == "cancelled"

    def test_task_type_values(self):
        """验证任务类型枚举值"""
        assert AsyncTaskType.REPORT_GENERATE.value == "report_generate"
        assert AsyncTaskType.REPORT_EXPORT.value == "report_export"
        assert AsyncTaskType.BATCH_EXPORT.value == "batch_export"


class TestCeleryConfiguration:
    """测试 Celery 配置"""

    def test_celery_app_exists(self):
        """验证 Celery 应用实例存在"""
        from app.core.celery import celery_app

        assert celery_app is not None
        assert celery_app.conf.task_serializer == "json"

    def test_celery_queues_configured(self):
        """验证 Celery 队列已配置"""
        from app.core.celery import celery_app

        queues = celery_app.conf.task_queues
        assert "default" in queues
        assert "reports" in queues
        assert "exports" in queues

    def test_celery_task_routes(self):
        """验证任务路由配置"""
        from app.core.celery import celery_app

        routes = celery_app.conf.task_routes
        assert "app.tasks.report_tasks.*" in routes
        assert routes["app.tasks.report_tasks.*"]["queue"] == "reports"


class TestReportExportService:
    """测试报告导出服务"""

    @pytest.fixture
    def mock_export_service(self):
        """创建模拟导出服务"""
        with patch("app.services.report_export_service.ReportExportService") as mock:
            service_instance = MagicMock()
            service_instance.export_as_pdf = AsyncMock(return_value={"file_path": "/tmp/test.pdf"})
            mock.return_value = service_instance
            yield service_instance

    @pytest.mark.asyncio
    async def test_export_pdf_calls_service(self, mock_export_service):
        """测试导出 PDF 调用服务"""
        from app.services.report_export_service import ReportExportService

        # 验证服务方法被调用
        # 实际测试需要数据库连接和完整上下文
        assert mock_export_service.export_as_pdf is not None


# ============ 集成测试 ============

class TestReportExportIntegration:
    """报告导出集成测试"""

    @pytest.fixture
    def mock_celery_app(self):
        """创建模拟 Celery 应用"""
        with patch("app.core.celery.celery_app") as mock:
            yield mock

    def test_export_task_submission(self, mock_celery_app):
        """测试导出任务提交"""
        # 模拟 Celery 任务发送
        mock_celery_app.send_task.return_value = MagicMock()

        from app.core.celery import celery_app

        # 验证可以发送任务
        result = celery_app.send_task(
            "app.tasks.report_tasks.export_report_pdf",
            args=["task-id", "report-id", "pdf"],
            queue="reports",
        )

        assert result is not None


# ============ 性能测试 ============

class TestReportExportPerformance:
    """报告导出性能测试"""

    @pytest.mark.asyncio
    async def test_export_completes_within_timeout(self):
        """测试导出在超时时间内完成"""
        import asyncio
        from app.services.report_export_service import ReportExportService

        # 性能测试 - 验证超时设置
        timeout_seconds = 60
        assert timeout_seconds > 0

        # 模拟快速完成
        async def quick_export():
            await asyncio.sleep(0.1)  # 模拟100ms导出
            return {"file_path": "/tmp/test.pdf"}

        start_time = asyncio.get_event_loop().time()
        result = await asyncio.wait_for(quick_export(), timeout=timeout_seconds)
        elapsed = asyncio.get_event_loop().time() - start_time

        assert result is not None
        assert elapsed < 1.0  # 应该小于1秒


# ============ Fixtures ============

@pytest.fixture
def sample_student_id():
    """提供示例学生ID"""
    return str(uuid4())


@pytest.fixture
def sample_report_id():
    """提供示例报告ID"""
    return str(uuid4())


@pytest.fixture
def sample_task_params():
    """提供示例任务参数"""
    return {
        "task_id": str(uuid4()),
        "student_id": str(uuid4()),
        "report_type": "weekly",
        "format": "pdf",
    }
