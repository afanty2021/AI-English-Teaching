"""
增强报告API路由 - AI英语教学系统
提供图表数据、异步导出、任务管理等端点
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.v1.learning_reports import get_learning_report_service
from app.models import User
from app.models.async_task import AsyncTaskType
from app.services.async_task_service import AsyncTaskService, get_async_task_service
from app.services.chart_data_service import ChartDataService, get_chart_data_service
from app.services.learning_report_service import LearningReportService

router = APIRouter()


# ============ 图表数据端点 ============

@router.get("/reports/{report_id}/charts/learning-trend")
async def get_learning_trend_chart(
    report_id: uuid.UUID,
    period: str = Query("30d", description="时间范围: 7d, 30d, 90d"),
    metrics: Optional[List[str]] = Query(None, description="指标: practices, correctRate, duration"),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Dict[str, Any]:
    """
    获取学习趋势图表数据

    - 返回每日练习数量、正确率、学习时长的时间序列数据
    - 支持7天、30天、90天时间范围选择
    - 支持多指标同时返回
    """
    chart_service = get_chart_data_service(db)

    # 解析时间范围
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(period, 30)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # 验证报告归属
    report_service = get_learning_report_service(db)
    report = await report_service.get_report_by_id(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在"
        )

    if str(report.student_id) != str(current_user.id):
        # 检查是否是教师访问学生报告
        await report_service.verify_student_belongs_to_teacher(
            current_user.id, report.student_id
        )

    # 获取图表数据
    data = await chart_service.get_learning_trend_data(
        student_id=report.student_id,
        start_date=start_date,
        end_date=end_date,
        metrics=metrics,
    )

    return {
        "code": 0,
        "message": "success",
        "data": data,
    }


@router.get("/reports/{report_id}/charts/ability-radar")
async def get_ability_radar_chart(
    report_id: uuid.UUID,
    compare_with: Optional[str] = Query(None, description="对比模式: class_avg, history"),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Dict[str, Any]:
    """
    获取能力雷达图数据

    - 返回6维能力评估（词汇、语法、阅读、听力、口语、写作）
    - 支持班级平均对比
    """
    chart_service = get_chart_data_service(db)

    # 验证报告归属
    report_service = get_learning_report_service(db)
    report = await report_service.get_report_by_id(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在"
        )

    if str(report.student_id) != str(current_user.id):
        await report_service.verify_student_belongs_to_teacher(
            current_user.id, report.student_id
        )

    # 获取雷达图数据
    data = await chart_service.get_ability_radar_data(
        student_id=report.student_id,
        compare_with=compare_with,
    )

    return {
        "code": 0,
        "message": "success",
        "data": data,
    }


@router.get("/reports/{report_id}/charts/knowledge-heatmap")
async def get_knowledge_heatmap_chart(
    report_id: uuid.UUID,
    filter_by_ability: Optional[str] = Query(None, description="按能力类型筛选"),
    filter_by_topic: Optional[str] = Query(None, description="按主题筛选"),
    filter_by_difficulty: Optional[str] = Query(None, description="按难度筛选"),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Dict[str, Any]:
    """
    获取知识点热力图数据

    - 返回知识点掌握度分布
    - 支持多维度筛选
    """
    chart_service = get_chart_data_service(db)

    # 验证报告归属
    report_service = get_learning_report_service(db)
    report = await report_service.get_report_by_id(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在"
        )

    if str(report.student_id) != str(current_user.id):
        await report_service.verify_student_belongs_to_teacher(
            current_user.id, report.student_id
        )

    # 构建筛选条件
    filters = {}
    if filter_by_ability:
        filters["ability"] = filter_by_ability
    if filter_by_topic:
        filters["topic"] = filter_by_topic
    if filter_by_difficulty:
        filters["difficulty"] = filter_by_difficulty

    # 获取热力图数据
    data = await chart_service.get_knowledge_heatmap_data(
        student_id=report.student_id,
        filters=filters,
    )

    return {
        "code": 0,
        "message": "success",
        "data": data,
    }


# ============ 异步导出端点 ============

@router.post("/reports/export")
async def export_report_async(
    report_id: Optional[uuid.UUID] = None,
    student_ids: Optional[List[uuid.UUID]] = None,
    export_format: str = Query("pdf", description="导出格式: pdf, image"),
    report_type: str = Query("full", description="报告类型: full, summary"),
    async_mode: bool = Query(True, description="是否使用异步模式"),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Dict[str, Any]:
    """
    异步导出报告

    - 支持单个报告导出和学生批量导出
    - 返回任务ID用于进度查询
    """
    task_service = get_async_task_service(db)

    # 验证参数
    if not report_id and not student_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供 report_id 或 student_ids"
        )

    if student_ids and len(student_ids) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="单次批量导出最多支持50个学生"
        )

    # 确定任务类型
    if len(student_ids or []) > 1:
        task_type = AsyncTaskType.BATCH_EXPORT.value
        task = await task_service.create_task(
            user_id=current_user.id,
            task_type=task_type,
            input_params={
                "student_ids": [str(s) for s in student_ids] if student_ids else None,
                "export_format": export_format,
                "report_type": report_type,
            },
        )
    else:
        task_type = AsyncTaskType.REPORT_EXPORT.value
        task = await task_service.create_task(
            user_id=current_user.id,
            task_type=task_type,
            input_params={
                "report_id": str(report_id) if report_id else None,
                "student_id": str(student_ids[0]) if student_ids else None,
                "export_format": export_format,
                "report_type": report_type,
            },
        )

    # 这里应该启动Celery任务
    from app.core.celery import celery_app
    from app.tasks.report_tasks import export_report_pdf

    # 提交 Celery 任务
    celery_app.send_task(
        "app.tasks.report_tasks.export_report_pdf",
        args=[str(task.id), report_id if report_id else "", export_format],
        queue="reports",
    )

    return {
        "code": 0,
        "message": "任务已创建",
        "data": {
            "taskId": str(task.id),
            "status": task.status,
            "message": "导出任务已提交，请在任务列表中查看进度",
            "estimatedTime": 60,  # 预计秒数
        }
    }


# ============ 任务管理端点 ============

@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Dict[str, Any]:
    """
    获取任务状态

    - 返回任务当前进度和状态
    - 完成后返回下载链接
    """
    task_service = get_async_task_service(db)
    task_data = await task_service.get_task_status(task_id, current_user.id)

    return {
        "code": 0,
        "message": "success",
        "data": task_data,
    }


@router.get("/tasks")
async def list_tasks(
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    task_type: Optional[str] = Query(None, description="任务类型筛选"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Dict[str, Any]:
    """
    获取当前用户的任务列表
    """
    task_service = get_async_task_service(db)
    tasks, total = await task_service.list_user_tasks(
        user_id=current_user.id,
        status_filter=status_filter,
        task_type=task_type,
        limit=limit,
        offset=offset,
    )

    return {
        "code": 0,
        "message": "success",
        "data": {
            "items": [t.to_api_response() for t in tasks],
            "total": total,
            "limit": limit,
            "offset": offset,
            "hasMore": offset + limit < total,
        }
    }


@router.delete("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Dict[str, Any]:
    """
    取消进行中的任务
    """
    task_service = get_async_task_service(db)
    task = await task_service.cancel_task(task_id, current_user.id)

    return {
        "code": 0,
        "message": "任务已取消",
        "data": task.to_api_response(),
    }


@router.post("/tasks/{task_id}/retry")
async def retry_task(
    task_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Dict[str, Any]:
    """
    重试失败的任务
    """
    task_service = get_async_task_service(db)
    task = await task_service.retry_task(task_id, current_user.id)

    return {
        "code": 0,
        "message": "任务已重试",
        "data": task.to_api_response(),
    }


@router.get("/tasks/active-count")
async def get_active_tasks_count(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Dict[str, Any]:
    """
    获取当前用户活跃任务数量
    """
    task_service = get_async_task_service(db)
    count = await task_service.get_active_tasks_count(current_user.id)

    return {
        "code": 0,
        "message": "success",
        "data": {"activeCount": count},
    }
