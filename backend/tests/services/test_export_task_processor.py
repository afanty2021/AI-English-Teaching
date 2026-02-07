"""
导出任务处理器测试 - AI英语教学系统

测试 ExportTaskProcessor 的完整功能：
- 完整导出流程（每种格式）
- 进度通知
- 错误处理
- 文件存储
- 任务状态更新
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.export_task import ExportFormat, ExportTask, TaskStatus
from app.models.export_template import ExportTemplate
from app.models.lesson_plan import LessonPlan
from app.services.export_task_processor import ExportTaskProcessor, get_export_task_processor


# ========== 测试夹具 ==========

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    # execute 将在测试中单独设置
    return db


@pytest.fixture
def mock_notifier():
    """模拟进度通知服务"""
    notifier = MagicMock()
    notifier.notify_progress = AsyncMock(return_value=True)
    notifier.notify_complete = AsyncMock(return_value=True)
    notifier.notify_error = AsyncMock(return_value=True)
    return notifier


@pytest.fixture
def mock_storage():
    """模拟文件存储服务"""
    storage = MagicMock()
    storage.save_file = AsyncMock(return_value=("/path/to/file.docx", 12345))
    return storage


@pytest.fixture
def sample_lesson_plan():
    """示例教案数据"""
    lesson = MagicMock(spec=LessonPlan)
    lesson.id = uuid.uuid4()
    lesson.title = "过去完成时教学"
    lesson.level = "B1"
    lesson.topic = "Grammar"
    lesson.duration = 45
    lesson.target_exam = "CET4"
    lesson.objectives = {
        "language_knowledge": ["掌握过去完成时的构成"],
        "language_skills": ["能够正确使用过去完成时"]
    }
    lesson.vocabulary = {
        "words": [
            {"word": "had done", "definition": "过去完成时", "example": "I had finished."}
        ]
    }
    lesson.grammar_points = {
        "points": [
            {
                "name": "过去完成时",
                "explanation": "表示在过去某时间之前已完成的动作",
                "examples": ["I had left when he arrived."]
            }
        ]
    }
    lesson.teaching_structure = {
        "stages": [
            {"name": "热身", "duration": 5, "activities": ["问候学生"]}
        ]
    }
    lesson.leveled_materials = {
        "basic": {"title": "基础阅读", "content": "简单内容..."}
    }
    lesson.exercises = {
        "items": [
            {
                "question": "选择正确形式",
                "options": ["A. had done", "B. have done"],
                "correct_answer": "A"
            }
        ]
    }
    lesson.ppt_outline = {
        "slides": [
            {"title": "过去完成时", "bullet_points": ["定义", "用法"]}
        ]
    }
    lesson.resources = {
        "links": ["https://example.com"]
    }
    lesson.teaching_notes = "注意学生容易混淆过去完成时和一般过去时"
    return lesson


@pytest.fixture
def sample_template():
    """示例模板数据"""
    template = MagicMock(spec=ExportTemplate)
    template.id = uuid.uuid4()
    template.name = "标准教案模板"
    template.format = ExportFormat.WORD.value
    template.template_path = "/templates/standard.docx"
    template.variables = [
        {"name": "teacher_name", "type": "text", "default": "教师"}
    ]
    template.increment_usage = Mock()
    return template


@pytest.fixture
def sample_task():
    """示例导出任务"""
    task = MagicMock()
    task.id = uuid.uuid4()
    task.status = TaskStatus.PENDING.value
    task.progress = 0
    task.error_message = None
    task.file_path = None
    task.file_size = None
    task.download_url = None
    task.started_at = None
    task.completed_at = None
    return task


@pytest.fixture
def processor(mock_db, mock_notifier, mock_storage):
    """创建处理器实例并注入模拟依赖"""
    with patch('app.services.export_task_processor.FileStorageService', return_value=mock_storage):
        with patch('app.services.export_task_processor.WordDocumentGenerator'):
            with patch('app.services.export_task_processor.PDFDocumentGenerator'):
                with patch('app.services.export_task_processor.PPTXDocumentGenerator'):
                    proc = ExportTaskProcessor(mock_db, mock_notifier)
                    proc.storage = mock_storage
                    return proc


def create_mock_result(value):
    """创建带有 scalar_one_or_none 的模拟结果对象"""
    result = Mock()
    result.scalar_one_or_none = Mock(return_value=value)
    return result


# ========== 核心功能测试 ==========

@pytest.mark.asyncio
async def test_process_export_task_word(processor, sample_task, sample_lesson_plan, mock_db):
    """测试处理Word格式导出任务"""

    # 设置数据库查询返回序列 - 使用 AsyncMock 和 side_effect
    def create_result(value):
        """创建带有 scalar_one_or_none 的结果对象"""
        result = Mock()
        result.scalar_one_or_none = Mock(return_value=value)
        return result

    # 模拟多次查询返回不同结果
    mock_db.execute = AsyncMock(side_effect=[
        create_result(sample_task),      # 第一次查询获取任务
        create_result(sample_lesson_plan),  # 第二次查询获取教案
        create_result(sample_task),      # 后续查询返回任务
    ])

    # 模拟生成器
    mock_word_gen = MagicMock()
    mock_word_gen.generate = Mock(return_value=b"fake word content")
    processor.word_generator = mock_word_gen

    # 模拟ContentRendererService
    with patch('app.services.export_task_processor.ContentRendererService') as mock_renderer:
        mock_renderer_instance = MagicMock()
        mock_renderer_instance.render_lesson_plan = Mock(return_value="# Test Content")
        mock_renderer.return_value = mock_renderer_instance

        # 执行导出
        result = await processor.process_export_task(
            task_id=sample_task.id,
            lesson_plan_id=sample_lesson_plan.id,
            template_id=None,
            format=ExportFormat.WORD.value,
            user_id=uuid.uuid4()
        )

        # 验证结果
        assert result is not None

        # 验证进度通知
        assert processor.notifier.notify_progress.call_count >= 3
        processor.notifier.notify_complete.assert_called_once()

        # 验证文件保存
        processor.storage.save_file.assert_called_once()


@pytest.mark.asyncio
async def test_process_export_task_pdf(processor, sample_task, sample_lesson_plan, mock_db):
    """测试处理PDF格式导出任务"""

    # 设置数据库查询返回序列
    mock_db.execute = AsyncMock(side_effect=[
        create_mock_result(sample_task),
        create_mock_result(sample_lesson_plan),
        create_mock_result(sample_task),
    ])

    # 模拟PDF生成器
    mock_pdf_gen = MagicMock()
    mock_pdf_gen.generate_from_lesson_plan = AsyncMock(return_value=b"fake pdf content")
    processor.pdf_generator = mock_pdf_gen

    # 模拟ContentRendererService
    with patch('app.services.export_task_processor.ContentRendererService') as mock_renderer:
        mock_renderer_instance = MagicMock()
        mock_renderer_instance.render_lesson_plan = Mock(return_value="# Test Content")
        mock_renderer.return_value = mock_renderer_instance

        result = await processor.process_export_task(
            task_id=sample_task.id,
            lesson_plan_id=sample_lesson_plan.id,
            template_id=None,
            format=ExportFormat.PDF.value,
            user_id=uuid.uuid4()
        )

        assert result is not None
        mock_pdf_gen.generate_from_lesson_plan.assert_called_once()


@pytest.mark.asyncio
async def test_process_export_task_pptx(processor, sample_task, sample_lesson_plan, mock_db):
    """测试处理PPTX格式导出任务"""

    # 设置数据库查询返回序列
    mock_db.execute = AsyncMock(side_effect=[
        create_mock_result(sample_task),
        create_mock_result(sample_lesson_plan),
        create_mock_result(sample_task),
    ])

    # 模拟PPTX生成器
    mock_pptx_gen = MagicMock()
    mock_pptx_gen.generate = Mock(return_value=b"fake pptx content")
    processor.pptx_generator = mock_pptx_gen

    # 模拟ContentRendererService
    with patch('app.services.export_task_processor.ContentRendererService') as mock_renderer:
        mock_renderer_instance = MagicMock()
        mock_renderer_instance.render_lesson_plan = Mock(return_value="# Test Content")
        mock_renderer.return_value = mock_renderer_instance

        result = await processor.process_export_task(
            task_id=sample_task.id,
            lesson_plan_id=sample_lesson_plan.id,
            template_id=None,
            format=ExportFormat.PPTX.value,
            user_id=uuid.uuid4()
        )

        assert result is not None


@pytest.mark.asyncio
async def test_process_export_task_markdown(processor, sample_task, sample_lesson_plan, mock_db):
    """测试处理Markdown格式导出任务"""

    # 设置数据库查询返回序列
    mock_db.execute = AsyncMock(side_effect=[
        create_mock_result(sample_task),
        create_mock_result(sample_lesson_plan),
        create_mock_result(sample_task),
    ])

    # Mock ContentRendererService
    with patch('app.services.export_task_processor.ContentRendererService') as mock_renderer:
        mock_renderer_instance = MagicMock()
        mock_renderer_instance.render_lesson_plan = Mock(return_value="# Test Markdown")
        mock_renderer.return_value = mock_renderer_instance

        result = await processor.process_export_task(
            task_id=sample_task.id,
            lesson_plan_id=sample_lesson_plan.id,
            template_id=None,
            format=ExportFormat.MARKDOWN.value,
            user_id=uuid.uuid4()
        )

        assert result is not None


# ========== 错误处理测试 ==========

@pytest.mark.asyncio
async def test_process_export_task_lesson_not_found(processor, sample_task, sample_lesson_plan, mock_db):
    """测试教案不存在的情况"""

    # 第一次返回任务，第二次返回None（教案不存在）
    mock_db.execute = AsyncMock(side_effect=[
        create_mock_result(sample_task),
        create_mock_result(None),
    ])

    # 模拟ContentRendererService
    with patch('app.services.export_task_processor.ContentRendererService') as mock_renderer:
        mock_renderer_instance = MagicMock()
        mock_renderer_instance.render_lesson_plan = Mock(return_value="# Test")
        mock_renderer.return_value = mock_renderer_instance

        with pytest.raises(Exception):
            await processor.process_export_task(
                task_id=sample_task.id,
                lesson_plan_id=sample_lesson_plan.id,
                template_id=None,
                format=ExportFormat.WORD.value,
                user_id=uuid.uuid4()
            )

        # 验证错误通知被调用
        processor.notifier.notify_error.assert_called_once()


@pytest.mark.asyncio
async def test_process_export_task_invalid_format(processor, sample_task, sample_lesson_plan, mock_db):
    """测试无效的导出格式"""

    mock_db.execute = AsyncMock(return_value=create_mock_result(sample_task))

    with pytest.raises(Exception):
        await processor.process_export_task(
            task_id=sample_task.id,
            lesson_plan_id=sample_lesson_plan.id,
            template_id=None,
            format="invalid_format",
            user_id=uuid.uuid4()
        )


@pytest.mark.asyncio
async def test_process_export_task_template_mismatch(processor, sample_task, sample_lesson_plan, sample_template, mock_db):
    """测试模板格式不匹配的情况"""

    # 模板是PDF格式，请求的是Word格式
    mock_db.execute = AsyncMock(side_effect=[
        create_mock_result(sample_task),
        create_mock_result(sample_lesson_plan),
        create_mock_result(sample_template),
    ])

    sample_template.format = ExportFormat.PDF.value

    with pytest.raises(Exception):
        await processor.process_export_task(
            task_id=sample_task.id,
            lesson_plan_id=sample_lesson_plan.id,
            template_id=sample_template.id,
            format=ExportFormat.WORD.value,
            user_id=uuid.uuid4()
        )


# ========== 辅助方法测试 ==========

def test_generate_filename(processor, sample_lesson_plan):
    """测试文件名生成"""
    filename = processor._generate_filename(sample_lesson_plan, ExportFormat.WORD)
    assert filename.endswith(".docx")
    assert "过去完成时教学" in filename
    assert "B1" in filename


def test_generate_filename_with_special_chars(processor, sample_lesson_plan):
    """测试包含特殊字符的标题"""
    sample_lesson_plan.title = "Test/教案:特殊*字符?"
    filename = processor._generate_filename(sample_lesson_plan, ExportFormat.PDF)
    assert filename.endswith(".pdf")
    # 特殊字符应被移除
    assert "/" not in filename
    assert ":" not in filename
    assert "*" not in filename


def test_get_format_from_filename(processor):
    """测试从文件名获取格式"""
    assert processor._get_format_from_filename("test.docx") == ExportFormat.WORD
    assert processor._get_format_from_filename("test.pdf") == ExportFormat.PDF
    assert processor._get_format_from_filename("test.pptx") == ExportFormat.PPTX
    assert processor._get_format_from_filename("test.md") == ExportFormat.MARKDOWN


def test_generate_download_url(processor):
    """测试下载URL生成"""
    with patch.object(processor.settings, 'CORS_ORIGINS', ['http://localhost:5173']):
        url = processor._generate_download_url("/path/to/file.docx")
        assert url.startswith("http://localhost:5173")
        assert "/api/v1/exports/download/" in url


# ========== 进度通知测试 ==========

@pytest.mark.asyncio
async def test_progress_notification_sequence(processor, sample_task, sample_lesson_plan, mock_db):
    """测试进度通知顺序"""

    # 设置数据库查询返回序列
    mock_db.execute = AsyncMock(side_effect=[
        create_mock_result(sample_task),      # 1: 获取任务
        create_mock_result(sample_lesson_plan),  # 2: 获取教案
        create_mock_result(sample_task),      # 3-6: 更新任务状态
        create_mock_result(sample_task),
        create_mock_result(sample_task),
        create_mock_result(sample_task),
    ])

    mock_word_gen = MagicMock()
    mock_word_gen.generate = Mock(return_value=b"content")
    processor.word_generator = mock_word_gen

    # 模拟ContentRendererService
    with patch('app.services.export_task_processor.ContentRendererService') as mock_renderer:
        mock_renderer_instance = MagicMock()
        mock_renderer_instance.render_lesson_plan = Mock(return_value="# Test")
        mock_renderer.return_value = mock_renderer_instance

        await processor.process_export_task(
            task_id=sample_task.id,
            lesson_plan_id=sample_lesson_plan.id,
            template_id=None,
            format=ExportFormat.WORD.value,
            user_id=uuid.uuid4()
        )

        # 验证进度通知被调用多次
        assert processor.notifier.notify_progress.call_count >= 3


# ========== 文件存储测试 ==========

@pytest.mark.asyncio
async def test_save_file_to_storage(processor, sample_lesson_plan):
    """测试文件保存到存储"""
    file_content = b"test content"
    filename = "test.docx"

    file_path, file_size = await processor._save_file_to_storage(
        file_content,
        filename,
        sample_lesson_plan.id,
        uuid.uuid4()
    )

    assert file_path == "/path/to/file.docx"
    assert file_size == 12345
    processor.storage.save_file.assert_called_once()


# ========== 任务状态更新测试 ==========

@pytest.mark.asyncio
async def test_update_task_status_processing(processor, sample_task, mock_db):
    """测试更新任务为处理中状态"""

    mock_db.execute = AsyncMock(return_value=create_mock_result(sample_task))

    await processor._update_task_status(
        sample_task.id,
        TaskStatus.PROCESSING,
        50,
        "处理中..."
    )

    assert sample_task.status == TaskStatus.PROCESSING.value
    assert sample_task.progress == 50


@pytest.mark.asyncio
async def test_update_task_status_completed(processor, sample_task, mock_db):
    """测试更新任务为完成状态"""

    mock_db.execute = AsyncMock(return_value=create_mock_result(sample_task))

    await processor._update_task_status(
        sample_task.id,
        TaskStatus.COMPLETED,
        100,
        None,
        file_path="/path/to/file.pdf",
        file_size=54321,
        download_url="http://example.com/download"
    )

    assert sample_task.status == TaskStatus.COMPLETED.value
    assert sample_task.progress == 100
    assert sample_task.file_path == "/path/to/file.pdf"
    assert sample_task.file_size == 54321
    assert sample_task.download_url == "http://example.com/download"


@pytest.mark.asyncio
async def test_update_task_status_failed(processor, sample_task, mock_db):
    """测试更新任务为失败状态"""

    mock_db.execute = AsyncMock(return_value=create_mock_result(sample_task))

    await processor._update_task_status(
        sample_task.id,
        TaskStatus.FAILED,
        0,
        "生成失败"
    )

    assert sample_task.status == TaskStatus.FAILED.value
    assert sample_task.error_message == "生成失败"


# ========== 便捷函数测试 ==========

def test_get_export_task_processor(mock_db, mock_notifier):
    """测试获取处理器实例的便捷函数"""
    with patch('app.services.export_task_processor.ExportTaskProcessor') as mock_processor_class:
        mock_instance = MagicMock()
        mock_processor_class.return_value = mock_instance

        result = get_export_task_processor(mock_db, mock_notifier)

        assert result == mock_instance
        mock_processor_class.assert_called_once_with(mock_db, mock_notifier)


# ========== 内容渲染测试 ==========

@pytest.mark.asyncio
async def test_render_content_with_template(processor, sample_lesson_plan, sample_template):
    """测试使用模板渲染内容"""
    with patch('app.services.export_task_processor.ContentRendererService') as mock_renderer:
        mock_renderer_instance = MagicMock()
        mock_renderer_instance.render_lesson_plan = Mock(return_value="# Rendered Content")
        mock_renderer.return_value = mock_renderer_instance

        content = await processor._render_content(
            sample_lesson_plan,
            sample_template,
            {"sections": ["metadata", "objectives"]}
        )

        assert content["title"] == sample_lesson_plan.title
        assert content["level"] == sample_lesson_plan.level
        assert content["markdown_content"] == "# Rendered Content"


@pytest.mark.asyncio
async def test_render_content_without_template(processor, sample_lesson_plan):
    """测试不使用模板渲染内容"""
    with patch('app.services.export_task_processor.ContentRendererService') as mock_renderer:
        mock_renderer_instance = MagicMock()
        mock_renderer_instance.render_lesson_plan = Mock(return_value="# Full Content")
        mock_renderer.return_value = mock_renderer_instance

        content = await processor._render_content(
            sample_lesson_plan,
            None,
            None
        )

        assert content["title"] == sample_lesson_plan.title
        assert "markdown_content" in content
