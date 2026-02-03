"""
对话 API v1 - 异步版本
提供 AI 口语陪练相关端点
"""
import uuid
import json
from datetime import datetime
from typing import List, Optional, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_user, get_current_student
from app.models import User, Student, Conversation, ConversationScenario
from app.schemas.conversation import (
    CreateConversationRequest,
    SendMessageRequest,
    ConversationResponse,
    ConversationDetailResponse,
    SendMessageResponse,
    CompleteConversationResponse,
    ScenariosListResponse,
    ScenarioInfo,
    MessageSchema,
    ConversationScores,
)
from app.services.conversation_service import get_conversation_service

router = APIRouter()


async def _stream_ai_response(
    response_text: str
) -> AsyncGenerator[str, None]:
    """
    流式生成 AI 响应

    Args:
        response_text: 完整的 AI 响应文本

    Yields:
        SSE 格式的数据流
    """
    # 模拟逐字流式输出
    words = response_text.split()
    accumulated = ""

    for i, word in enumerate(words):
        accumulated += word + " "

        # 发送 token 事件
        chunk = {
            "type": "token",
            "content": word + " ",
            "index": i
        }
        yield f"data: {json.dumps(chunk)}\n\n"

        # 模拟网络延迟
        await asyncio.sleep(0.03)

    # 发送完成事件
    complete_chunk = {
        "type": "complete",
        "full_message": accumulated.strip(),
        "total_tokens": len(words)
    }
    yield f"data: {json.dumps(complete_chunk)}\n\n"

    # 发送结束标记
    yield "data: [DONE]\n\n"


import asyncio


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建新对话",
    description="创建一个新的 AI 口语练习对话会话"
)
async def create_conversation(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: CreateConversationRequest
) -> ConversationResponse:
    """
    创建新的对话会话

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        request: 对话创建请求

    Returns:
        创建的对话信息

    Raises:
        HTTPException: 如果学生不存在或验证失败
    """
    # 获取当前用户的学生信息
    result = await db.execute(
        select(Student).where(Student.user_id == current_user.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到学生档案，请先完善个人信息"
        )

    # 转换 schema 枚举到模型枚举
    scenario_enum = ConversationScenario(request.scenario.value)

    # 创建对话
    service = get_conversation_service()
    try:
        conversation = await service.create_conversation(
            db=db,
            student_id=str(student.id),
            scenario=scenario_enum,
            level=request.level
        )
        await db.commit()
        await db.refresh(conversation)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return ConversationResponse(
        id=str(conversation.id),
        student_id=str(conversation.student_id),
        scenario=conversation.scenario.value,
        level=conversation.level,
        status=conversation.status.value,
        message_count=len(conversation.get_messages()),
        started_at=conversation.started_at,
        completed_at=conversation.completed_at
    )


@router.post(
    "/{conversation_id}/message",
    response_model=SendMessageResponse,
    summary="发送消息",
    description="在对话中发送用户消息并获取 AI 回复"
)
async def send_message(
    conversation_id: str,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: SendMessageRequest
) -> SendMessageResponse:
    """
    在对话中发送消息

    Args:
        conversation_id: 对话 ID (UUID)
        db: 数据库会话
        current_user: 当前认证用户
        request: 消息请求

    Returns:
        AI 的回复

    Raises:
        HTTPException: 如果对话不存在或未激活
    """
    # 验证学生拥有此对话
    result = await db.execute(
        select(Student).where(Student.user_id == current_user.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到学生档案"
        )

    # 验证对话属于该学生
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == uuid.UUID(conversation_id),
            Conversation.student_id == student.id
        )
    )
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )

    # 发送消息
    service = get_conversation_service()
    try:
        ai_response = await service.send_message(
            db=db,
            conversation_id=conversation_id,
            user_message=request.message
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return SendMessageResponse(
        message_id=None,
        role="assistant",
        content=ai_response,
        timestamp=datetime.utcnow().isoformat()
    )


@router.get(
    "/{conversation_id}/message/stream",
    summary="发送消息（流式）",
    description="发送用户消息并以流式方式获取 AI 回复（SSE）"
)
async def send_message_stream(
    conversation_id: str,
    message: str,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """
    流式发送消息

    Args:
        conversation_id: 对话 ID (UUID)
        message: 用户消息内容
        db: 数据库会话
        current_user: 当前认证用户

    Returns:
        SSE 格式的流式响应

    Raises:
        HTTPException: 如果对话不存在或未激活
    """
    # 验证学生拥有此对话
    result = await db.execute(
        select(Student).where(Student.user_id == current_user.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到学生档案"
        )

    # 验证对话属于该学生
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == uuid.UUID(conversation_id),
            Conversation.student_id == student.id
        )
    )
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )

    # 发送消息获取完整响应
    service = get_conversation_service()
    try:
        ai_response = await service.send_message(
            db=db,
            conversation_id=conversation_id,
            user_message=message
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # 返回流式响应
    return StreamingResponse(
        _stream_ai_response(ai_response),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post(
    "/{conversation_id}/complete",
    response_model=CompleteConversationResponse,
    summary="完成对话",
    description="结束对话会话并获取表现评分"
)
async def complete_conversation(
    conversation_id: str,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CompleteConversationResponse:
    """
    完成对话并获取评分

    Args:
        conversation_id: 对话 ID (UUID)
        db: 数据库会话
        current_user: 当前认证用户

    Returns:
        包含评分的对话完成信息

    Raises:
        HTTPException: 如果对话不存在或已完成
    """
    # 验证学生拥有此对话
    result = await db.execute(
        select(Student).where(Student.user_id == current_user.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到学生档案"
        )

    # 验证对话属于该学生
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == uuid.UUID(conversation_id),
            Conversation.student_id == student.id
        )
    )
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )

    # 完成对话
    service = get_conversation_service()
    try:
        scores = await service.complete_conversation(
            db=db,
            conversation_id=conversation_id
        )
        await db.commit()
        await db.refresh(conversation)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return CompleteConversationResponse(
        conversation_id=str(conversation.id),
        status=conversation.status.value,
        completed_at=conversation.completed_at,
        scores=ConversationScores(**scores),
        message_count=len(conversation.get_messages()),
        duration_seconds=conversation.calculate_duration_seconds()
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="获取对话详情",
    description="获取指定对话的详细信息"
)
async def get_conversation(
    conversation_id: str,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ConversationDetailResponse:
    """
    获取对话详情

    Args:
        conversation_id: 对话 ID (UUID)
        db: 数据库会话
        current_user: 当前认证用户

    Returns:
        详细对话信息

    Raises:
        HTTPException: 如果对话不存在
    """
    # 验证学生拥有此对话
    result = await db.execute(
        select(Student).where(Student.user_id == current_user.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到学生档案"
        )

    # 获取对话
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == uuid.UUID(conversation_id),
            Conversation.student_id == student.id
        )
    )
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )

    # 获取消息
    messages_data = conversation.get_messages()
    messages = [
        MessageSchema(
            role=msg["role"],
            content=msg["content"],
            timestamp=msg.get("timestamp")
        )
        for msg in messages_data
    ]

    # 构建评分（如果已完成）
    scores = None
    if conversation.status.value == "completed":
        scores = ConversationScores(
            fluency_score=conversation.fluency_score,
            vocabulary_score=conversation.vocabulary_score,
            grammar_score=conversation.grammar_score,
            overall_score=conversation.overall_score,
            feedback=conversation.feedback
        )

    return ConversationDetailResponse(
        id=str(conversation.id),
        student_id=str(conversation.student_id),
        scenario=conversation.scenario.value,
        level=conversation.level,
        status=conversation.status.value,
        messages=messages,
        started_at=conversation.started_at,
        completed_at=conversation.completed_at,
        scores=scores
    )


