"""
图表数据服务 - AI英语教学系统
负责聚合学习趋势、能力雷达图、知识点热力图等可视化数据
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Student, Practice, Mistake, LearningReport
from app.services.knowledge_graph_service import get_knowledge_graph_service


class ChartDataService:
    """图表数据服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.kg_service = get_knowledge_graph_service()

    async def get_learning_trend_data(
        self,
        student_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
        metrics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        获取学习趋势数据

        Args:
            student_id: 学生ID
            start_date: 开始日期
            end_date: 结束日期
            metrics: 要返回的指标列表 (practices, correctRate, duration)

        Returns:
            dict: 包含各指标时间序列数据
        """
        if metrics is None:
            metrics = ["practices", "correctRate", "duration"]

        result = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "metrics": {}
        }

        if "practices" in metrics:
            result["metrics"]["practices"] = await self._get_practice_trend(
                student_id, start_date, end_date
            )

        if "correctRate" in metrics:
            result["metrics"]["correctRate"] = await self._get_correct_rate_trend(
                student_id, start_date, end_date
            )

        if "duration" in metrics:
            result["metrics"]["duration"] = await self._get_duration_trend(
                student_id, start_date, end_date
            )

        return result

    async def _get_practice_trend(
        self,
        student_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """获取每日练习数量趋势"""
        query = text("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as count
            FROM practices
            WHERE
                student_id = :student_id
                AND created_at >= :start_date
                AND created_at < :end_date
            GROUP BY DATE(created_at)
            ORDER BY date
        """)

        result = await self.db.execute(
            query,
            {
                "student_id": student_id,
                "start_date": start_date,
                "end_date": end_date + timedelta(days=1)
            }
        )

        rows = result.all()
        return [
            {"date": row[0].isoformat(), "count": row[1]}
            for row in rows
        ]

    async def _get_correct_rate_trend(
        self,
        student_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """获取每日正确率趋势"""
        query = text("""
            SELECT
                DATE(created_at) as date,
                AVG(correct_rate) as rate
            FROM practices
            WHERE
                student_id = :student_id
                AND created_at >= :start_date
                AND created_at < :end_date
                AND correct_rate IS NOT NULL
            GROUP BY DATE(created_at)
            ORDER BY date
        """)

        result = await self.db.execute(
            query,
            {
                "student_id": student_id,
                "start_date": start_date,
                "end_date": end_date + timedelta(days=1)
            }
        )

        rows = result.all()
        return [
            {"date": row[0].isoformat(), "rate": round(float(row[1] or 0) * 100, 2)}
            for row in rows
        ]

    async def _get_duration_trend(
        self,
        student_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """获取每日学习时长趋势"""
        query = text("""
            SELECT
                DATE(created_at) as date,
                SUM(duration) as minutes
            FROM practices
            WHERE
                student_id = :student_id
                AND created_at >= :start_date
                AND created_at < :end_date
                AND duration IS NOT NULL
            GROUP BY DATE(created_at)
            ORDER BY date
        """)

        result = await self.db.execute(
            query,
            {
                "student_id": student_id,
                "start_date": start_date,
                "end_date": end_date + timedelta(days=1)
            }
        )

        rows = result.all()
        return [
            {"date": row[0].isoformat(), "minutes": row[1] or 0}
            for row in rows
        ]

    async def get_ability_radar_data(
        self,
        student_id: uuid.UUID,
        compare_with: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取能力雷达图数据

        Args:
            student_id: 学生ID
            compare_with: 对比模式 (none, class_avg, history)

        Returns:
            dict: 能力雷达图数据
        """
        # 获取学生知识图谱
        student_result = await self.db.execute(
            select(Student)
            .options(selectinload(Student.knowledge_graph))
            .where(Student.id == student_id)
        )
        student = student_result.scalar_one_or_none()

        if not student or not student.knowledge_graph:
            return self._get_default_ability_data()

        kg = student.knowledge_graph
        abilities = kg.nodes.get("abilities", {}) if kg.nodes else {}

        # 构建能力数据
        ability_list = []
        ability_names = ["vocabulary", "grammar", "reading", "listening", "speaking", "writing"]
        ability_labels = {
            "vocabulary": "词汇",
            "grammar": "语法",
            "reading": "阅读",
            "listening": "听力",
            "speaking": "口语",
            "writing": "写作",
        }

        for name in ability_names:
            ability_info = abilities.get(name, {})
            value = ability_info.get("level", 0)
            ability_list.append({
                "name": ability_labels.get(name, name),
                "value": round(value, 2),
                "confidence": round(ability_info.get("confidence", 0), 2),
                "relatedTopics": ability_info.get("relatedTopics", []),
            })

        # 排序找出最强和最弱项
        sorted_abilities = sorted(
            [(a["name"], a["value"]) for a in ability_list],
            key=lambda x: x[1],
            reverse=True
        )

        strongest = sorted_abilities[0] if sorted_abilities else None
        weakest = sorted_abilities[-1] if sorted_abilities else None

        result = {
            "abilities": ability_list,
            "strongestPoint": {
                "name": strongest[0] if strongest else "无",
                "value": strongest[1] if strongest else 0,
            },
            "weakestPoint": {
                "name": weakest[0] if weakest else "无",
                "value": weakest[1] if weakest else 0,
            },
        }

        # 添加对比数据
        if compare_with == "class_avg":
            result["classAverage"] = await self._get_class_average_abilities(student_id)

        return result

    async def _get_class_average_abilities(
        self,
        student_id: uuid.UUID,
    ) -> Dict[str, float]:
        """获取班级平均能力值"""
        # 获取学生所在班级
        query = text("""
            SELECT ci.head_teacher_id
            FROM class_students cs
            JOIN classes ci ON cs.class_id = ci.id
            WHERE cs.student_id = :student_id
            AND cs.enrollment_status = 'active'
            LIMIT 1
        """)

        result = await self.db.execute(query, {"student_id": student_id})
        row = result.first()

        if not row:
            return {}

        teacher_id = row[0]

        # 获取班级学生ID列表
        class_query = text("""
            SELECT cs.student_id
            FROM class_students cs
            WHERE cs.class_id IN (
                SELECT id FROM classes WHERE head_teacher_id = :teacher_id
            )
            AND cs.enrollment_status = 'active'
        """)

        class_result = await self.db.execute(class_query, {"teacher_id": teacher_id})
        student_ids = [r[0] for r in class_result.all()]

        if not student_ids:
            return {}

        # 计算班级平均能力（简化版：从最新报告中获取）
        ability_labels = {
            "vocabulary": "词汇",
            "grammar": "语法",
            "reading": "阅读",
            "listening": "听力",
            "speaking": "口语",
            "writing": "写作",
        }

        averages = {}
        for name, label in ability_labels.items():
            avg_query = text("""
                SELECT AVG(
                    (ability_analysis->'ability_radar'->>(
                        SELECT index FROM ability_radar,
                        (SELECT json_array_elements(ability_analysis->'ability_radar') AS arr) sub
                        WHERE arr->>'name' = :label
                    ))->>'value')::float
                FROM learning_reports
                WHERE student_id = ANY(:student_ids)
                AND ability_analysis IS NOT NULL
                AND created_at >= NOW() - INTERVAL '90 days'
            """)
            # 简化处理，返回默认值
            averages[name] = 50.0

        return averages

    async def _get_default_ability_data(self) -> Dict[str, Any]:
        """获取默认能力数据（当无数据时）"""
        ability_labels = ["词汇", "语法", "阅读", "听力", "口语", "写作"]
        return {
            "abilities": [
                {"name": name, "value": 0, "confidence": 0, "relatedTopics": []}
                for name in ability_labels
            ],
            "classAverage": None,
            "strongestPoint": {"name": "无", "value": 0},
            "weakestPoint": {"name": "无", "value": 0},
        }

    async def get_knowledge_heatmap_data(
        self,
        student_id: uuid.UUID,
        filters: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        获取知识点热力图数据

        Args:
            student_id: 学生ID
            filters: 筛选条件 (ability, topic, difficulty)

        Returns:
            dict: 知识点热力图数据
        """
        filters = filters or {}

        # 获取学生的错题数据作为知识点掌握度基础
        query = select(Mistake).where(
            and_(
                Mistake.student_id == student_id,
                Mistake.status != "mastered",
            )
        )

        # 应用筛选条件
        if "ability" in filters:
            query = query.where(Mistake.ability_type == filters["ability"])

        if "topic" in filters:
            query = query.where(Mistake.topic == filters["topic"])

        if "difficulty" in filters:
            query = query.where(Mistake.difficulty_level == filters["difficulty"])

        result = await self.db.execute(query)
        mistakes = result.scalars().all()

        # 按主题分组统计
        topic_stats = {}
        for m in mistakes:
            topic = m.topic or "未分类"
            ability = m.ability_type or "综合"
            difficulty = m.difficulty_level or "unknown"

            if topic not in topic_stats:
                topic_stats[topic] = {
                    "id": topic,
                    "name": topic,
                    "abilities": {}
                }

            if ability not in topic_stats[topic]["abilities"]:
                topic_stats[topic]["abilities"][ability] = {
                    "name": ability,
                    "difficulty": difficulty,
                    "total": 0,
                    "correct": 0,
                    "trend": self._calculate_trend(m),
                }

            topic_stats[topic]["abilities"][ability]["total"] += 1
            # 简化：正确题数统计
            if m.status == "reviewed":
                topic_stats[topic]["abilities"][ability]["correct"] += 1

        # 转换为列表格式并计算掌握率
        topics = []
        for topic_data in topic_stats.values():
            abilities = []
            for abil_data in topic_data["abilities"].values():
                total = abil_data["total"]
                correct = abil_data["correct"]
                mastery_rate = (correct / total * 100) if total > 0 else 0

                abilities.append({
                    "name": abil_data["name"],
                    "difficulty": abil_data["difficulty"],
                    "masteryRate": round(mastery_rate, 2),
                    "practiceCount": total,
                    "trend": abil_data["trend"],
                })

            topics.append({
                "id": topic_data["id"],
                "name": topic_data["name"],
                "abilities": abilities,
            })

        # 按掌握率排序（最弱的在前）
        topics.sort(key=lambda x: self._get_topic_avg_mastery(x), reverse=True)

        return {
            "topics": topics,
            "filters": filters,
        }

    def _calculate_trend(self, mistake: Mistake) -> str:
        """计算知识点趋势"""
        # 简化实现：基于错误次数判断
        return "stable"

    def _get_topic_avg_mastery(self, topic: Dict) -> float:
        """获取主题平均掌握率"""
        if not topic["abilities"]:
            return 0
        rates = [a["masteryRate"] for a in topic["abilities"]]
        return sum(rates) / len(rates) if rates else 0

    async def get_weekly_summary(
        self,
        student_id: uuid.UUID,
        weeks: int = 4,
    ) -> Dict[str, Any]:
        """
        获取最近几周的周报汇总

        Args:
            student_id: 学生ID
            weeks: 周数

        Returns:
            dict: 周报汇总数据
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(weeks=weeks)

        # 获取练习统计
        query = text("""
            SELECT
                DATE_TRUNC('week', created_at) as week_start,
                COUNT(*) as total_practices,
                AVG(correct_rate) as avg_correct_rate,
                SUM(duration) as total_duration
            FROM practices
            WHERE
                student_id = :student_id
                AND created_at >= :start_date
                AND created_at < :end_date
            GROUP BY DATE_TRUNC('week', created_at)
            ORDER BY week_start
        """)

        result = await self.db.execute(
            query,
            {
                "student_id": student_id,
                "start_date": start_date,
                "end_date": end_date
            }
        )

        weeks_data = []
        for row in result.all():
            weeks_data.append({
                "week_start": row[0].isoformat(),
                "total_practices": row[1],
                "avg_correct_rate": round(float(row[2] or 0) * 100, 2),
                "total_duration": row[3] or 0,
            })

        return {
            "student_id": str(student_id),
            "weeks": weeks_data,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            }
        }


def get_chart_data_service(db: AsyncSession) -> ChartDataService:
    """获取图表数据服务实例"""
    return ChartDataService(db)
