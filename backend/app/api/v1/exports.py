"""
流式导出 API 路由 - AI英语教学系统
支持教案流式导出，边生成边传输，优化内存使用
"""
import logging
import uuid
from typing import AsyncIterator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_teacher, get_db
from app.models import User, UserRole
from app.models.export_task import ExportFormat
from app.models.lesson_plan import LessonPlan
from app.services.content_renderer_service import ContentRendererService
from app.services.streaming_document_service import get_streaming_document_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/stream")
async def stream_export_lesson_plan(
    lesson_plan_id: uuid.UUID,
    format: str = Query(..., description="导出格式: word, pdf, pptx"),
    template_id: Optional[uuid.UUID] = Query(None, description="可选的模板ID"),
    include_sections: Optional[List[str]] = Query(None, description="要包含的章节列表"),
    chunk_size: int = Query(8192, ge=1024, le=1048576, description="数据块大小（字节）"),
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    流式导出教案

    支持 Word、PDF、PPTX 格式的流式导出，边生成边传输，优化内存使用。

    Args:
        lesson_plan_id: 教案ID
        format: 导出格式 (word, pdf, pptx)
        template_id: 可选的模板ID
        include_sections: 要包含的章节列表
        chunk_size: 数据块大小（字节），范围 1024-1048576
        current_user: 当前教师用户
        db: 数据库会话

    Returns:
        StreamingResponse: 流式响应

    Raises:
        HTTPException: 如果教案不存在、格式不支持或无权访问
    """
    # 1. 验证格式
    try:
        export_format = ExportFormat(format)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的导出格式: {format}。支持的格式: word, pdf, pptx"
        )

    # 2. 获取教案
    from sqlalchemy import select
    result = await db.execute(
        select(LessonPlan).where(LessonPlan.id == lesson_plan_id)
    )
    lesson_plan = result.scalar_one_or_none()

    if not lesson_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教案不存在"
        )

    # 3. 验证权限（教师只能导出自己的教案，管理员可以导出所有）
    if (
        current_user.role == UserRole.TEACHER
        and not current_user.is_superuser
        and lesson_plan.teacher_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权导出此教案"
        )

    # 4. 渲染内容
    renderer = ContentRendererService(format="markdown")
    try:
        rendered_content = renderer.render_lesson_plan(
            lesson_plan,
            include_sections=include_sections
        )
    except Exception as e:
        logger.error(f"渲染教案内容失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"渲染教案内容失败: {str(e)}"
        )

    # 5. 准备模板变量
    template_vars = {
        "title": lesson_plan.title,
        "topic": lesson_plan.topic,
        "level": lesson_plan.level,
        "duration": lesson_plan.duration,
        "target_exam": lesson_plan.target_exam or "",
        "teacher_name": current_user.full_name or current_user.username,
        "rendered_content": rendered_content,
    }

    # 6. 准备内容数据
    content_data = {
        "title": lesson_plan.title,
        "topic": lesson_plan.topic,
        "level": lesson_plan.level,
        "duration": lesson_plan.duration,
        "target_exam": lesson_plan.target_exam,
        "objectives": lesson_plan.objectives,
        "vocabulary": lesson_plan.vocabulary,
        "grammar_points": lesson_plan.grammar_points,
        "teaching_structure": lesson_plan.teaching_structure,
        "leveled_materials": lesson_plan.leveled_materials,
        "exercises": lesson_plan.exercises,
        "ppt_outline": lesson_plan.ppt_outline,
        "resources": lesson_plan.resources,
        "teaching_notes": lesson_plan.teaching_notes,
    }

    # 7. 流式生成文档
    streaming_service = get_streaming_document_service()

    # 定义异步生成器函数
    async def generate_document() -> AsyncIterator[bytes]:
        """生成文档数据块"""
        try:
            if export_format == ExportFormat.WORD:
                async for chunk in streaming_service.stream_generate_word(
                    content=content_data,
                    template_vars=template_vars,
                    chunk_size=chunk_size,
                ):
                    yield chunk

            elif export_format == ExportFormat.PDF:
                async for chunk in streaming_service.stream_generate_pdf(
                    lesson_plan=lesson_plan,
                    chunk_size=chunk_size,
                    include_sections=include_sections,
                ):
                    yield chunk

            elif export_format == ExportFormat.PPTX:
                async for chunk in streaming_service.stream_generate_pptx(
                    content=content_data,
                    template_vars=template_vars,
                    chunk_size=chunk_size,
                ):
                    yield chunk

        except Exception as e:
            logger.error(f"流式生成文档失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文档生成失败: {str(e)}"
            )

    # 8. 确定媒体类型和文件名
    media_types = {
        ExportFormat.WORD: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ExportFormat.PDF: "application/pdf",
        ExportFormat.PPTX: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }

    file_extensions = {
        ExportFormat.WORD: "docx",
        ExportFormat.PDF: "pdf",
        ExportFormat.PPTX: "pptx",
    }

    media_type = media_types[export_format]
    file_extension = file_extensions[export_format]

    # URL 编码文件名以支持中文
    from urllib.parse import quote
    safe_filename = quote(f"教案-{lesson_plan.title}-{lesson_plan.level}.{file_extension}", safe='')

    # 9. 返回流式响应
    return StreamingResponse(
        generate_document(),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename*=UTF-8\'\'{safe_filename}',
            "Cache-Control": "no-cache",
        }
    )


@router.get("/formats")
async def list_export_formats(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    获取支持的导出格式列表

    Returns:
        包含支持格式的字典
    """
    return {
        "formats": [
            {
                "value": ExportFormat.WORD.value,
                "label": "Word文档",
                "extension": "docx",
                "media_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            },
            {
                "value": ExportFormat.PDF.value,
                "label": "PDF文档",
                "extension": "pdf",
                "media_type": "application/pdf",
            },
            {
                "value": ExportFormat.PPTX.value,
                "label": "PowerPoint演示",
                "extension": "pptx",
                "media_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            },
        ]
    }
