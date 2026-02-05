"""
学习报告生成服务 - AI英语教学系统
负责聚合学习数据、分析能力进展、生成个性化建议
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Student, Practice, Mistake, MistakeStatus, MistakeType, LearningReport
from app.services.ai_service import AIService
from app.services.knowledge_graph_service import get_knowledge_graph_service


class LearningReportService:
    """学习报告生成服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.kg_service = get_knowledge_graph_service()

    async def generate_report(
        self,
        student_id: uuid.UUID,
        report_type: str = "custom",
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        生成完整的学习报告

        Args:
            student_id: 学生ID
            report_type: 报告类型 (weekly, monthly, custom)
            period_start: 统计开始时间
            period_end: 统计结束时间

        Returns:
            dict: 包含统计数据、能力分析、薄弱点、建议的完整报告
        """
        # 确定时间范围
        if not period_end:
            period_end = datetime.utcnow()
        if not period_start:
            # 默认30天
            period_start = period_end - timedelta(days=30)

        # 并行生成各部分数据
        statistics = await self.generate_statistics(student_id, period_start, period_end)
        ability_analysis = await self.analyze_ability_progress(student_id, period_start, period_end)
        weak_points = await self.analyze_weak_points(student_id, period_start, period_end)

        # 生成学习建议
        recommendations = await self.generate_recommendations(
            student_id, statistics, ability_analysis, weak_points
        )

        # 组合报告
        report = {
            "student_id": str(student_id),
            "report_type": report_type,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "statistics": statistics,
            "ability_analysis": ability_analysis,
            "weak_points": weak_points,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat(),
        }

        # 保存到数据库
        learning_report = LearningReport(
            student_id=student_id,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            status="completed",
            statistics=statistics,
            ability_analysis=ability_analysis,
            weak_points=weak_points,
            recommendations=recommendations,
            ai_insights=report.get("ai_insights"),
        )
        self.db.add(learning_report)
        await self.db.commit()
        await self.db.refresh(learning_report)

        # 添加数据库生成的字段到返回值
        report["id"] = str(learning_report.id)
        report["created_at"] = learning_report.created_at.isoformat()
        report["updated_at"] = learning_report.updated_at.isoformat()

        return report

    async def generate_statistics(
        self,
        student_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        """
        生成基础统计数据

        包括: 练习次数、正确率、学习时长、错题数量等
        """
        # 获取练习数据
        practice_result = await self.db.execute(
            select(Practice)
            .where(
                and_(
                    Practice.student_id == student_id,
                    Practice.created_at >= period_start,
                    Practice.created_at <= period_end,
                )
            )
        )
        practices = practice_result.scalars().all()

        # 统计练习数据
        total_practices = len(practices)
        completed_practices = sum(1 for p in practices if p.status == "completed")

        # 计算平均正确率
        correct_rates = [p.correct_rate for p in practices if p.correct_rate is not None]
        avg_correct_rate = sum(correct_rates) / len(correct_rates) if correct_rates else 0

        # 计算总学习时长（分钟）
        total_duration = sum(p.duration or 0 for p in practices)

        # 获取错题统计
        mistake_result = await self.db.execute(
            select(Mistake)
            .where(
                and_(
                    Mistake.student_id == student_id,
                    Mistake.first_mistaken_at >= period_start,
                    Mistake.first_mistaken_at <= period_end,
                )
            )
        )
        mistakes = mistake_result.scalars().all()

        # 按类型统计错题
        mistake_by_type = {}
        for m in mistakes:
            mtype = m.mistake_type
            mistake_by_type[mtype] = mistake_by_type.get(mtype, 0) + 1

        # 按状态统计错题
        mistake_by_status = {}
        for m in mistakes:
            status = m.status
            mistake_by_status[status] = mistake_by_status.get(status, 0) + 1

        return {
            "total_practices": total_practices,
            "completed_practices": completed_practices,
            "completion_rate": round(completed_practices / total_practices * 100, 2) if total_practices > 0 else 0,
            "avg_correct_rate": round(avg_correct_rate * 100, 2),
            "total_duration_minutes": total_duration,
            "total_duration_hours": round(total_duration / 60, 2),
            "total_mistakes": len(mistakes),
            "mistake_by_type": mistake_by_type,
            "mistake_by_status": mistake_by_status,
            "period_days": (period_end - period_start).days,
        }

    async def analyze_ability_progress(
        self,
        student_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        """
        分析能力进展

        从知识图谱获取历史能力值，计算趋势和增长
        """
        # 获取学生的知识图谱
        kg_result = await self.db.execute(
            select(Student)
            .options(selectinload(Student.knowledge_graph))
            .where(Student.id == student_id)
        )
        student = kg_result.scalar_one_or_none()

        if not student or not student.knowledge_graph:
            # 没有知识图谱，返回默认值
            return {
                "current_abilities": {},
                "ability_trend": [],
                "strongest_area": None,
                "weakest_area": None,
                "overall_progress": 0,
            }

        kg = student.knowledge_graph
        nodes = kg.nodes or {}

        # 获取当前能力值
        abilities = nodes.get("abilities", {})

        # 获取最后更新时间
        last_updated = kg.updated_at.isoformat() if kg.updated_at else None

        # 能力雷达图数据
        radar_data = []
        for ability_name, ability_info in abilities.items():
            radar_data.append({
                "name": self._translate_ability(ability_name),
                "value": ability_info.get("level", 0),
                "confidence": ability_info.get("confidence", 0),
            })

        # 排序找出最强和最弱项
        sorted_abilities = sorted(
            [(name, info.get("level", 0)) for name, info in abilities.items()],
            key=lambda x: x[1],
            reverse=True
        )

        strongest = sorted_abilities[0] if sorted_abilities else None
        weakest = sorted_abilities[-1] if sorted_abilities else None

        return {
            "current_abilities": abilities,
            "ability_radar": radar_data,
            "strongest_area": {
                "name": self._translate_ability(strongest[0]) if strongest else None,
                "level": strongest[1] if strongest else 0,
            } if strongest else None,
            "weakest_area": {
                "name": self._translate_ability(weakest[0]) if weakest else None,
                "level": weakest[1] if weakest else 0,
            } if weakest else None,
            "last_updated": last_updated,
        }

    async def analyze_weak_points(
        self,
        student_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        """
        分析薄弱知识点

        识别高频错误、未掌握的知识点
        """
        # 获取错题数据
        mistake_result = await self.db.execute(
            select(Mistake)
            .where(
                and_(
                    Mistake.student_id == student_id,
                    Mistake.first_mistaken_at >= period_start,
                    Mistake.first_mistaken_at <= period_end,
                    Mistake.status != MistakeStatus.MASTERED,  # 排除已掌握的
                )
            )
        )
        mistakes = mistake_result.scalars().all()

        # 统计知识点
        knowledge_point_counts = {}
        for m in mistakes:
            if m.knowledge_points:
                for kp in m.knowledge_points:
                    knowledge_point_counts[kp] = knowledge_point_counts.get(kp, 0) + 1

        # 排序找出高频薄弱点
        sorted_weak_points = sorted(
            knowledge_point_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 按主题统计
        topic_counts = {}
        for m in mistakes:
            topic = m.topic or "未分类"
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # 按难度统计
        difficulty_counts = {}
        for m in mistakes:
            diff = m.difficulty_level or "unknown"
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1

        return {
            "total_unmastered": len(mistakes),
            "knowledge_points": dict(sorted_weak_points[:10]),  # 只取前10个
            "knowledge_point_counts": dict(sorted_weak_points),
            "by_topic": topic_counts,
            "by_difficulty": difficulty_counts,
            "top_weak_points": [
                {"point": kp, "count": count}
                for kp, count in sorted_weak_points[:5]
            ],
        }

    async def generate_recommendations(
        self,
        student_id: uuid.UUID,
        statistics: Dict[str, Any],
        ability_analysis: Dict[str, Any],
        weak_points: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        生成个性化学习建议

        基于统计数据和能力分析生成学习建议
        """
        recommendations = []

        # 1. 基于练习完成度的建议
        completion_rate = statistics.get("completion_rate", 0)
        if completion_rate < 70:
            recommendations.append({
                "category": "学习习惯",
                "priority": "high",
                "title": "提高练习完成率",
                "description": f"当前练习完成率为 {completion_rate}%，建议每天坚持完成至少15分钟的练习。规律的学习比长时间突击更有效。"
            })
        elif completion_rate >= 90:
            recommendations.append({
                "category": "学习习惯",
                "priority": "low",
                "title": "保持良好习惯",
                "description": "你的练习完成率很高！继续保持这个良好的学习习惯。"
            })

        # 2. 基于正确率的建议
        avg_correct_rate = statistics.get("avg_correct_rate", 0)
        if avg_correct_rate < 60:
            recommendations.append({
                "category": "学习策略",
                "priority": "high",
                "title": "巩固基础知识",
                "description": f"当前平均正确率为 {avg_correct_rate}%，建议先复习基础知识点，不要急于做难度较高的题目。"
            })

        # 3. 基于薄弱点的建议
        if weak_points.get("top_weak_points"):
            top_weak = weak_points["top_weak_points"][0]
            recommendations.append({
                "category": "重点突破",
                "priority": "high",
                "title": f"重点关注：{top_weak['point']}",
                "description": f"这个知识点出现了 {top_weak['count']} 次错误，建议集中时间进行针对性练习。"
            })

        # 4. 基于能力分析的建议
        weakest = ability_analysis.get("weakest_area")
        if weakest and weakest.get("level", 0) < 60:
            recommendations.append({
                "category": "能力提升",
                "priority": "medium",
                "title": f"加强{weakest['name']}练习",
                "description": f"当前{weakest['name']}水平为 {weakest['level']}，建议多做相关练习来提升这项能力。"
            })

        # 5. 学习时长建议
        total_hours = statistics.get("total_duration_hours", 0)
        if total_hours < 5:
            recommendations.append({
                "category": "学习时长",
                "priority": "medium",
                "title": "增加学习时长",
                "description": f"本周期学习时长为 {total_hours:.1f} 小时，建议每周至少投入 3-5 小时进行英语学习。"
            })

        return {
            "recommendations": recommendations,
            "priority_count": {
                "high": sum(1 for r in recommendations if r.get("priority") == "high"),
                "medium": sum(1 for r in recommendations if r.get("priority") == "medium"),
                "low": sum(1 for r in recommendations if r.get("priority") == "low"),
            },
            "total_count": len(recommendations),
        }

    async def generate_ai_recommendations(
        self,
        student_id: uuid.UUID,
        statistics: Dict[str, Any],
    ) -> str:
        """
        使用AI生成个性化学习建议

        Args:
            student_id: 学生ID
            statistics: 统计数据

        Returns:
            str: AI生成的建议文本
        """
        # 获取学生信息
        student_result = await self.db.execute(
            select(Student)
            .options(selectinload(Student.user))
            .where(Student.id == student_id)
        )
        student = student_result.scalar_one_or_none()

        if not student:
            return "无法获取学生信息"

        user = student.user if student else None
        if not user:
            return "无法获取用户信息"

        # 构建提示词
        prompt = f"""你是专业的英语学习顾问。请根据以下学生学习数据，生成个性化的学习建议。

学生信息：
- 姓名：{user.full_name or '同学'}
- 当前水平：{student.current_cefr_level or '未知'}
- 目标考试：{student.target_exam or '未设置'}

学习统计数据：
- 练习次数：{statistics.get('total_practices', 0)} 次
- 完成率：{statistics.get('completion_rate', 0)}%
- 平均正确率：{statistics.get('avg_correct_rate', 0)}%
- 学习时长：{statistics.get('total_duration_hours', 0):.1f} 小时
- 错题数量：{statistics.get('total_mistakes', 0)} 道

错题类型分布：
{self._format_dict(statistics.get('mistake_by_type', {}))}

请生成：
1. 学习亮点总结（2-3条）
2. 需要改进的方面（2-3条）
3. 具体可行的学习建议（3-5条）

要求：
- 语气鼓励且专业
- 建议具体可行
- 结合学生的实际水平
"""

        try:
            # 调用AI服务
            ai_service = AIService()
            response = await ai_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是专业的英语学习顾问，擅长分析学习数据并提供个性化建议。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7,
            )

            return response.strip()

        except Exception as e:
            # AI调用失败，返回通用建议
            return self._get_default_recommendations(statistics)

    def _translate_ability(self, ability_name: str) -> str:
        """翻译能力名称"""
        translations = {
            "listening": "听力",
            "reading": "阅读",
            "speaking": "口语",
            "writing": "写作",
            "grammar": "语法",
            "vocabulary": "词汇",
        }
        return translations.get(ability_name, ability_name)

    def _format_dict(self, d: Dict[str, int]) -> str:
        """格式化字典为字符串"""
        return "\n".join([f"- {k}: {v}" for k, v in d.items()])

    def _get_default_recommendations(self, statistics: Dict[str, Any]) -> str:
        """获取默认建议（AI调用失败时使用）"""
        return f"""基于你的学习数据，以下是一些建议：

**学习亮点**：
- 你已经完成了 {statistics.get('total_practices', 0)} 次练习，这是很好的开始！
- 继续保持学习的规律性，你会看到进步的。

**改进建议**：
- 当前平均正确率为 {statistics.get('avg_correct_rate', 0)}%，建议在做题后认真查看解析，理解错误原因
- 建议每天坚持至少15分钟的英语学习时间
- 对于错题要及时复习，避免重复犯错

**学习方向**：
- 重点关注自己的薄弱知识点，进行针对性练习
- 建议多听多说，提升英语实际应用能力
"""

    async def get_student_reports(
        self,
        student_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List["LearningReport"], int]:
        """
        获取学生的学习报告列表

        Args:
            student_id: 学生ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            (报告列表, 总数)
        """
        # 导入模型避免循环导入
        from app.models.learning_report import LearningReport

        # 查询总数
        count_result = await self.db.execute(
            select(func.count(LearningReport.id))
            .where(LearningReport.student_id == student_id)
        )
        total = count_result.scalar()

        # 查询报告列表
        result = await self.db.execute(
            select(LearningReport)
            .where(LearningReport.student_id == student_id)
            .order_by(LearningReport.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        reports = result.scalars().all()

        return list(reports), total

    async def get_teacher_student_reports(
        self,
        teacher_id: uuid.UUID,
        class_id: Optional[uuid.UUID] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        获取教师班级学生列表及报告概览

        Args:
            teacher_id: 教师ID
            class_id: 班级ID（可选）
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            (学生列表, 总数)
        """
        # 导入模型避免循环导入
        from app.models.class_model import ClassInfo, ClassStudent
        from app.models.student import Student
        from app.models.user import User

        # 构建查询：获取教师负责的班级下的学生
        query = (
            select(
                Student.id,
                Student.student_number,
                User.username,
                User.email,
                ClassInfo.id.label("class_id"),
                ClassInfo.name.label("class_name"),
                ClassInfo.grade,
                LearningReport.id.label("latest_report_id"),
                LearningReport.created_at.label("latest_report_created_at"),
                LearningReport.report_type.label("latest_report_type"),
            )
            .select_from(Student)
            .join(User, Student.user_id == User.id)
            .join(ClassStudent, Student.id == ClassStudent.student_id)
            .join(ClassInfo, ClassStudent.class_id == ClassInfo.id)
            .join(
                # 获取最新的学习报告（LEFT JOIN）
                LearningReport,
                and_(
                    LearningReport.student_id == Student.id,
                    LearningReport.created_at == (
                        select(func.max(LearningReport.created_at))
                        .where(LearningReport.student_id == Student.id)
                        .correlate(Student)
                    ),
                ),
                isouter=True,
            )
            .where(
                and_(
                    ClassInfo.head_teacher_id == teacher_id,
                    ClassStudent.enrollment_status == "active",
                    ClassInfo.status == "active",
                )
            )
        )

        # 如果指定了班级ID，添加筛选
        if class_id:
            query = query.where(ClassInfo.id == class_id)

        # 查询总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 查询学生列表
        query = query.order_by(User.username.asc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        rows = result.all()

        # 转换为字典格式
        students = []
        for row in rows:
            students.append({
                "student_id": str(row.id),
                "student_number": row.student_number,
                "student_name": row.username,
                "email": row.email,
                "class_id": str(row.class_id),
                "class_name": row.class_name,
                "grade": row.grade,
                "latest_report": {
                    "report_id": str(row.latest_report_id) if row.latest_report_id else None,
                    "created_at": row.latest_report_created_at.isoformat() if row.latest_report_created_at else None,
                    "report_type": row.latest_report_type if row.latest_report_type else None,
                } if row.latest_report_id else None,
                "has_reports": bool(row.latest_report_id),
            })

        return students, total

    async def get_student_reports_for_teacher(
        self,
        teacher_id: uuid.UUID,
        student_id: uuid.UUID,
        report_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List["LearningReport"], int]:
        """
        获取指定学生的报告列表（教师视角）

        Args:
            teacher_id: 教师ID
            student_id: 学生ID
            report_type: 报告类型筛选
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            (报告列表, 总数)

        Raises:
            HTTPException: 如果学生不属于该教师
        """
        # 验证学生是否属于该教师
        await self.verify_student_belongs_to_teacher(teacher_id, student_id)

        # 导入模型避免循环导入
        from app.models.learning_report import LearningReport

        # 构建查询
        query = select(LearningReport).where(LearningReport.student_id == student_id)

        # 添加报告类型筛选
        if report_type:
            query = query.where(LearningReport.report_type == report_type)

        # 查询总数
        count_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar()

        # 查询报告列表
        query = query.order_by(LearningReport.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        reports = result.scalars().all()

        return list(reports), total

    async def verify_student_belongs_to_teacher(
        self,
        teacher_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> None:
        """
        验证学生是否属于该教师

        Args:
            teacher_id: 教师ID
            student_id: 学生ID

        Raises:
            HTTPException 404: 如果学生不属于该教师
        """
        from app.models.class_model import ClassInfo, ClassStudent
        from fastapi import HTTPException, status

        # 查询学生是否在教师负责的班级中
        result = await self.db.execute(
            select(func.count(ClassStudent.id))
            .select_from(ClassStudent)
            .join(ClassInfo, ClassStudent.class_id == ClassInfo.id)
            .where(
                and_(
                    ClassStudent.student_id == student_id,
                    ClassInfo.head_teacher_id == teacher_id,
                    ClassStudent.enrollment_status == "active",
                    ClassInfo.status == "active",
                )
            )
        )
        count = result.scalar()

        if count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="学生不存在或不属于该教师"
            )

    async def generate_class_summary(
        self,
        teacher_id: uuid.UUID,
        class_id: uuid.UUID,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        生成班级学习状况汇总

        Args:
            teacher_id: 教师ID
            class_id: 班级ID
            period_start: 统计开始时间
            period_end: 统计结束时间

        Returns:
            dict: 班级学习状况汇总

        Raises:
            HTTPException: 如果班级不属于该教师
        """
        from app.models.class_model import ClassInfo, ClassStudent
        from app.models.student import Student
        from app.models.user import User
        from fastapi import HTTPException, status

        # 确定时间范围
        if not period_end:
            period_end = datetime.utcnow()
        if not period_start:
            period_start = period_end - timedelta(days=30)

        # 验证班级是否属于该教师
        result = await self.db.execute(
            select(ClassInfo)
            .where(
                and_(
                    ClassInfo.id == class_id,
                    ClassInfo.head_teacher_id == teacher_id,
                    ClassInfo.status == "active",
                )
            )
        )
        class_info = result.scalar_one_or_none()

        if not class_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="班级不存在或不属于该教师"
            )

        # 获取班级学生总数
        total_students_result = await self.db.execute(
            select(func.count(ClassStudent.id))
            .select_from(ClassStudent)
            .where(
                and_(
                    ClassStudent.class_id == class_id,
                    ClassStudent.enrollment_status == "active",
                )
            )
        )
        total_students = total_students_result.scalar()

        # 获取有报告的学生数（活跃学生）
        active_students_result = await self.db.execute(
            select(func.count(func.distinct(LearningReport.student_id)))
            .select_from(LearningReport)
            .join(ClassStudent, LearningReport.student_id == ClassStudent.student_id)
            .where(
                and_(
                    ClassStudent.class_id == class_id,
                    ClassStudent.enrollment_status == "active",
                    LearningReport.created_at >= period_start,
                    LearningReport.created_at <= period_end,
                )
            )
        )
        active_students = active_students_result.scalar() or 0

        # 获取班级整体统计数据
        stats_result = await self.db.execute(
            select(
                func.avg(LearningReport.statistics["completion_rate"].asfloat()),
                func.avg(LearningReport.statistics["avg_correct_rate"].asfloat()),
                func.sum(LearningReport.statistics["total_duration_minutes"].asfloat()),
            )
            .select_from(LearningReport)
            .join(ClassStudent, LearningReport.student_id == ClassStudent.student_id)
            .where(
                and_(
                    ClassStudent.class_id == class_id,
                    ClassStudent.enrollment_status == "active",
                    LearningReport.created_at >= period_start,
                    LearningReport.created_at <= period_end,
                )
            )
        )
        stats = stats_result.one()
        avg_completion_rate = float(stats[0]) if stats[0] else 0.0
        avg_correct_rate = float(stats[1]) if stats[1] else 0.0
        total_study_hours = float(stats[2]) / 60.0 if stats[2] else 0.0

        # 获取能力分布统计
        ability_result = await self.db.execute(
            select(LearningReport.ability_analysis)
            .select_from(LearningReport)
            .join(ClassStudent, LearningReport.student_id == ClassStudent.student_id)
            .where(
                and_(
                    ClassStudent.class_id == class_id,
                    ClassStudent.enrollment_status == "active",
                    LearningReport.created_at >= period_start,
                    LearningReport.created_at <= period_end,
                )
            )
            .order_by(LearningReport.created_at.desc())
            .limit(50)  # 取最近的报告
        )
        ability_data = ability_result.scalars().all()

        # 计算班级整体能力分布
        ability_distribution = {
            "listening": 0.0,
            "reading": 0.0,
            "speaking": 0.0,
            "writing": 0.0,
            "grammar": 0.0,
            "vocabulary": 0.0,
        }

        if ability_data:
            for ability in ability_data:
                if ability and "ability_radar" in ability:
                    for item in ability["ability_radar"]:
                        name = item.get("name", "").lower()
                        value = item.get("value", 0)
                        if "听力" in name or "listening" in name:
                            ability_distribution["listening"] += value
                        elif "阅读" in name or "reading" in name:
                            ability_distribution["reading"] += value
                        elif "口语" in name or "speaking" in name:
                            ability_distribution["speaking"] += value
                        elif "写作" in name or "writing" in name:
                            ability_distribution["writing"] += value
                        elif "语法" in name or "grammar" in name:
                            ability_distribution["grammar"] += value
                        elif "词汇" in name or "vocabulary" in name:
                            ability_distribution["vocabulary"] += value

            # 计算平均值
            count = len([d for d in ability_data if d])
            if count > 0:
                for key in ability_distribution:
                    ability_distribution[key] = round(ability_distribution[key] / count, 2)

        # 获取薄弱知识点汇总
        weak_points_result = await self.db.execute(
            select(LearningReport.weak_points)
            .select_from(LearningReport)
            .join(ClassStudent, LearningReport.student_id == ClassStudent.student_id)
            .where(
                and_(
                    ClassStudent.class_id == class_id,
                    ClassStudent.enrollment_status == "active",
                    LearningReport.created_at >= period_start,
                    LearningReport.created_at <= period_end,
                )
            )
        )
        weak_points_data = weak_points_result.scalars().all()

        # 汇总薄弱知识点
        weak_points_summary = {}
        if weak_points_data:
            for wp in weak_points_data:
                if wp and "knowledge_points" in wp:
                    for kp, count in wp["knowledge_points"].items():
                        weak_points_summary[kp] = weak_points_summary.get(kp, 0) + count

            # 排序并取前10个
            sorted_weak_points = sorted(
                weak_points_summary.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

            weak_points_summary = [{"knowledge_point": kp, "affected_students": count}
                                 for kp, count in sorted_weak_points]
        else:
            weak_points_summary = []

        return {
            "class_id": str(class_id),
            "class_name": class_info.name,
            "total_students": total_students,
            "active_students": active_students,
            "overall_stats": {
                "avg_completion_rate": round(avg_completion_rate, 2),
                "avg_correct_rate": round(avg_correct_rate, 2),
                "total_study_hours": round(total_study_hours, 2),
            },
            "ability_distribution": ability_distribution,
            "top_weak_points": weak_points_summary,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
        }


def get_learning_report_service(db: AsyncSession) -> LearningReportService:
    """获取学习报告服务实例"""
    return LearningReportService(db)
