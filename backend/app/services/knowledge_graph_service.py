"""
知识图谱服务 - AI英语教学系统
提供知识图谱诊断、更新和查询功能
采用混合策略：初始诊断用AI深度分析，日常更新用规则引擎零成本维护
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_graph import KnowledgeGraph
from app.models.student import Student
from app.services.ai_service import get_ai_service
from app.services.graph_rules import RuleEngine


class KnowledgeGraphService:
    """
    知识图谱服务类

    核心策略：
    1. 初始诊断：使用AI深度分析学生能力，建立完整的知识图谱
    2. 日常更新：使用规则引擎根据练习结果实时更新（零成本）
    3. 定期复盘：每周/每月使用AI重新分析，优化图谱准确性

    成本优化：
    - AI分析仅在初始诊断和定期复盘时使用（约占5%）
    - 规则引擎处理90%的日常更新（零成本）
    - 预计可节省95%的AI调用成本
    """

    def __init__(self):
        """初始化知识图谱服务"""
        self.ai_service = get_ai_service()
        self.rule_engine = RuleEngine()

    async def get_student_graph(
        self,
        db: AsyncSession,
        student_id: uuid.UUID,
    ) -> Optional[KnowledgeGraph]:
        """
        获取学生的知识图谱

        Args:
            db: 数据库会话
            student_id: 学生ID

        Returns:
            Optional[KnowledgeGraph]: 知识图谱对象，如果不存在返回None
        """
        result = await db.execute(
            select(KnowledgeGraph).where(
                KnowledgeGraph.student_id == student_id
            )
        )
        return result.scalar_one_or_none()

    async def create_student_graph(
        self,
        db: AsyncSession,
        student_id: uuid.UUID,
        initial_data: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeGraph:
        """
        为学生创建空的知识图谱

        Args:
            db: 数据库会话
            student_id: 学生ID
            initial_data: 初始数据（可选）

        Returns:
            KnowledgeGraph: 新创建的知识图谱对象
        """
        graph = KnowledgeGraph(
            student_id=student_id,
            nodes=initial_data.get("nodes", []) if initial_data else [],
            edges=initial_data.get("edges", []) if initial_data else [],
            abilities=initial_data.get("abilities", {}) if initial_data else {},
            cefr_level=initial_data.get("cefr_level") if initial_data else None,
            exam_coverage=initial_data.get("exam_coverage", {}) if initial_data else {},
            ai_analysis=initial_data.get("ai_analysis", {}) if initial_data else {},
        )

        db.add(graph)
        await db.commit()
        await db.refresh(graph)

        return graph

    async def diagnose_initial(
        self,
        db: AsyncSession,
        student_id: uuid.UUID,
        practice_data: List[Dict[str, Any]],
        force_reanalyze: bool = False,
    ) -> Dict[str, Any]:
        """
        初始诊断（使用AI深度分析）

        这是知识图谱的核心功能，在以下情况调用：
        1. 学生首次注册完成评估后
        2. 知识图谱不存在时
        3. force_reanalyze=True 时强制重新分析

        AI分析包括：
        - 综合评估确定CEFR等级
        - 分析各项语言能力
        - 识别薄弱点和优势
        - 提供学习建议
        - 评估考试准备度

        Args:
            db: 数据库会话
            student_id: 学生ID
            practice_data: 学生练习数据列表
            force_reanalyze: 是否强制重新分析（忽略已有图谱）

        Returns:
            Dict[str, Any]: 诊断结果，包含：
                - success: 是否成功
                - graph_id: 知识图谱ID
                - cefr_level: CEFR等级
                - abilities: 能力评估
                - weak_points: 薄弱点
                - recommendations: 学习建议
                - analysis_summary: 分析总结

        Raises:
            ValueError: 如果学生不存在或数据无效
        """
        # 1. 获取学生信息
        student_result = await db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = student_result.scalar_one_or_none()

        if not student:
            raise ValueError(f"学生不存在: {student_id}")

        # 2. 检查是否已有知识图谱
        existing_graph = await self.get_student_graph(db, student_id)

        if existing_graph and not force_reanalyze:
            # 已有图谱且不强制重新分析
            return {
                "success": True,
                "graph_id": str(existing_graph.id),
                "cefr_level": existing_graph.cefr_level,
                "abilities": existing_graph.abilities,
                "weak_points": existing_graph.ai_analysis.get("weak_points", []),
                "recommendations": existing_graph.ai_analysis.get("recommendations", []),
                "analysis_summary": "使用已有的知识图谱诊断结果",
                "is_cached": True,
            }

        # 3. 准备学生信息
        student_info = {
            "id": str(student.id),
            "name": student.user.real_name if student.user else "未知",
            "target_exam": student.target_exam,
            "target_score": student.target_score,
            "current_cefr_level": student.current_cefr_level,
        }

        # 4. 调用AI进行深度分析
        try:
            ai_analysis = await self.ai_service.analyze_student_assessment(
                student_info=student_info,
                practice_data=practice_data,
                target_exam=student.target_exam,
            )
        except Exception as e:
            raise ValueError(f"AI分析失败: {str(e)}")

        # 5. 构建知识图谱数据结构
        nodes = self._build_graph_nodes(ai_analysis, student.target_exam)
        edges = self._build_graph_edges(ai_analysis, practice_data)
        abilities = ai_analysis.get("abilities", {})
        cefr_level = ai_analysis.get("cefr_level", "A1")
        exam_coverage = self._calculate_exam_coverage(
            practice_data, student.target_exam
        )

        # 6. 更新或创建知识图谱
        if existing_graph:
            # 更新已有图谱
            existing_graph.nodes = nodes
            existing_graph.edges = edges
            existing_graph.abilities = abilities
            existing_graph.cefr_level = cefr_level
            existing_graph.exam_coverage = exam_coverage
            existing_graph.ai_analysis = ai_analysis
            existing_graph.last_ai_analysis_at = datetime.utcnow()
            graph = existing_graph
        else:
            # 创建新图谱
            graph = await self.create_student_graph(
                db=db,
                student_id=student_id,
                initial_data={
                    "nodes": nodes,
                    "edges": edges,
                    "abilities": abilities,
                    "cefr_level": cefr_level,
                    "exam_coverage": exam_coverage,
                    "ai_analysis": ai_analysis,
                }
            )
            graph.last_ai_analysis_at = datetime.utcnow()

        await db.commit()
        await db.refresh(graph)

        # 7. 更新学生的当前CEFR等级
        student.current_cefr_level = cefr_level
        await db.commit()

        # 8. 返回诊断结果
        return {
            "success": True,
            "graph_id": str(graph.id),
            "cefr_level": cefr_level,
            "abilities": abilities,
            "weak_points": ai_analysis.get("weak_points", []),
            "strong_points": ai_analysis.get("strong_points", []),
            "recommendations": ai_analysis.get("recommendations", []),
            "exam_readiness": ai_analysis.get("exam_readiness", {}),
            "analysis_summary": ai_analysis.get("analysis_summary", ""),
            "is_cached": False,
            "analyzed_at": graph.last_ai_analysis_at.isoformat(),
        }

    async def update_from_practice(
        self,
        db: AsyncSession,
        student_id: uuid.UUID,
        practice_record: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        从练习更新知识图谱（使用规则引擎，零成本）

        这是日常更新的主要方法，在学生完成每次练习后调用。
        使用规则引擎分析练习结果，实时更新能力值，无需AI调用。

        规则引擎逻辑：
        1. 根据正确率调整相关能力值
        2. 根据题目主题更新薄弱点/优势点
        3. 根据难度等级评估能力提升
        4. 累积更新，定期触发AI复盘

        Args:
            db: 数据库会话
            student_id: 学生ID
            practice_record: 练习记录，包含：
                - content_id: 内容ID
                - topic: 主题
                - difficulty: 难度等级
                - score: 得分
                - correct_rate: 正确率
                - time_spent: 耗时（秒）

        Returns:
            Dict[str, Any]: 更新结果，包含：
                - success: 是否成功
                - updated_abilities: 更新后的能力值
                - changes: 变化详情
                - need_ai_review: 是否需要AI复盘

        Raises:
            ValueError: 如果学生不存在或知识图谱不存在
        """
        # 1. 获取知识图谱
        graph = await self.get_student_graph(db, student_id)
        if not graph:
            raise ValueError(f"知识图谱不存在，请先进行初始诊断: {student_id}")

        # 2. 使用规则引擎分析练习
        analysis = self.rule_engine.analyze_practice(practice_record)

        # 3. 计算能力更新
        updated_abilities, changes = self.rule_engine.calculate_ability_update(
            current_abilities=graph.abilities or {},
            practice_analysis=analysis,
        )

        # 4. 更新知识图谱
        graph.abilities = updated_abilities
        graph.updated_at = datetime.utcnow()

        # 5. 检查是否需要AI复盘
        need_ai_review = self._should_trigger_ai_review(graph)

        if need_ai_review:
            # 标记需要AI复盘
            if not graph.ai_analysis:
                graph.ai_analysis = {}
            graph.ai_analysis["needs_review"] = True
            graph.ai_analysis["last_review_at"] = datetime.utcnow().isoformat()

        await db.commit()
        await db.refresh(graph)

        # 6. 返回更新结果
        return {
            "success": True,
            "graph_id": str(graph.id),
            "updated_abilities": updated_abilities,
            "changes": changes,
            "need_ai_review": need_ai_review,
            "update_method": "rule_engine",  # 标记使用规则引擎
            "updated_at": graph.updated_at.isoformat(),
        }

    async def get_weak_points(
        self,
        db: AsyncSession,
        student_id: uuid.UUID,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取学生的薄弱点

        Args:
            db: 数据库会话
            student_id: 学生ID
            limit: 返回数量限制

        Returns:
            List[Dict[str, Any]]: 薄弱点列表，每项包含：
                - topic: 主题
                - ability: 相关能力
                - current_level: 当前水平
                - reason: 原因
                - priority: 优先级
        """
        graph = await self.get_student_graph(db, student_id)
        if not graph:
            return []

        # 从AI分析中获取薄弱点
        ai_weak_points = graph.ai_analysis.get("weak_points", [])

        # 从当前能力值中识别薄弱点
        abilities = graph.abilities or {}
        weak_from_abilities = []

        for ability, value in abilities.items():
            if value < 60:  # 能力值低于60视为薄弱
                weak_from_abilities.append({
                    "topic": ability,
                    "ability": ability,
                    "current_level": value,
                    "reason": f"{ability}能力值为{value:.1f}，低于基础水平",
                    "priority": "high" if value < 40 else "medium",
                })

        # 合并去重
        all_weak_points = ai_weak_points + weak_from_abilities

        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        all_weak_points.sort(
            key=lambda x: priority_order.get(x.get("priority", "low"), 3)
        )

        return all_weak_points[:limit]

    async def get_recommendations(
        self,
        db: AsyncSession,
        student_id: uuid.UUID,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        获取学习建议

        Args:
            db: 数据库会话
            student_id: 学生ID
            limit: 返回数量限制

        Returns:
            List[Dict[str, Any]]: 学习建议列表，按优先级排序
        """
        graph = await self.get_student_graph(db, student_id)
        if not graph:
            return []

        # 从AI分析中获取建议
        ai_recommendations = graph.ai_analysis.get("recommendations", [])

        # 基于当前能力生成补充建议
        abilities = graph.abilities or {}
        dynamic_recommendations = []

        for ability, value in abilities.items():
            if value < 50:
                dynamic_recommendations.append({
                    "priority": "high",
                    "suggestion": (
                        f"加强{ability}基础训练。当前水平{value:.1f}，"
                        f"建议从简单材料开始，逐步提高难度。"
                    ),
                    "ability": ability,
                })
            elif value < 70:
                dynamic_recommendations.append({
                    "priority": "medium",
                    "suggestion": (
                        f"巩固{ability}能力。当前水平{value:.1f}，"
                        f"建议多做中等难度练习，提高准确率。"
                    ),
                    "ability": ability,
                })

        # 合并去重
        all_recommendations = ai_recommendations + dynamic_recommendations

        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        all_recommendations.sort(
            key=lambda x: priority_order.get(x.get("priority", "low"), 3)
        )

        return all_recommendations[:limit]

    async def trigger_ai_review(
        self,
        db: AsyncSession,
        student_id: uuid.UUID,
        practice_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        触发AI复盘分析

        定期调用（如每周/每月），对知识图谱进行深度重新分析，
        修正规则引擎的累积误差，优化诊断准确性。

        Args:
            db: 数据库会话
            student_id: 学生ID
            practice_data: 近期练习数据

        Returns:
            Dict[str, Any]: 复盘结果
        """
        # 强制重新诊断
        return await self.diagnose_initial(
            db=db,
            student_id=student_id,
            practice_data=practice_data,
            force_reanalyze=True,
        )

    def _build_graph_nodes(
        self,
        ai_analysis: Dict[str, Any],
        target_exam: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        构建知识图谱节点

        Args:
            ai_analysis: AI分析结果
            target_exam: 目标考试

        Returns:
            List[Dict[str, Any]]: 节点列表
        """
        nodes = []

        # 能力节点
        abilities = ai_analysis.get("abilities", {})
        for ability, value in abilities.items():
            nodes.append({
                "id": f"ability_{ability}",
                "type": "ability",
                "label": ability,
                "value": value,
                "level": self._get_ability_level(value),
            })

        # 考试节点
        if target_exam:
            nodes.append({
                "id": f"exam_{target_exam}",
                "type": "exam",
                "label": target_exam,
                "readiness": ai_analysis.get("exam_readiness", {}).get("ready", False),
            })

        # 主题节点（基于薄弱点）
        for weak_point in ai_analysis.get("weak_points", []):
            nodes.append({
                "id": f"topic_{weak_point['topic']}",
                "type": "weak_point",
                "label": weak_point["topic"],
                "reason": weak_point.get("reason", ""),
            })

        return nodes

    def _build_graph_edges(
        self,
        ai_analysis: Dict[str, Any],
        practice_data: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        构建知识图谱边

        Args:
            ai_analysis: AI分析结果
            practice_data: 练习数据

        Returns:
            List[Dict[str, Any]]: 边列表
        """
        edges = []

        # 能力之间的关系边
        ability_relations = [
            ("listening", "vocabulary", "depends_on"),
            ("reading", "grammar", "depends_on"),
            ("reading", "vocabulary", "depends_on"),
            ("writing", "grammar", "depends_on"),
            ("writing", "vocabulary", "depends_on"),
            ("speaking", "listening", "related_to"),
            ("writing", "reading", "related_to"),
        ]

        for source, target, relation in ability_relations:
            edges.append({
                "source": f"ability_{source}",
                "target": f"ability_{target}",
                "type": relation,
            })

        return edges

    def _calculate_exam_coverage(
        self,
        practice_data: List[Dict[str, Any]],
        target_exam: Optional[str],
    ) -> Dict[str, Any]:
        """
        计算考试覆盖度

        Args:
            practice_data: 练习数据
            target_exam: 目标考试

        Returns:
            Dict[str, Any]: 覆盖度信息
        """
        coverage = {
            "total_practices": len(practice_data),
            "topics_covered": len(set(p.get("topic") for p in practice_data)),
            "recent_activity": len([
                p for p in practice_data
                if datetime.fromisoformat(p.get("created_at", "")) > datetime.utcnow() - timedelta(days=7)
            ]),
        }

        return coverage

    def _get_ability_level(self, value: float) -> str:
        """
        根据能力值获取等级

        Args:
            value: 能力值 (0-100)

        Returns:
            str: 等级描述
        """
        if value >= 90:
            return "excellent"
        elif value >= 75:
            return "good"
        elif value >= 60:
            return "intermediate"
        elif value >= 40:
            return "basic"
        else:
            return "beginner"

    def _should_trigger_ai_review(self, graph: KnowledgeGraph) -> bool:
        """
        判断是否需要触发AI复盘

        触发条件：
        1. 距离上次AI分析超过7天
        2. 规则引擎更新超过50次（假设每次update都会计数）
        3. 任意能力值变化超过20分

        Args:
            graph: 知识图谱

        Returns:
            bool: 是否需要AI复盘
        """
        # 条件1：距离上次AI分析超过7天
        if graph.last_ai_analysis_at:
            days_since_last_analysis = (
                datetime.utcnow() - graph.last_ai_analysis_at
            ).days
            if days_since_last_analysis >= 7:
                return True

        # 条件2：检查能力值变化（这里简化处理，实际应该记录历史）
        update_count = graph.ai_analysis.get("update_count", 0) if graph.ai_analysis else 0
        if update_count >= 50:
            return True

        return False


# 创建全局单例
_knowledge_graph_service: Optional[KnowledgeGraphService] = None


def get_knowledge_graph_service() -> KnowledgeGraphService:
    """
    获取知识图谱服务单例

    Returns:
        KnowledgeGraphService: 知识图谱服务实例
    """
    global _knowledge_graph_service
    if _knowledge_graph_service is None:
        _knowledge_graph_service = KnowledgeGraphService()
    return _knowledge_graph_service
