"""
智能复习服务 - AI英语教学系统
基于艾宾浩斯遗忘曲线提供智能错题复习提醒
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Mistake, MistakeStatus


class MistakeReviewService:
    """
    智能复习服务类

    功能：
    1. 基于艾宾浩斯遗忘曲线计算最佳复习时间
    2. 生成今日复习清单
    3. 识别即将遗忘的紧急复习项
    4. 提供复习统计数据
    5. 智能推荐复习题目

    艾宾浩斯复习间隔：
    - 第1次复习: 1天后
    - 第2次复习: 3天后
    - 第3次复习: 7天后
    - 第4次复习: 14天后
    - 第5次复习: 30天后
    """

    # 艾宾浩斯遗忘曲线复习间隔（天）
    EBINGHAUS_INTERVALS = [1, 3, 7, 14, 30]

    # 紧急复习阈值（小时）- 超过此时间未复习视为紧急
    URGENT_THRESHOLD_HOURS = 24

    def __init__(self, db: AsyncSession):
        """
        初始化智能复习服务

        Args:
            db: 数据库会话
        """
        self.db = db

    def _get_review_interval(self, review_count: int) -> int:
        """
        根据复习次数获取复习间隔

        Args:
            review_count: 已复习次数

        Returns:
            间隔天数
        """
        idx = min(review_count, len(self.EBINGHAUS_INTERVALS) - 1)
        return self.EBINGHAUS_INTERVALS[idx]

    def calculate_next_review_time(self, mistake: Mistake) -> datetime:
        """
        计算错题的最佳下次复习时间

        基于艾宾浩斯遗忘曲线：
        - 首次复习后1天
        - 第2次复习后3天
        - 第3次复习后7天
        - 以此类推...

        Args:
            mistake: 错题记录

        Returns:
            下次复习时间
        """
        # 获取间隔天数
        interval_days = self._get_review_interval(mistake.review_count)

        # 如果从未复习，基于首次错误时间
        if mistake.last_reviewed_at is None:
            return mistake.first_mistaken_at + timedelta(days=interval_days)

        # 基于上次复习时间计算
        return mistake.last_reviewed_at + timedelta(days=interval_days)

    def is_overdue(self, mistake: Mistake) -> bool:
        """
        判断错题是否已过期（需要紧急复习）

        Args:
            mistake: 错题记录

        Returns:
            是否已过期
        """
        next_review = self.calculate_next_review_time(mistake)
        return datetime.utcnow() > next_review

    def is_urgent(self, mistake: Mistake) -> bool:
        """
        判断错题是否紧急（接近或已过最佳复习时间）

        Args:
            mistake: 错题记录

        Returns:
            是否紧急
        """
        next_review = self.calculate_next_review_time(mistake)
        urgent_threshold = next_review - timedelta(hours=self.URGENT_THRESHOLD_HOURS)
        return datetime.utcnow() >= urgent_threshold

    def get_review_priority_score(self, mistake: Mistake) -> float:
        """
        计算复习优先级分数（越高越优先）

        优先级因素：
        1. 过期时间（越过期分数越高）
        2. 错误次数（越高越优先）
        3. 从未复习（优先复习）
        4. 复习次数（越少越优先）

        Args:
            mistake: 错题记录

        Returns:
            优先级分数
        """
        score = 0.0

        # 1. 过期时间权重（0-40分）
        if self.is_overdue(mistake):
            next_review = self.calculate_next_review_time(mistake)
            overdue_days = (datetime.utcnow() - next_review).days
            score += min(40, overdue_days * 10 + 20)
        elif self.is_urgent(mistake):
            score += 20  # 即将过期

        # 2. 错误次数权重（0-30分）
        score += min(30, mistake.mistake_count * 6)

        # 3. 从未复习奖励（10分）
        if mistake.review_count == 0:
            score += 10

        # 4. 复习次数惩罚（越复习越不优先，0-20分）
        score += max(0, 20 - mistake.review_count * 4)

        # 5. 新错题（最近7天内）额外奖励（10分）
        if mistake.first_mistaken_at > datetime.utcnow() - timedelta(days=7):
            score += 10

        return score

    async def get_today_review_list(
        self, student_id: UUID, limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取今日复习清单

        包含：
        - 已过期的错题
        - 即将过期的错题（24小时内）
        - 从未复习的新错题

        Args:
            student_id: 学生ID
            limit: 返回数量限制

        Returns:
            复习清单字典
        """
        # 获取需要复习的错题
        query = select(Mistake).where(
            and_(
                Mistake.student_id == student_id,
                Mistake.status.in_([
                    MistakeStatus.PENDING.value,
                    MistakeStatus.REVIEWING.value,
                ]),
            )
        )

        result = await self.db.execute(query)
        all_pending = result.scalars().all()

        # 分类
        overdue = []  # 已过期
        urgent = []  # 即将过期
        new_mistakes = []  # 新错题（从未复习）
        normal = []  # 正常复习

        now = datetime.utcnow()
        urgent_threshold = now - timedelta(hours=self.URGENT_THRESHOLD_HOURS)

        for mistake in all_pending:
            next_review = self.calculate_next_review_time(mistake)

            if mistake.review_count == 0:
                # 从未复习的新错题
                if now > mistake.first_mistaken_at + timedelta(days=1):
                    # 超过1天还没复习
                    overdue.append(mistake)
                elif now > mistake.first_mistaken_at:
                    # 今日需要复习
                    new_mistakes.append(mistake)
                else:
                    normal.append(mistake)
            elif now > next_review:
                # 已过期
                overdue.append(mistake)
            elif next_review > urgent_threshold:
                # 即将过期（24小时内）
                urgent.append(mistake)
            else:
                normal.append(mistake)

        # 计算优先级分数并排序
        def sort_key(m: Mistake) -> float:
            return -self.get_review_priority_score(m)

        overdue.sort(key=sort_key)
        urgent.sort(key=sort_key)
        new_mistakes.sort(key=sort_key)
        normal.sort(key=sort_key)

        # 合并结果
        prioritized = overdue + urgent + new_mistakes[:5] + normal[:limit - len(overdue) - len(urgent)]

        # 转换为字典列表
        today_list = [
            self._mistake_to_review_item(m, "overdue" if m in overdue else "urgent" if m in urgent else "new")
            for m in prioritized[:limit]
        ]

        return {
            "student_id": str(student_id),
            "date": now.strftime("%Y-%m-%d"),
            "total_count": len(all_pending),
            "today_count": len(today_list),
            "overdue_count": len(overdue),
            "urgent_count": len(urgent),
            "review_list": today_list,
        }

    async def get_urgent_review(
        self, student_id: UUID, limit: int = 10
    ) -> Dict[str, Any]:
        """
        获取紧急复习项（即将遗忘的错题）

        Args:
            student_id: 学生ID
            limit: 返回数量限制

        Returns:
            紧急复习列表
        """
        query = select(Mistake).where(
            and_(
                Mistake.student_id == student_id,
                Mistake.status.in_([
                    MistakeStatus.PENDING.value,
                    MistakeStatus.REVIEWING.value,
                ]),
            )
        )

        result = await self.db.execute(query)
        all_pending = result.scalars().all()

        # 筛选紧急项
        urgent_items = []
        for mistake in all_pending:
            if self.is_urgent(mistake):
                overdue_hours = 0
                if self.is_overdue(mistake):
                    next_review = self.calculate_next_review_time(mistake)
                    overdue_hours = int((datetime.utcnow() - next_review).total_seconds() / 3600)

                urgent_items.append(
                    self._mistake_to_review_item(mistake, "overdue" if overdue_hours > 0 else "urgent")
                )

        # 按紧急程度排序
        urgent_items.sort(key=lambda x: (-x["overdue_hours"], -x["mistake_count"]))

        return {
            "student_id": str(student_id),
            "total_urgent": len(urgent_items),
            "urgent_list": urgent_items[:limit],
        }

    async def get_review_statistics(self, student_id: UUID) -> Dict[str, Any]:
        """
        获取复习统计数据

        Args:
            student_id: 学生ID

        Returns:
            统计数据字典
        """
        # 获取所有错题
        query = select(Mistake).where(Mistake.student_id == student_id)
        result = await self.db.execute(query)
        all_mistakes = result.scalars().all()

        total = len(all_mistakes)
        if total == 0:
            return {
                "student_id": str(student_id),
                "total_mistakes": 0,
                "mastered_count": 0,
                "pending_count": 0,
                "review_count": 0,
                "mastery_rate": 0,
                "today_reviewed": 0,
                "streak_days": 0,
                "overdue_count": 0,
            }

        # 统计各状态
        status_counts: Dict[str, int] = {"pending": 0, "reviewing": 0, "mastered": 0, "ignored": 0}
        for m in all_mistakes:
            status_counts[m.status] = status_counts.get(m.status, 0) + 1

        # 计算掌握率
        mastered = status_counts.get("mastered", 0)
        mastery_rate = round(mastered / total * 100, 1) if total > 0 else 0

        # 计算今日复习数量
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_reviewed = sum(1 for m in all_mistakes if m.last_reviewed_at and m.last_reviewed_at >= today_start)

        # 统计过期数量
        overdue_count = sum(1 for m in all_mistakes if self.is_overdue(m))

        # 计算连续复习天数（简化版：基于今天是否复习）
        streak_days = 1 if today_reviewed > 0 else 0

        # 统计复习次数
        total_reviews = sum(m.review_count for m in all_mistakes)

        return {
            "student_id": str(student_id),
            "total_mistakes": total,
            "mastered_count": mastered,
            "pending_count": status_counts.get("pending", 0),
            "reviewing_count": status_counts.get("reviewing", 0),
            "review_count": total_reviews,
            "mastery_rate": mastery_rate,
            "today_reviewed": today_reviewed,
            "streak_days": streak_days,
            "overdue_count": overdue_count,
        }

    async def get_recommended_review(
        self, student_id: UUID, limit: int = 10
    ) -> Dict[str, Any]:
        """
        推荐复习题目（智能排序）

        基于优先级分数排序，推荐最需要复习的错题

        Args:
            student_id: 学生ID
            limit: 返回数量限制

        Returns:
            推荐复习列表
        """
        query = select(Mistake).where(
            and_(
                Mistake.student_id == student_id,
                Mistake.status.in_([
                    MistakeStatus.PENDING.value,
                    MistakeStatus.REVIEWING.value,
                ]),
            )
        )

        result = await self.db.execute(query)
        all_pending = result.scalars().all()

        # 计算优先级并排序
        scored = []
        for mistake in all_pending:
            score = self.get_review_priority_score(mistake)
            next_review = self.calculate_next_review_time(mistake)

            scored.append({
                "mistake": mistake,
                "score": score,
                "next_review": next_review,
                "is_overdue": self.is_overdue(mistake),
            })

        # 按分数降序排序
        scored.sort(key=lambda x: (-x["score"], x["next_review"]))

        # 获取前N个
        top_mistakes = scored[:limit]

        return {
            "student_id": str(student_id),
            "recommended_count": len(top_mistakes),
            "recommendations": [
                {
                    **self._mistake_to_review_item(m["mistake"], "overdue" if m["is_overdue"] else "normal"),
                    "priority_score": round(m["score"], 1),
                    "next_review_at": m["next_review"].strftime("%Y-%m-%d %H:%M"),
                }
                for m in top_mistakes
            ],
        }

    async def get_review_calendar(
        self, student_id: UUID, days: int = 30
    ) -> Dict[str, Any]:
        """
        获取复习日历（未来N天的复习计划）

        Args:
            student_id: 学生ID
            days: 天数

        Returns:
            复习日历
        """
        query = select(Mistake).where(
            and_(
                Mistake.student_id == student_id,
                Mistake.status.in_([
                    MistakeStatus.PENDING.value,
                    MistakeStatus.REVIEWING.value,
                ]),
            )
        )

        result = await self.db.execute(query)
        all_pending = result.scalars().all()

        # 按日期分组
        calendar: Dict[str, List[Dict]] = {}
        today = datetime.utcnow().date()

        for mistake in all_pending:
            next_review = self.calculate_next_review_time(mistake)
            review_date = next_review.date()

            # 只关注未来days天
            if review_date < today:
                review_date = today

            for i in range(days):
                date = today + timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")

                if date_str not in calendar:
                    calendar[date_str] = []

                if date == review_date:
                    calendar[date_str].append(
                        self._mistake_to_review_item(mistake, "scheduled")
                    )

        return {
            "student_id": str(student_id),
            "start_date": today.strftime("%Y-%m-%d"),
            "end_date": (today + timedelta(days=days - 1)).strftime("%Y-%m-%d"),
            "calendar": calendar,
        }

    def _mistake_to_review_item(
        self, mistake: Mistake, review_type: str = "normal"
    ) -> Dict[str, Any]:
        """
        将错题转换为复习项字典

        Args:
            mistake: 错题记录
            review_type: 复习类型

        Returns:
            复习项字典
        """
        next_review = self.calculate_next_review_time(mistake)
        overdue_hours = 0

        if self.is_overdue(mistake):
            overdue_hours = int(
                (datetime.utcnow() - next_review).total_seconds() / 3600
            )

        return {
            "id": str(mistake.id),
            "question_preview": mistake.question[:100] + "..." if len(mistake.question) > 100 else mistake.question,
            "mistake_type": mistake.mistake_type,
            "topic": mistake.topic,
            "mistake_count": mistake.mistake_count,
            "review_count": mistake.review_count,
            "status": mistake.status,
            "review_type": review_type,
            "next_review_at": next_review.strftime("%Y-%m-%d %H:%M"),
            "is_overdue": self.is_overdue(mistake),
            "overdue_hours": overdue_hours,
            "priority_score": self.get_review_priority_score(mistake),
        }


# 创建服务工厂函数
def get_mistake_review_service(db: AsyncSession) -> MistakeReviewService:
    """
    获取智能复习服务实例

    Args:
        db: 数据库会话

    Returns:
        MistakeReviewService: 智能复习服务实例
    """
    return MistakeReviewService(db)
