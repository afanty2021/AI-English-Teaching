"""
报告导出 Celery 任务
处理异步报告生成和导出任务
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal, get_db
from app.models import User
from app.models.async_task import AsyncTask, AsyncTaskStatus, AsyncTaskType
from app.services.async_task_service import AsyncTaskService
from app.services.learning_report_service import LearningReportService
from app.services.report_export_service import ReportExportService

logger = logging.getLogger(__name__)


def run_async(coro):
    """运行异步函数（Celery worker 环境）"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def get_db_session():
    """获取数据库会话（同步版本，用于 Celery 任务）"""
    return AsyncSessionLocal()


# ============ 报告生成任务 ============

@shared_task(
    bind=True,
    name="app.tasks.report_tasks.generate_report",
    max_retries=3,
    default_retry_delay=60,
)
def generate_report(self, task_id: str, student_id: str, report_type: str,
                   period_start: Optional[str] = None, period_end: Optional[str] = None,
                   title: Optional[str] = None, description: Optional[str] = None):
    """
    生成学习报告任务

    Args:
        task_id: 异步任务ID
        student_id: 学生ID
        report_type: 报告类型 (weekly/monthly/custom)
        period_start: 开始日期 (ISO格式)
        period_end: 结束日期 (ISO格式)
        title: 报告标题
        description: 报告描述
    """
    async_task_service = None

    try:
        # 获取数据库会话
        db = get_db_session()
        async_task_service = AsyncTaskService(db)

        # 更新任务状态为处理中
        async_task_service.update_task_progress(
            task_id=task_id,
            progress=10,
            message="开始生成学习报告..."
        )

        # 解析日期
        start_dt = datetime.fromisoformat(period_start) if period_start else None
        end_dt = datetime.fromisoformat(period_end) if period_end else None

        # 获取学习报告服务
        report_service = LearningReportService(db)

        # 生成报告
        report = run_async(
            report_service.generate_report(
                student_id=UUID(student_id),
                report_type=report_type,
                period_start=start_dt,
                period_end=end_dt,
                title=title,
                description=description,
            )
        )

        # 更新进度
        async_task_service.update_task_progress(
            task_id=task_id,
            progress=90,
            message="报告生成完成..."
        )

        # 完成任务
        async_task_service.complete_task(
            task_id=task_id,
            result_data={
                "report_id": str(report.id),
                "report_type": report.report_type,
                "title": report.title,
            },
            message="学习报告生成成功"
        )

        logger.info(f"Report generated successfully: {report.id}")
        return {"report_id": str(report.id), "status": "completed"}

    except Exception as exc:
        logger.error(f"Error generating report: {exc}")

        if async_task_service:
            async_task_service.fail_task(
                task_id=task_id,
                error_message=str(exc),
            )

        raise self.retry(exc=exc)


# ============ 报告导出任务 ============

@shared_task(
    bind=True,
    name="app.tasks.report_tasks.export_report_pdf",
    max_retries=3,
    default_retry_delay=60,
)
def export_report_pdf(self, task_id: str, report_id: str, format: str = "pdf"):
    """
    导出报告为 PDF 或其他格式

    Args:
        task_id: 异步任务ID
        report_id: 报告ID
        format: 导出格式 (pdf/markdown/word)
    """
    async_task_service = None

    try:
        # 获取数据库会话
        db = get_db_session()
        async_task_service = AsyncTaskService(db)

        # 更新任务状态
        async_task_service.update_task_progress(
            task_id=task_id,
            progress=10,
            message="正在准备导出..."
        )

        # 获取报告
        report_service = LearningReportService(db)
        report = run_async(report_service.get_report_by_id(UUID(report_id)))

        if not report:
            raise ValueError(f"Report not found: {report_id}")

        # 更新进度
        async_task_service.update_task_progress(
            task_id=task_id,
            progress=30,
            message="正在渲染报告内容..."
        )

        # 执行导出
        export_service = ReportExportService(db)
        result = run_async(
            export_service.export_as_pdf(
                report_id=UUID(report_id),
                format=format,
            )
        )

        # 更新进度
        async_task_service.update_task_progress(
            task_id=task_id,
            progress=90,
            message="导出完成..."
        )

        # 完成任务
        async_task_service.complete_task(
            task_id=task_id,
            result_data={
                "report_id": report_id,
                "format": format,
                "file_path": result.get("file_path") if isinstance(result, dict) else str(result),
            },
            message=f"报告导出成功 ( {format.upper()} )"
        )

        logger.info(f"Report exported successfully: {report_id}")
        return {"report_id": report_id, "status": "completed", "format": format}

    except Exception as exc:
        logger.error(f"Error exporting report: {exc}")

        if async_task_service:
            async_task_service.fail_task(
                task_id=task_id,
                error_message=str(exc),
            )

        raise self.retry(exc=exc)


# ============ 批量导出任务 ============

