"""
导出任务处理器 - AI英语教学系统

处理教案导出任务的完整流程，包括内容渲染、文档生成、文件存储。
支持多种导出格式（Word、PDF、PPTX、Markdown），集成实时进度通知。

核心功能：
- 处理导出任务主入口（process_export_task）
- 执行文档生成（_execute_generation）
- 更新任务状态（_update_task_status）
- 保存文件到存储（_save_file_to_storage）
- 生成下载URL（_generate_download_url）
"""

import logging
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.metrics import (
    record_export_task_started,
    record_export_task_completed,
    record_export_task_failed,
)
from app.models.export_task import ExportFormat, ExportTask, TaskStatus
from app.models.export_template import ExportTemplate
from app.models.lesson_plan import LessonPlan
from app.services.content_renderer_service import ContentRendererService
from app.services.document_generators.pdf_generator import PDFDocumentGenerator
from app.services.document_generators.pptx_generator import PPTXDocumentGenerator
from app.services.document_generators.word_generator import WordDocumentGenerator
from app.services.file_storage_service import FileStorageService
from app.services.progress_notifier import ProgressNotifier
from app.utils.concurrency import get_export_concurrency_controller

logger = logging.getLogger(__name__)


class ExportTaskProcessor:
    """
    导出任务处理器

    负责处理教案导出任务的完整生命周期：
    1. 获取教案数据和模板配置
    2. 使用 ContentRendererService 渲染内容
    3. 使用对应的文档生成器生成文档
    4. 保存文件到 FileStorageService
    5. 更新任务状态并通知进度
    6. 生成下载URL

    使用示例：
        ```python
        processor = ExportTaskProcessor(db, notifier)

        task_id = uuid.uuid4()
        await processor.process_export_task(
            task_id=task_id,
            lesson_plan_id=lesson_id,
            template_id=template_id,
            format=ExportFormat.WORD,
            user_id=user_id
        )
        ```
    """

    # 进度百分比配置
    PROGRESS_STAGES = {
        "loading": 5,
        "rendering": 20,
        "generating": 80,
        "saving": 90,
        "completed": 100,
    }

    def __init__(
        self,
        db: AsyncSession,
        notifier: Optional[ProgressNotifier] = None,
    ):
        """
        初始化导出任务处理器

        Args:
            db: 数据库会话
            notifier: 进度通知服务（可选，默认使用全局单例）
        """
        self.db = db
        self.notifier = notifier or ProgressNotifier()
        self.settings = get_settings()

        # 初始化并发控制器
        self.concurrency_controller = get_export_concurrency_controller()

        # 初始化生成器
        self.word_generator = WordDocumentGenerator()
        self.pdf_generator = PDFDocumentGenerator()
        self.pptx_generator = PPTXDocumentGenerator()

        # 初始化存储服务
        self.storage = FileStorageService()

    async def process_export_task(
        self,
        task_id: uuid.UUID,
        lesson_plan_id: uuid.UUID,
        template_id: Optional[uuid.UUID],
        format: str,
        user_id: uuid.UUID,
        options: Optional[Dict[str, Any]] = None,
    ) -> ExportTask:
        """
        处理导出任务主入口

        Args:
            task_id: 任务ID
            lesson_plan_id: 教案ID
            template_id: 模板ID（可选）
            format: 导出格式 (word/pdf/pptx/markdown)
            user_id: 用户ID
            options: 导出选项（可选）

        Returns:
            ExportTask: 更新后的任务对象

        Raises:
            HTTPException: 教案或模板不存在时
            RuntimeError: 文档生成失败时
        """
        task = None
        try:
            # 1. 获取任务对象
            task = await self._get_task(task_id)
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"导出任务不存在: {task_id}"
                )

            # 2. 验证格式
            try:
                export_format = ExportFormat(format)
            except ValueError:
                # 记录验证失败指标
                record_export_task_failed("validation", format)
                await self._update_task_status(
                    task_id, TaskStatus.FAILED, 0, f"不支持的导出格式: {format}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=f"不支持的导出格式: {format}"
                )

            # 3. 获取并发槽位（在队列中等待）
            controller_status = self.concurrency_controller.get_status()
            logger.info(
                f"导出任务等待获取槽位: {task_id}, "
                f"当前状态: {controller_status['active_count']}/{controller_status['max_concurrent']} 活跃"
            )

            # 使用上下文管理器自动管理槽位的获取和释放
            async with self.concurrency_controller.acquire(
                task_id=str(task_id),
                timeout=self.settings.EXPORT_TASK_TIMEOUT
            ) as acquired:
                if not acquired:
                    # 超时未获得槽位
                    # 记录超时失败指标
                    record_export_task_failed("timeout", format)
                    error_message = (
                        f"服务器繁忙，当前有 {controller_status['active_count']} "
                        f"个导出任务正在处理，请稍后重试"
                    )
                    await self._update_task_status(task_id, TaskStatus.FAILED, 0, error_message)
                    self.concurrency_controller.reject_task(str(task_id))
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=error_message
                    )

                # 4. 成功获取槽位，使用指标上下文管理器包裹任务执行
                async with record_export_task_started(format, str(task_id)):
                    # 更新任务状态为处理中
                    await self._update_task_status(
                        task_id,
                        TaskStatus.PROCESSING,
                        self.PROGRESS_STAGES["loading"],
                        "正在加载教案数据...",
                    )

                    logger.info(
                        f"导出任务获得槽位开始处理: {task_id}, "
                        f"活跃任务: {self.concurrency_controller.active_count}/"
                        f"{self.concurrency_controller.max_concurrent}"
                    )

                    try:
                        # 5. 获取教案数据
                        lesson = await self._get_lesson_plan(lesson_plan_id)
                        if not lesson:
                            await self._update_task_status(task_id, TaskStatus.FAILED, 0, "教案不存在")
                            raise HTTPException(
                                status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"教案不存在: {lesson_plan_id}"
                            )

                        # 6. 获取模板（如果指定）
                        template = None
                        template_vars = {}
                        if template_id:
                            template = await self._get_template(template_id)
                            if not template:
                                await self._update_task_status(task_id, TaskStatus.FAILED, 0, "模板不存在")
                                raise HTTPException(
                                    status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f"模板不存在: {template_id}"
                                )
                            # 验证模板格式匹配
                            if template.format != format:
                                await self._update_task_status(
                                    task_id,
                                    TaskStatus.FAILED,
                                    0,
                                    f"模板格式({template.format})与请求格式({format})不匹配",
                                )
                                raise HTTPException(
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"模板格式({template.format})与请求格式({format})不匹配",
                                )

                            # 从选项中获取模板变量
                            if options and "template_variables" in options:
                                template_vars = options["template_variables"]

                        # 7. 渲染内容
                        await self._notify_progress(
                            task_id, self.PROGRESS_STAGES["rendering"], "正在渲染教案内容..."
                        )

                        rendered_content = await self._render_content(lesson, template, options)

                        # 8. 生成文档
                        await self._notify_progress(
                            task_id,
                            self.PROGRESS_STAGES["generating"],
                            f"正在生成{export_format.value.upper()}文档...",
                        )

                        file_content = await self._execute_generation(
                            lesson, rendered_content, export_format, template_vars
                        )

                        # 9. 保存文件
                        await self._notify_progress(
                            task_id, self.PROGRESS_STAGES["saving"], "正在保存文件..."
                        )

                        filename = self._generate_filename(lesson, export_format)
                        file_path, file_size = await self._save_file_to_storage(
                            file_content, filename, lesson_plan_id, user_id
                        )

                        # 10. 生成下载URL
                        download_url = self._generate_download_url(file_path)

                        # 11. 更新任务为完成状态
                        await self._update_task_status(
                            task_id,
                            TaskStatus.COMPLETED,
                            self.PROGRESS_STAGES["completed"],
                            None,
                            file_path=file_path,
                            file_size=file_size,
                            download_url=download_url,
                        )

                        # 12. 通知完成
                        await self.notifier.notify_complete(str(task_id), download_url)

                        # 13. 更新模板使用次数
                        if template:
                            template.increment_usage()
                            await self.db.commit()

                        logger.info(
                            f"导出任务完成: {task_id}, "
                            f"格式: {format}, "
                            f"文件: {file_path}, "
                            f"大小: {file_size} bytes"
                        )

                        # 记录任务完成指标
                        record_export_task_completed(format, "completed")

                        # 刷新并返回任务
                        await self.db.refresh(task)
                        return task

                    except HTTPException:
                        # HTTP异常特殊处理，重新抛出
                        raise
                    except Exception as e:
                        # 记录生成失败指标
                        record_export_task_failed("generation", format)
                        raise

        except HTTPException as http_exc:
            # HTTP异常也记录错误并通知
            error_message = http_exc.detail
            if task:
                await self._update_task_status(task_id, TaskStatus.FAILED, 0, error_message)
                await self.notifier.notify_error(str(task_id), error_message)
            raise
        except Exception as e:
            logger.error(f"导出任务处理失败: {task_id}, 错误: {e}", exc_info=e)

            # 更新任务为失败状态
            error_message = f"文档生成失败: {str(e)}"
            if task:
                await self._update_task_status(task_id, TaskStatus.FAILED, 0, error_message)
                await self.notifier.notify_error(str(task_id), error_message)

            raise RuntimeError(f"导出任务处理失败: {e}") from e

    async def _render_content(
        self,
        lesson: LessonPlan,
        template: Optional[ExportTemplate],
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        渲染教案内容

        Args:
            lesson: 教案对象
            template: 模板对象（可选）
            options: 导出选项（可选）

        Returns:
            Dict[str, Any]: 渲染后的内容数据
        """
        # 确定要包含的章节
        include_sections = None
        if options and "sections" in options:
            include_sections = options["sections"]

        # 使用 ContentRendererService 渲染
        renderer = ContentRendererService(format="markdown")
        markdown_content = renderer.render_lesson_plan(lesson, include_sections)

        # 构建结构化内容
        rendered_content = {
            "title": lesson.title,
            "level": lesson.level,
            "topic": lesson.topic,
            "duration": lesson.duration,
            "target_exam": lesson.target_exam,
            "objectives": lesson.objectives,
            "vocabulary": lesson.vocabulary,
            "grammar_points": lesson.grammar_points,
            "teaching_structure": lesson.teaching_structure,
            "leveled_materials": lesson.leveled_materials,
            "exercises": lesson.exercises,
            "ppt_outline": lesson.ppt_outline,
            "resources": lesson.resources,
            "teaching_notes": lesson.teaching_notes,
            "markdown_content": markdown_content,  # 保存Markdown内容用于某些格式
        }

        return rendered_content

    async def _execute_generation(
        self,
        lesson: LessonPlan,
        content: Dict[str, Any],
        format: ExportFormat,
        template_vars: Dict[str, Any],
    ) -> bytes:
        """
        执行文档生成

        Args:
            lesson: 教案对象
            content: 渲染后的内容
            format: 导出格式
            template_vars: 模板变量

        Returns:
            bytes: 生成的文档二进制内容

        Raises:
            ValueError: 不支持的格式
            RuntimeError: 文档生成失败
        """
        try:
            if format == ExportFormat.WORD:
                # 使用 Word 生成器
                return self.word_generator.generate(content, template_vars)

            elif format == ExportFormat.PDF:
                # 使用 PDF 生成器
                return await self.pdf_generator.generate_from_lesson_plan(lesson)

            elif format == ExportFormat.PPTX:
                # 使用 PPTX 生成器
                return self.pptx_generator.generate(content, template_vars)

            elif format == ExportFormat.MARKDOWN:
                # 直接返回 Markdown 内容
                markdown_content = content.get("markdown_content", "")
                if not markdown_content:
                    # 如果没有预渲染的Markdown，使用ContentRendererService
                    renderer = ContentRendererService(format="markdown")
                    markdown_content = renderer.render_lesson_plan(lesson)
                return markdown_content.encode("utf-8")

            else:
                raise ValueError(f"不支持的导出格式: {format}")

        except Exception as e:
            logger.error(f"文档生成失败: {format}, 错误: {e}", exc_info=e)
            raise RuntimeError(f"文档生成失败: {e}") from e

    async def _update_task_status(
        self,
        task_id: uuid.UUID,
        status: TaskStatus,
        progress: int,
        error_message: Optional[str] = None,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        download_url: Optional[str] = None,
    ) -> None:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            progress: 进度百分比
            error_message: 错误消息（可选）
            file_path: 文件路径（可选）
            file_size: 文件大小（可选）
            download_url: 下载URL（可选）
        """
        try:
            # 获取任务
            query = select(ExportTask).where(ExportTask.id == task_id)
            result = await self.db.execute(query)
            task = result.scalar_one_or_none()

            if not task:
                logger.warning(f"更新任务状态失败: 任务不存在 {task_id}")
                return

            # 更新状态
            task.status = status.value
            task.progress = progress

            if error_message:
                task.error_message = error_message

            if file_path:
                task.file_path = file_path

            if file_size is not None:
                task.file_size = file_size

            if download_url:
                task.download_url = download_url

            # 更新时间戳
            if status == TaskStatus.PROCESSING and not task.started_at:
                task.started_at = datetime.utcnow()

            if status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                task.completed_at = datetime.utcnow()

            await self.db.commit()
            logger.debug(
                f"任务状态已更新: {task_id}, " f"状态: {status.value}, " f"进度: {progress}%"
            )

        except Exception as e:
            logger.error(f"更新任务状态失败: {task_id}, 错误: {e}", exc_info=e)

    async def _save_file_to_storage(
        self,
        file_content: bytes,
        filename: str,
        lesson_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[str, int]:
        """
        保存文件到存储

        Args:
            file_content: 文件内容（字节）
            filename: 文件名
            lesson_id: 教案ID
            user_id: 用户ID

        Returns:
            tuple[str, int]: (文件路径, 文件大小)
        """
        # 使用 FileStorageService 保存文件
        # 注意：需要将format转换为ExportFormat枚举
        file_path, file_size = await self.storage.save_file(
            content=file_content, filename=filename, format=self._get_format_from_filename(filename)
        )

        logger.info(
            f"文件已保存: {file_path}, "
            f"大小: {file_size} bytes, "
            f"教案: {lesson_id}, "
            f"用户: {user_id}"
        )

        return file_path, file_size

    def _generate_download_url(self, file_path: str) -> str:
        """
        生成下载URL

        Args:
            file_path: 文件存储路径

        Returns:
            str: 下载URL
        """
        # 从文件路径中提取文件名
        filename = Path(file_path).name

        # 构建下载URL
        base_url = self.settings.CORS_ORIGINS[0] if self.settings.CORS_ORIGINS else ""
        download_url = f"{base_url}/api/v1/exports/download/{filename}"

        return download_url

    def _generate_filename(self, lesson: LessonPlan, format: ExportFormat) -> str:
        """
        生成文件名

        Args:
            lesson: 教案对象
            format: 导出格式

        Returns:
            str: 文件名
        """
        # 清理标题中的非法字符
        safe_title = "".join(
            c for c in lesson.title if c.isalnum() or c in (" ", "-", "_", ".")
        ).strip()

        # 限制长度
        if len(safe_title) > 50:
            safe_title = safe_title[:50]

        # 获取扩展名
        ext_map = {
            ExportFormat.WORD: "docx",
            ExportFormat.PDF: "pdf",
            ExportFormat.PPTX: "pptx",
            ExportFormat.MARKDOWN: "md",
        }
        ext = ext_map.get(format, format.value)

        # 生成文件名
        filename = f"{safe_title}_{lesson.level}.{ext}"

        return filename

    def _get_format_from_filename(self, filename: str) -> ExportFormat:
        """
        从文件名获取导出格式

        Args:
            filename: 文件名

        Returns:
            ExportFormat: 导出格式枚举
        """
        ext_map = {
            ".docx": ExportFormat.WORD,
            ".pdf": ExportFormat.PDF,
            ".pptx": ExportFormat.PPTX,
            ".md": ExportFormat.MARKDOWN,
        }

        ext = Path(filename).suffix.lower()
        return ext_map.get(ext, ExportFormat.MARKDOWN)

    async def _notify_progress(
        self,
        task_id: uuid.UUID,
        progress: int,
        message: str,
    ) -> None:
        """
        通知进度更新

        Args:
            task_id: 任务ID
            progress: 进度百分比
            message: 进度描述
        """
        await self.notifier.notify_progress(str(task_id), progress, message)

    async def _get_task(self, task_id: uuid.UUID) -> Optional[ExportTask]:
        """
        获取任务对象

        Args:
            task_id: 任务ID

        Returns:
            Optional[ExportTask]: 任务对象，不存在返回None
        """
        query = select(ExportTask).where(ExportTask.id == task_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_lesson_plan(self, lesson_plan_id: uuid.UUID) -> Optional[LessonPlan]:
        """
        获取教案对象

        Args:
            lesson_plan_id: 教案ID

        Returns:
            Optional[LessonPlan]: 教案对象，不存在返回None
        """
        query = select(LessonPlan).where(LessonPlan.id == lesson_plan_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_template(self, template_id: uuid.UUID) -> Optional[ExportTemplate]:
        """
        获取模板对象

        Args:
            template_id: 模板ID

        Returns:
            Optional[ExportTemplate]: 模板对象，不存在返回None
        """
        query = select(ExportTemplate).where(ExportTemplate.id == template_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


# ========== 模块级便捷函数 ==========


def get_export_task_processor(
    db: AsyncSession,
    notifier: Optional[ProgressNotifier] = None,
) -> ExportTaskProcessor:
    """
    获取导出任务处理器实例

    Args:
        db: 数据库会话
        notifier: 进度通知服务（可选）

    Returns:
        ExportTaskProcessor: 导出任务处理器实例
    """
    return ExportTaskProcessor(db, notifier)
