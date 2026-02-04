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


def get_learning_report_service(db: AsyncSession) -> LearningReportService:
    """获取学习报告服务实例"""
    return LearningReportService(db)