@shared_task(
    bind=True,
    name="app.tasks.report_tasks.batch_export_reports",
    max_retries=1,
    default_retry_delay=120,
)
def batch_export_reports(self, task_id: str, student_id: str, report_ids: list, format: str = "pdf"):
    """
    批量导出多个报告

    Args:
        task_id: 主任务ID
        student_id: 学生ID
        report_ids: 报告ID列表
        format: 导出格式
    """
    async_task_service = None

    try:
        # 获取数据库会话
        db = get_db_session()
        async_task_service = AsyncTaskService(db)

        total = len(report_ids)
        completed = 0
        failed = 0

        # 更新主任务状态
        async_task_service.update_task_progress(
            task_id=task_id,
            progress=0,
            message=f"开始批量导出 {total} 个报告...",
            result_details={
                "total": total,
                "completed": 0,
                "failed": 0,
            }
        )

        # 导出服务
        export_service = ReportExportService(db)
        report_service = LearningReportService(db)

        for idx, report_id in enumerate(report_ids):
            try:
                # 获取报告
                report = run_async(report_service.get_report_by_id(UUID(report_id)))
                if not report:
                    failed += 1
                    continue

                # 执行导出
                result = run_async(
                    export_service.export_as_pdf(
                        report_id=UUID(report_id),
                        format=format,
                    )
                )

                if result:
                    completed += 1

                # 更新进度
                progress = int((idx + 1) / total * 100)
                async_task_service.update_task_progress(
                    task_id=task_id,
                    progress=progress,
                    message=f"已导出 {idx + 1}/{total} 个报告",
                    result_details={
                        "total": total,
                        "completed": completed,
                        "failed": failed,
                    }
                )

            except Exception as e:
                logger.error(f"Error exporting report {report_id}: {e}")
                failed += 1

        # 完成任务
        final_status = "completed" if failed == 0 else "partially_completed"
        async_task_service.complete_task(
            task_id=task_id,
            result_data={
                "total": total,
                "completed": completed,
                "failed": failed,
                "format": format,
            },
            message=f"批量导出完成: {completed}/{total} 成功",
            status=final_status,
        )

        return {
            "status": final_status,
            "total": total,
            "completed": completed,
            "failed": failed,
        }

    except Exception as exc:
        logger.error(f"Error in batch export: {exc}")

        if async_task_service:
            async_task_service.fail_task(
                task_id=task_id,
                error_message=str(exc),
            )

        raise self.retry(exc=exc)


# ============ 清理任务 ============

@shared_task(
    name="app.tasks.report_tasks.cleanup_expired_tasks",
)
def cleanup_expired_tasks():
    """
    清理过期的异步任务
    每天或每周执行一次，清理已完成的旧任务
    """
    db = get_db_session()
    async_task_service = AsyncTaskService(db)

    cleaned = run_async(async_task_service.cleanup_old_tasks(days=30))

    logger.info(f"Cleaned up {cleaned} expired tasks")
    return {"cleaned_tasks": cleaned}


# ============ 取消任务 ============

@shared_task(
    bind=True,
    name="app.tasks.report_tasks.cancel_task",
)
def cancel_task(self, task_id: str):
    """
    取消任务

    Args:
        task_id: 要取消的任务ID
    """
    db = get_db_session()
    async_task_service = AsyncTaskService(db)

    success = run_async(async_task_service.cancel_task(task_id, None))  # 简化处理

    if success:
        logger.info(f"Task cancelled: {task_id}")
        return {"status": "cancelled", "task_id": task_id}
    else:
        logger.warning(f"Failed to cancel task: {task_id}")
        return {"status": "failed", "task_id": task_id}


# ============ 异步包装器（供 API 调用） ============

async def async_generate_report(
    student_id: str,
    report_type: str,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:
    """
    异步生成学习报告（包装 Celery 任务）

    Returns:
        dict: 任务信息
    """
    from app.core.celery import celery_app

    db = AsyncSessionLocal()
    async_task_service = AsyncTaskService(db)

    # 通过 student_id 获取用户ID
    result = await db.execute(
        select(User.id).where(User.id == UUID(student_id))
    )
    user_id = result.scalar_one_or_none()

    if not user_id:
        raise ValueError(f"User not found: {student_id}")

    task = await async_task_service.create_task(
        user_id=user_id,
        task_type=AsyncTaskType.REPORT_GENERATE.value,
        input_params={
            "report_type": report_type,
            "period_start": period_start,
            "period_end": period_end,
            "title": title,
            "description": description,
        },
        priority=0,
    )

    # 提交 Celery 任务
    celery_app.send_task(
        "app.tasks.report_tasks.generate_report",
        args=[
            str(task.id),
            student_id,
            report_type,
            period_start,
            period_end,
            title,
            description,
        ],
        queue="reports",
    )

    return {
        "task_id": str(task.id),
        "status": "pending",
        "message": "报告生成任务已提交",
    }


async def async_export_report(
    report_id: str,
    format: str = "pdf",
) -> dict:
    """
    异步导出报告（包装 Celery 任务）

    Returns:
        dict: 任务信息
    """
    from app.core.celery import celery_app

    db = AsyncSessionLocal()
    async_task_service = AsyncTaskService(db)

    # 获取报告信息
    report_service = LearningReportService(db)
    report = await report_service.get_report_by_id(UUID(report_id))

    if not report:
        raise ValueError(f"Report not found: {report_id}")

    # 通过 student_id 获取用户ID
    result = await db.execute(
        select(User.id).where(User.id == report.student_id)
    )
    user_id = result.scalar_one_or_none()

    task = await async_task_service.create_task(
        user_id=user_id,
        task_type=AsyncTaskType.REPORT_EXPORT.value,
        input_params={
            "report_id": report_id,
            "format": format,
        },
        priority=1,
    )

    # 提交 Celery 任务
    celery_app.send_task(
        "app.tasks.report_tasks.export_report_pdf",
        args=[str(task.id), report_id, format],
        queue="reports",
    )

    return {
        "task_id": str(task.id),
        "status": "pending",
        "message": f"导出任务已提交 ( {format.upper()} )",
    }
