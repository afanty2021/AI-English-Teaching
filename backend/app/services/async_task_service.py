"""
异步任务服务 - AI英语教学系统
负责异步任务的创建、查询、状态管理和取消操作
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User
from app.models.async_task import AsyncTask, AsyncTaskStatus, AsyncTaskType
from fastapi import HTTPException, status


class AsyncTaskService:
    """异步任务服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(
        self,
        user_id: uuid.UUID,
        task_type: str,
        input_params: Optional[Dict[str, Any]] = None,
        priority: int = 0,
    ) -> AsyncTask:
        """
        创建新的异步任务

        Args:
            user_id: 用户ID
            task_type: 任务类型 (report_export, batch_export)
            input_params: 任务输入参数
            priority: 任务优先级

        Returns:
            AsyncTask: 创建的任务实例
        """
        # 验证任务类型
        if task_type not in [t.value for t in AsyncTaskType]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的任务类型: {task_type}"
            )

        task = AsyncTask(
            user_id=user_id,
            task_type=task_type,
            status=AsyncTaskStatus.PENDING.value,
            progress=0,
            input_params=input_params,
            priority=priority,
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def get_task_status(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        获取任务状态

        Args:
            task_id: 任务ID
            user_id: 用户ID（用于权限验证）

        Returns:
            dict: 任务状态信息

        Raises:
            HTTPException: 任务不存在或无权限
        """
        result = await self.db.execute(
            select(AsyncTask)
            .where(AsyncTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        # 验证任务归属
        if task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此任务"
            )

        return task.to_api_response()

    async def update_task_progress(
        self,
        task_id: uuid.UUID,
        progress: int,
        message: Optional[str] = None,
    ) -> AsyncTask:
        """
        更新任务进度

        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            message: 状态消息

        Returns:
            AsyncTask: 更新后的任务实例

        Raises:
            HTTPException: 任务不存在
        """
        result = await self.db.execute(
            select(AsyncTask)
            .where(AsyncTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        task.progress = max(0, min(100, progress))
        task.updated_at = datetime.utcnow()

        if message:
            task.input_params = {
                **(task.input_params or {}),
                "status_message": message
            }

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def complete_task(
        self,
        task_id: uuid.UUID,
        result_url: Optional[str] = None,
        result_details: Optional[Dict[str, Any]] = None,
    ) -> AsyncTask:
        """
        标记任务完成

        Args:
            task_id: 任务ID
            result_url: 结果文件URL
            result_details: 结果详细信息

        Returns:
            AsyncTask: 更新后的任务实例

        Raises:
            HTTPException: 任务不存在
        """
        result = await self.db.execute(
            select(AsyncTask)
            .where(AsyncTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        task.status = AsyncTaskStatus.COMPLETED.value
        task.progress = 100
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()

        if result_url:
            task.result_url = result_url

        if result_details:
            task.result_details = result_details

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def fail_task(
        self,
        task_id: uuid.UUID,
        error_message: str,
        can_retry: bool = True,
    ) -> AsyncTask:
        """
        标记任务失败

        Args:
            task_id: 任务ID
            error_message: 错误信息
            can_retry: 是否可重试

        Returns:
            AsyncTask: 更新后的任务实例

        Raises:
            HTTPException: 任务不存在
        """
        result = await self.db.execute(
            select(AsyncTask)
            .where(AsyncTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        task.status = AsyncTaskStatus.FAILED.value
        task.error_message = error_message
        task.updated_at = datetime.utcnow()

        if can_retry and task.retry_count < task.max_retries:
            # 准备重置为pending状态以便重试
            task.retry_count += 1

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def cancel_task(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> AsyncTask:
        """
        取消任务

        Args:
            task_id: 任务ID
            user_id: 用户ID（用于权限验证）

        Returns:
            AsyncTask: 更新后的任务实例

        Raises:
            HTTPException: 任务不存在、无权限或任务已完成
        """
        result = await self.db.execute(
            select(AsyncTask)
            .where(AsyncTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        # 验证任务归属
        if task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权取消此任务"
            )

        # 检查任务状态
        if task.status in (AsyncTaskStatus.COMPLETED.value, AsyncTaskStatus.FAILED.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无法取消状态为 {task.status} 的任务"
            )

        task.status = AsyncTaskStatus.CANCELLED.value
        task.updated_at = datetime.utcnow()
        task.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def list_user_tasks(
        self,
        user_id: uuid.UUID,
        status_filter: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List[AsyncTask], int]:
        """
        获取用户的任务列表

        Args:
            user_id: 用户ID
            status_filter: 状态筛选
            task_type: 任务类型筛选
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            (任务列表, 总数)
        """
        # 构建查询
        query = select(AsyncTask).where(AsyncTask.user_id == user_id)

        if status_filter:
            query = query.where(AsyncTask.status == status_filter)

        if task_type:
            query = query.where(AsyncTask.task_type == task_type)

        # 查询总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 查询列表
        query = query.order_by(AsyncTask.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        tasks = result.scalars().all()

        return list(tasks), total

    async def get_active_tasks_count(
        self,
        user_id: uuid.UUID,
    ) -> int:
        """
        获取用户活跃任务数量

        Args:
            user_id: 用户ID

        Returns:
            int: 活跃任务数量
        """
        result = await self.db.execute(
            select(func.count(AsyncTask.id))
            .where(
                and_(
                    AsyncTask.user_id == user_id,
                    AsyncTask.status.in_([
                        AsyncTaskStatus.PENDING.value,
                        AsyncTaskStatus.PROCESSING.value,
                    ])
                )
            )
        )
        return result.scalar() or 0

    async def cleanup_old_tasks(
        self,
        days: int = 30,
        statuses: Optional[List[str]] = None,
    ) -> int:
        """
        清理旧任务（删除已完成或失败超过指定天数的任务）

        Args:
            days: 任务完成后经过的天数
            statuses: 要清理的状态列表

        Returns:
            int: 删除的任务数量
        """
        if statuses is None:
            statuses = [AsyncTaskStatus.COMPLETED.value, AsyncTaskStatus.FAILED.value, AsyncTaskStatus.CANCELLED.value]

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # 获取要删除的任务
        result = await self.db.execute(
            select(AsyncTask.id)
            .where(
                and_(
                    AsyncTask.status.in_(statuses),
                    AsyncTask.completed_at != None,  # noqa: E711
                    AsyncTask.completed_at < cutoff_date
                )
            )
        )
        task_ids = [row[0] for row in result.all()]

        if not task_ids:
            return 0

        # 删除任务
        await self.db.execute(
            AsyncTask.__table__.delete()
            .where(AsyncTask.id.in_(task_ids))
        )
        await self.db.commit()

        return len(task_ids)

    async def retry_task(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> AsyncTask:
        """
        重试失败的任务

        Args:
            task_id: 任务ID
            user_id: 用户ID（用于权限验证）

        Returns:
            AsyncTask: 重置后的任务实例

        Raises:
            HTTPException: 任务不存在、无权限或不可重试
        """
        result = await self.db.execute(
            select(AsyncTask)
            .where(AsyncTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        # 验证任务归属
        if task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权重试此任务"
            )

        # 检查是否可以重试
        if not task.can_retry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="任务不可重试或已达到最大重试次数"
            )

        # 重置任务状态
        task.status = AsyncTaskStatus.PENDING.value
        task.progress = 0
        task.error_message = None
        task.updated_at = datetime.utcnow()
        task.completed_at = None

        await self.db.commit()
        await self.db.refresh(task)

        return task


def get_async_task_service(db: AsyncSession) -> AsyncTaskService:
    """获取异步任务服务实例"""
    return AsyncTaskService(db)