@router.get(
    "",
    response_model=List[ConversationResponse],
    summary="获取对话列表",
    description="获取当前学生的所有对话列表"
)
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ConversationResponse]:
    """
    获取当前学生的对话列表

    Args:
        skip: 跳过记录数
        limit: 返回记录上限
        db: 数据库会话
        current_user: 当前认证用户

    Returns:
        对话列表
    """
    # 获取学生
    result = await db.execute(
        select(Student).where(Student.user_id == current_user.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        return []

    # 获取对话
    service = get_conversation_service()
    conversations = await service.list_conversations(
        db=db,
        student_id=str(student.id),
        skip=skip,
        limit=limit
    )

    return [
        ConversationResponse(
            id=str(c.id),
            student_id=str(c.student_id),
            scenario=c.scenario.value,
            level=c.level,
            status=c.status.value,
            message_count=len(c.get_messages()),
            started_at=c.started_at,
            completed_at=c.completed_at
        )
        for c in conversations
    ]


@router.get(
    "/scenarios/available",
    response_model=ScenariosListResponse,
    summary="获取可用场景",
    description="获取所有可用的对话场景列表"
)
async def get_available_scenarios() -> ScenariosListResponse:
    """
    获取可用的对话场景列表

    Returns:
        可用场景列表
    """
    service = get_conversation_service()
    scenarios = service.get_available_scenarios()

    scenario_objects = [
        ScenarioInfo(**scenario)
        for scenario in scenarios
    ]

    return ScenariosListResponse(scenarios=scenario_objects)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除对话",
    description="删除对话（仅限非活跃对话）"
)
async def delete_conversation(
    conversation_id: str,
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    删除对话

    Args:
        conversation_id: 对话 ID (UUID)
        db: 数据库会话
        current_user: 当前认证用户

    Raises:
        HTTPException: 如果对话不存在或活跃中
    """
    # 验证学生拥有此对话
    result = await db.execute(
        select(Student).where(Student.user_id == current_user.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到学生档案"
        )

    # 获取对话
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == uuid.UUID(conversation_id),
            Conversation.student_id == student.id
        )
    )
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )

    # 不能删除活跃对话
    if conversation.status.value == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法删除活跃对话，请先完成对话"
        )

    await db.delete(conversation)
    await db.commit()
