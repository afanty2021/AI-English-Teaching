"""
学习报告API v1
提供学习报告的生成、查询、导出等端点
"""
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User, UserRole
from app.services.learning_report_service import get_learning_report_service
from app.services.report_export_service import get_report_export_service

router = APIRouter()


@router.post("/generate", response_model=dict, status_code=status.HTTP_201_CREATED)
async def generate_report(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    report_data: dict,
) -> Any:
    """
    生成学习报告

    学生可以手动生成自己的学习报告，支持自定义时间范围。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是学生）
        report_data: 报告参数，包含：
            - report_type: 报告类型 (weekly, monthly, custom)
            - period_start: 开始时间（可选，默认30天前）
            - period_end: 结束时间（可选，默认当前时间）

    Returns:
        dict: 生成的报告数据

    Raises:
        HTTPException 400: 参数错误
        HTTPException 403: 权限不足
    """
    # 权限检查：只有学生可以生成报告
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以生成学习报告"
        )

    # 检查学生档案是否存在
    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生档案不存在，请先完善个人信息"
        )

    student_id = current_user.student_profile.id

    # 获取参数
    report_type = report_data.get("report_type", "custom")

    # 处理时间参数
    from datetime import datetime

    period_start = None
    period_end = None

    if "period_start" in report_data:
        try:
            period_start = datetime.fromisoformat(report_data["period_start"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="period_start 格式错误，应为 ISO 8601 格式"
            )

    if "period_end" in report_data:
        try:
            period_end = datetime.fromisoformat(report_data["period_end"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="period_end 格式错误，应为 ISO 8601 格式"
            )

    # 生成报告
    service = get_learning_report_service(db)
    report = await service.generate_report(
        student_id=student_id,
        report_type=report_type,
        period_start=period_start,
        period_end=period_end,
    )

    # 将报告保存到数据库（如果需要）
    # 当前采用实时生成方式，不保存快照

    return {
        "report": report,
        "message": "学习报告生成成功"
    }


@router.get("/me", response_model=dict)
async def get_my_reports(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    report_type: Optional[str] = Query(None, description="报告类型筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
) -> Any:
    """
    获取我的学习报告列表

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是学生）
        report_type: 报告类型筛选
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        dict: 报告列表和总数

    Raises:
        HTTPException 403: 权限不足
    """
    # 权限检查：只有学生可以查看自己的报告
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以查看自己的学习报告"
        )

    # 检查学生档案是否存在
    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生档案不存在，请先完善个人信息"
        )

    student_id = current_user.student_profile.id

    # 获取报告列表
    service = get_learning_report_service(db)
    reports, total = await service.get_student_reports(
        student_id=student_id,
        limit=limit,
        offset=offset,
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "reports": [
            {
                "id": str(report.id),
                "report_type": report.report_type,
                "period_start": report.period_start.isoformat(),
                "period_end": report.period_end.isoformat(),
                "status": report.status,
                "title": report.title,
                "created_at": report.created_at.isoformat(),
            }
            for report in reports
        ]
    }


@router.get("/{report_id}", response_model=dict)
async def get_report_detail(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    report_id: str,
) -> Any:
    """
    获取学习报告详情

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        report_id: 报告ID

    Returns:
        dict: 报告详情

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 报告不存在
    """
    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的报告ID格式"
        )

    # 获取报告
    from app.models.learning_report import LearningReport

    result = await db.execute(
        select(LearningReport).where(LearningReport.id == report_uuid)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在"
        )

    # 权限检查：只能查看自己的报告
    if current_user.role == UserRole.STUDENT:
        if not current_user.student_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学生档案不存在，请先完善个人信息"
            )
        if report.student_id != current_user.student_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看此报告"
            )

    return {
        "id": str(report.id),
        "student_id": str(report.student_id),
        "report_type": report.report_type,
        "period_start": report.period_start.isoformat(),
        "period_end": report.period_end.isoformat(),
        "status": report.status,
        "title": report.title,
        "description": report.description,
        "statistics": report.statistics,
        "ability_analysis": report.ability_analysis,
        "weak_points": report.weak_points,
        "recommendations": report.recommendations,
        "ai_insights": report.ai_insights,
        "created_at": report.created_at.isoformat(),
        "updated_at": report.updated_at.isoformat(),
    }


@router.post("/{report_id}/export")
async def export_report(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    report_id: str,
    format_type: str = Query("pdf", description="导出格式: pdf, image"),
) -> Any:
    """
    导出学习报告

    支持导出为 PDF 文件或图片。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是学生）
        report_id: 报告ID
        format_type: 导出格式 (pdf, image)

    Returns:
        StreamingResponse: 文件流

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 报告不存在
        HTTPException 400: 参数错误
    """
    # 权限检查：只有学生可以导出自己的报告
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以导出学习报告"
        )

    # 检查学生档案是否存在
    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生档案不存在，请先完善个人信息"
        )

    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的报告ID格式"
        )

    # 验证导出格式
    valid_formats = ["pdf", "image"]
    if format_type not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的导出格式: {format_type}。支持的格式: {', '.join(valid_formats)}"
        )

    try:
        # 获取导出服务
        export_service = get_report_export_service(db)

        # 获取报告详情（用于验证权限）
        from app.models.learning_report import LearningReport

        result = await db.execute(
            select(LearningReport).where(LearningReport.id == report_uuid)
        )
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报告不存在"
            )

        # 权限检查
        if report.student_id != current_user.student_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权导出此报告"
            )

        # 准备报告数据
        report_data = {
            "id": str(report.id),
            "report_type": report.report_type,
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
            "title": report.title or f"{report.report_type}报告",
            "statistics": report.statistics or {},
            "ability_analysis": report.ability_analysis or {},
            "weak_points": report.weak_points or {},
            "recommendations": report.recommendations or {},
            "ai_insights": report.ai_insights,
        }

        # 如果报告数据为空（实时报告），需要先生成
        if not report.statistics:
            service = get_learning_report_service(db)
            full_report = await service.generate_report(
                student_id=report.student_id,
                report_type=report.report_type,
                period_start=report.period_start,
                period_end=report.period_end,
            )
            report_data.update(full_report)

        # 根据格式选择导出方法
        if format_type == "pdf":
            filename, content = await export_service.export_as_pdf(report_data)
            media_type = "application/pdf"

        else:  # image
            filename, content = await export_service.export_as_image(report_data)
            media_type = "image/png"

        # 创建文件流
        def iterfile():
            yield content

        # 编码文件名以支持中文
        from urllib.parse import quote
        encoded_filename = quote(filename)

        return StreamingResponse(
            iterfile(),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )

    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}"
        )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    report_id: str,
) -> None:
    """
    删除学习报告

    注意：删除操作不可恢复，请谨慎使用。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        report_id: 报告ID

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 报告不存在
    """
    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的报告ID格式"
        )

    # 获取报告
    from app.models.learning_report import LearningReport

    result = await db.execute(
        select(LearningReport).where(LearningReport.id == report_uuid)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在"
        )

    # 权限检查：学生只能删除自己的报告
    if current_user.role == UserRole.STUDENT:
        if not current_user.student_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学生档案不存在"
            )
        if report.student_id != current_user.student_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此报告"
            )

    # 删除报告
    await db.delete(report)
    await db.commit()
