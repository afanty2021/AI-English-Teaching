"""
导出任务模型测试
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import MagicMock

from app.models.export_task import ExportTask, TaskStatus, ExportFormat


class TestTaskStatus:
    """任务状态枚举测试"""

    def test_task_status_values(self):
        """测试任务状态枚举值"""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.PROCESSING == "processing"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"

    def test_task_status_all_values(self):
        """测试所有任务状态"""
        expected = ["pending", "processing", "completed", "failed", "cancelled"]
        actual = [status.value for status in TaskStatus]
        assert actual == expected


class TestExportFormat:
    """导出格式枚举测试"""

    def test_export_format_values(self):
        """测试导出格式枚举值"""
        assert ExportFormat.WORD == "word"
        assert ExportFormat.PDF == "pdf"
        assert ExportFormat.PPTX == "pptx"
        assert ExportFormat.MARKDOWN == "markdown"

    def test_export_format_all_values(self):
        """测试所有导出格式"""
        expected = ["word", "pdf", "pptx", "markdown"]
        actual = [fmt.value for fmt in ExportFormat]
        assert actual == expected


class TestExportTask:
    """导出任务模型测试"""

    def test_task_creation(self):
        """测试任务创建"""
        task = ExportTask(
            id=uuid.uuid4(),
            lesson_id=uuid.uuid4(),
            created_by=uuid.uuid4(),
            format=ExportFormat.WORD.value,
            status=TaskStatus.PENDING.value,
            options={"sections": ["overview", "objectives"]}
        )

        assert task.format == "word"
        assert task.status == "pending"
        assert task.progress == 0
        assert task.options == {"sections": ["overview", "objectives"]}

    def test_task_default_values(self):
        """测试任务默认值"""
        task = ExportTask(
            lesson_id=uuid.uuid4(),
            created_by=uuid.uuid4(),
            format=ExportFormat.PDF.value
        )

        assert task.status == "pending"
        assert task.progress == 0
        assert task.template_id is None
        assert task.file_path is None
        assert task.error_message is None

    def test_is_pending_property(self):
        """测试 is_pending 属性"""
        task = ExportTask(
            lesson_id=uuid.uuid4(),
            created_by=uuid.uuid4(),
            format=ExportFormat.WORD.value,
            status=TaskStatus.PENDING.value
        )
        assert task.is_pending is True

        task.status = TaskStatus.PROCESSING.value
        assert task.is_pending is False

    def test_is_processing_property(self):
        """测试 is_processing 属性"""
        task = ExportTask(
            lesson_id=uuid.uuid4(),
            created_by=uuid.uuid4(),
            format=ExportFormat.WORD.value,
            status=TaskStatus.PROCESSING.value
        )
        assert task.is_processing is True

        task.status = TaskStatus.COMPLETED.value
        assert task.is_processing is False

    def test_is_completed_property(self):
        """测试 is_completed 属性"""
        task = ExportTask(
            lesson_id=uuid.uuid4(),
            created_by=uuid.uuid4(),
            format=ExportFormat.WORD.value,
            status=TaskStatus.COMPLETED.value
        )
        assert task.is_completed is True

        task.status = TaskStatus.FAILED.value
        assert task.is_completed is False

    def test_is_failed_property(self):
        """测试 is_failed 属性"""
        task = ExportTask(
            lesson_id=uuid.uuid4(),
            created_by=uuid.uuid4(),
            format=ExportFormat.WORD.value,
            status=TaskStatus.FAILED.value,
            error_message="Test error"
        )
        assert task.is_failed is True
        assert task.error_message == "Test error"

    def test_is_terminal_property(self):
        """测试 is_terminal 属性"""
        task = ExportTask(
            lesson_id=uuid.uuid4(),
            created_by=uuid.uuid4(),
            format=ExportFormat.WORD.value
        )

        # Pending 不是终态
        assert task.is_terminal is False

        # Processing 不是终态
        task.status = TaskStatus.PROCESSING.value
        assert task.is_terminal is False

        # Completed 是终态
        task.status = TaskStatus.COMPLETED.value
        assert task.is_terminal is True

        # Failed 是终态
        task.status = TaskStatus.FAILED.value
        assert task.is_terminal is True

        # Cancelled 是终态
        task.status = TaskStatus.CANCELLED.value
        assert task.is_terminal is True

    def test_repr(self):
        """测试 __repr__ 方法"""
        task_id = uuid.uuid4()
        task = ExportTask(
            id=task_id,
            lesson_id=uuid.uuid4(),
            created_by=uuid.uuid4(),
            format=ExportFormat.PDF.value,
            status=TaskStatus.PENDING.value
        )

        repr_str = repr(task)
        assert "ExportTask" in repr_str
        assert str(task_id) in repr_str
        assert "pdf" in repr_str
        assert "pending" in repr_str


class TestExportTaskRelationships:
    """导出任务关系测试"""

    def test_lesson_relationship(self):
        """测试与教案的关系"""
        lesson_id = uuid.uuid4()
        task = ExportTask(
            lesson_id=lesson_id,
            created_by=uuid.uuid4(),
            format=ExportFormat.WORD.value
        )

        # 验证关系字段存在
        assert hasattr(task, 'lesson')
        assert hasattr(task, 'lesson_id')
        assert task.lesson_id == lesson_id

    def test_template_relationship(self):
        """测试与模板的关系"""
        template_id = uuid.uuid4()
        task = ExportTask(
            lesson_id=uuid.uuid4(),
            template_id=template_id,
            created_by=uuid.uuid4(),
            format=ExportFormat.WORD.value
        )

        # 验证关系字段存在
        assert hasattr(task, 'template')
        assert task.template_id == template_id

    def test_creator_relationship(self):
        """测试与创建者的关系"""
        user_id = uuid.uuid4()
        task = ExportTask(
            lesson_id=uuid.uuid4(),
            created_by=user_id,
            format=ExportFormat.WORD.value
        )

        # 验证关系字段存在
        assert hasattr(task, 'creator')
        assert task.created_by == user_id
