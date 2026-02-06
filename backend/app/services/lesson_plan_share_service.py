"""
教案分享服务 - AI英语教学系统

处理教师间教案分享的业务逻辑。
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import LessonPlan, LessonPlanShare, SharePermission, ShareStatus, User


class LessonPlanShareService:
    """教案分享服务类"""

    async def create_share(
        self,
        db: AsyncSession,
        lesson_plan_id: uuid.UUID,
        shared_by_id: uuid.UUID,
        shared_to_id: uuid.UUID,
        permission: SharePermission,
        message: Optional[str] = None,
        expires_days: Optional[int] = None,
    ) -> LessonPlanShare:
        """
        创建教案分享

        Args:
            db: 数据库会话
            lesson_plan_id: 教案ID
            shared_by_id: 分享者ID
            shared_to_id: 接收者ID
            permission: 分享权限
            message: 分享附言
            expires_days: 有效期天数

        Returns:
            LessonPlanShare: 创建的分享记录

        Raises:
            ValueError: 如果教案不存在或无权分享
        """
        # 验证教案存在且属于分享者
        lesson_plan = await db.get(LessonPlan, lesson_plan_id)
        if not lesson_plan:
            raise ValueError("教案不存在")

        if lesson_plan.teacher_id != shared_by_id:
            raise ValueError("无权分享此教案")

        # 不能分享给自己
        if shared_by_id == shared_to_id:
            raise ValueError("不能分享给自己")

        # 检查是否已存在待处理或已接受的分享
        existing_share = await db.execute(
            select(LessonPlanShare).where(
                and_(
                    LessonPlanShare.lesson_plan_id == lesson_plan_id,
                    LessonPlanShare.shared_to == shared_to_id,
                    LessonPlanShare.status.in_([
                        ShareStatus.PENDING.value,
                        ShareStatus.ACCEPTED.value
                    ])
                )
            )
        )
        if existing_share.scalar_one_or_none():
            raise ValueError("该教案已经分享给此用户")

        # 计算过期时间
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)

        # 创建分享记录
        share = LessonPlanShare(
            lesson_plan_id=lesson_plan_id,
            shared_by=shared_by_id,
            shared_to=shared_to_id,
            permission=permission.value,
            status=ShareStatus.PENDING.value,
            message=message,
            expires_at=expires_at,
        )

        db.add(share)

        # 更新教案的分享状态和计数
        lesson_plan.is_shared = True
        lesson_plan.share_count = (lesson_plan.share_count or 0) + 1

        await db.commit()
        await db.refresh(share)

        return share

    async def accept_share(
        self,
        db: AsyncSession,
        share_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> LessonPlanShare:
        """
        接受分享

        Args:
            db: 数据库会话
            share_id: 分享记录ID
            user_id: 当前用户ID

        Returns:
            LessonPlanShare: 更新后的分享记录

        Raises:
            ValueError: 如果分享不存在或无权操作
        """
        share = await db.get(LessonPlanShare, share_id)
        if not share:
            raise ValueError("分享记录不存在")

        if share.shared_to != user_id:
            raise ValueError("无权操作此分享")

        if share.status != ShareStatus.PENDING.value:
            raise ValueError("该分享已被处理")

        if share.is_expired():
            share.status = ShareStatus.EXPIRED.value
            await db.commit()
            raise ValueError("分享已过期")

        share.status = ShareStatus.ACCEPTED.value
        await db.commit()
        await db.refresh(share)

        return share

    async def reject_share(
        self,
        db: AsyncSession,
        share_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> LessonPlanShare:
        """
        拒绝分享

        Args:
            db: 数据库会话
            share_id: 分享记录ID
            user_id: 当前用户ID

        Returns:
            LessonPlanShare: 更新后的分享记录

        Raises:
            ValueError: 如果分享不存在或无权操作
        """
        share = await db.get(LessonPlanShare, share_id)
        if not share:
            raise ValueError("分享记录不存在")

        if share.shared_to != user_id:
            raise ValueError("无权操作此分享")

        if share.status != ShareStatus.PENDING.value:
            raise ValueError("该分享已被处理")

        share.status = ShareStatus.REJECTED.value
        await db.commit()
        await db.refresh(share)

        return share

    async def cancel_share(
        self,
        db: AsyncSession,
        share_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """
        取消分享

        Args:
            db: 数据库会话
            share_id: 分享记录ID
            user_id: 当前用户ID

        Returns:
            bool: 是否成功取消

        Raises:
            ValueError: 如果分享不存在或无权操作
        """
        share = await db.get(LessonPlanShare, share_id)
        if not share:
            raise ValueError("分享记录不存在")

        if share.shared_by != user_id:
            raise ValueError("无权取消此分享")

        # 只能取消待处理或已接受的分享
        if share.status not in [
            ShareStatus.PENDING.value,
            ShareStatus.ACCEPTED.value
        ]:
            raise ValueError("该分享无法取消")

        # 更新教案的分享计数
        lesson_plan = await db.get(LessonPlan, share.lesson_plan_id)
        if lesson_plan and lesson_plan.share_count > 0:
            lesson_plan.share_count -= 1
            # 检查是否还有其他活跃的分享
            remaining_shares = await db.execute(
                select(func.count(LessonPlanShare.id)).where(
                    and_(
                        LessonPlanShare.lesson_plan_id == share.lesson_plan_id,
                        LessonPlanShare.status.in_([
                            ShareStatus.PENDING.value,
                            ShareStatus.ACCEPTED.value
                        ])
                    )
                )
            )
            remaining_count = remaining_shares.scalar() - 1  # 减去即将删除的这个
            if remaining_count == 0:
                lesson_plan.is_shared = False

        await db.delete(share)
        await db.commit()

        return True

    async def get_shared_with_me(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        status: Optional[ShareStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LessonPlanShare], int]:
        """
        获取分享给我的教案列表

        Args:
            db: 数据库会话
            user_id: 当前用户ID
            status: 状态筛选
            page: 页码
            page_size: 每页大小

        Returns:
            tuple[list[LessonPlanShare], int]: (分享列表, 总数)
        """
        # 构建查询
        query = select(LessonPlanShare).where(
            LessonPlanShare.shared_to == user_id
        )

        # 应用状态筛选
        if status:
            query = query.where(LessonPlanShare.status == status.value)
        else:
            # 默认只显示未过期且未被拒绝的分享
            query = query.where(
                or_(
                    LessonPlanShare.expires_at.is_(None),
                    LessonPlanShare.expires_at > datetime.utcnow()
                )
            )
            query = query.where(
                LessonPlanShare.status != ShareStatus.REJECTED.value
            )

        # 预加载关联数据
        query = query.options(
            selectinload(LessonPlanShare.lesson_plan),
            selectinload(LessonPlanShare.sharer),
            selectinload(LessonPlanShare.recipient)
        )

        # 计算总数
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        # 排序和分页
        query = query.order_by(LessonPlanShare.created_at.desc())
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        shares = result.scalars().all()

        return list(shares), total

    async def get_shared_by_me(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        status: Optional[ShareStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LessonPlanShare], int]:
        """
        获取我分享的教案列表

        Args:
            db: 数据库会话
            user_id: 当前用户ID
            status: 状态筛选
            page: 页码
            page_size: 每页大小

        Returns:
            tuple[list[LessonPlanShare], int]: (分享列表, 总数)
        """
        # 构建查询
        query = select(LessonPlanShare).where(
            LessonPlanShare.shared_by == user_id
        )

        # 应用状态筛选
        if status:
            query = query.where(LessonPlanShare.status == status.value)

        # 预加载关联数据
        query = query.options(
            selectinload(LessonPlanShare.lesson_plan),
            selectinload(LessonPlanShare.sharer),
            selectinload(LessonPlanShare.recipient)
        )

        # 计算总数
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        # 排序和分页
        query = query.order_by(LessonPlanShare.created_at.desc())
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        shares = result.scalars().all()

        return list(shares), total

    async def check_share_access(
        self,
        db: AsyncSession,
        lesson_plan_id: uuid.UUID,
        user_id: uuid.UUID,
        required_permission: SharePermission = SharePermission.VIEW,
    ) -> Optional[LessonPlanShare]:
        """
        检查用户对教案的分享访问权限

        Args:
            db: 数据库会话
            lesson_plan_id: 教案ID
            user_id: 用户ID
            required_permission: 所需权限

        Returns:
            Optional[LessonPlanShare]: 如果有权限返回分享记录，否则返回None
        """
        # 查找有效的分享记录
        share = await db.execute(
            select(LessonPlanShare).where(
                and_(
                    LessonPlanShare.lesson_plan_id == lesson_plan_id,
                    LessonPlanShare.shared_to == user_id,
                    LessonPlanShare.status == ShareStatus.ACCEPTED.value,
                    or_(
                        LessonPlanShare.expires_at.is_(None),
                        LessonPlanShare.expires_at > datetime.utcnow()
                    )
                )
            )
        )
        share = share.scalar_one_or_none()

        if not share:
            return None

        # 检查权限是否满足
        permission_order = {
            SharePermission.COPY.value: 3,  # 最高权限
            SharePermission.EDIT.value: 2,
            SharePermission.VIEW.value: 1,
        }

        if permission_order.get(share.permission, 0) < permission_order.get(required_permission.value, 0):
            return None

        return share


# 创建全局单例
_lesson_plan_share_service: Optional[LessonPlanShareService] = None


def get_lesson_plan_share_service() -> LessonPlanShareService:
    """
    获取教案分享服务单例

    Returns:
        LessonPlanShareService: 教案分享服务实例
    """
    global _lesson_plan_share_service
    if _lesson_plan_share_service is None:
        _lesson_plan_share_service = LessonPlanShareService()
    return _lesson_plan_share_service
