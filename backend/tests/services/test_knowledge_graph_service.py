"""
知识图谱服务测试 - AI英语教学系统
测试 KnowledgeGraphService 类的各项功能
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.knowledge_graph_service import (
    KnowledgeGraphService,
    get_knowledge_graph_service,
)
from app.models.knowledge_graph import KnowledgeGraph
from app.models.student import Student


class TestKnowledgeGraphService:
    """知识图谱服务测试类"""

    @pytest.fixture
    def kg_service(self):
        """创建知识图谱服务实例"""
        return KnowledgeGraphService()

    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.scalar_one_or_none = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def mock_student(self):
        """模拟学生对象"""
        student = MagicMock(spec=Student)
        student.id = "student-123"
        student.user.real_name = "张三"
        student.target_exam = "CET4"
        student.target_score = 500
        student.current_cefr_level = None
        return student

    @pytest.fixture
    def mock_knowledge_graph(self):
        """模拟知识图谱对象"""
        graph = MagicMock(spec=KnowledgeGraph)
        graph.id = "graph-123"
        graph.student_id = "student-123"
        graph.nodes = []
        graph.edges = []
        graph.abilities = {}
        graph.cefr_level = None
        graph.exam_coverage = {}
        graph.ai_analysis = {}
        graph.last_ai_analysis_at = None
        return graph

    @pytest.mark.asyncio
    async def test_get_student_graph_exists(self, kg_service, mock_db_session, mock_knowledge_graph):
        """测试获取存在的知识图谱"""
        mock_db_session.scalar_one_or_none.return_value = mock_knowledge_graph

        result = await kg_service.get_student_graph(
            db=mock_db_session,
            student_id="student-123",
        )

        assert result is not None
        assert result.id == "graph-123"

    @pytest.mark.asyncio
    async def test_get_student_graph_not_exists(self, kg_service, mock_db_session):
        """测试获取不存在的知识图谱"""
        mock_db_session.scalar_one_or_none.return_value = None

        result = await kg_service.get_student_graph(
            db=mock_db_session,
            student_id="student-123",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_create_student_graph(self, kg_service, mock_db_session):
        """测试创建知识图谱"""
        initial_data = {
            "nodes": [{"id": "1", "type": "ability"}],
            "edges": [],
            "abilities": {"reading": 70},
            "cefr_level": "B1",
        }

        with patch.object(kg_service, "create_student_graph", return_value=MagicMock()) as mock_create:
            await kg_service.create_student_graph(
                db=mock_db_session,
                student_id="student-123",
                initial_data=initial_data,
            )

            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_diagnose_initial_success(
        self,
        kg_service,
        mock_db_session,
        mock_student,
        mock_knowledge_graph,
    ):
        """测试初始诊断成功"""
        # 模拟不存在知识图谱
        mock_db_session.scalar_one_ornone.return_value = None

        # 模拟AI分析结果
        ai_analysis = {
            "cefr_level": "B1",
            "abilities": {
                "listening": 75,
                "reading": 80,
                "speaking": 65,
                "writing": 70,
                "grammar": 72,
                "vocabulary": 68,
            },
            "weak_points": [
                {"topic": "语法", "reason": "复杂句型掌握不足"}
            ],
            "strong_points": ["阅读理解"],
            "recommendations": [
                {"priority": "high", "suggestion": "加强语法练习"}
            ],
            "exam_readiness": {
                "ready": False,
                "gap": "需要提升综合能力"
            },
            "analysis_summary": "整体水平良好",
        }

        practice_data = [
            {
                "content_id": "1",
                "topic": "阅读",
                "difficulty": "intermediate",
                "score": 80,
                "correct_rate": 0.85,
                "time_spent": 300,
                "created_at": "2024-01-01T00:00:00",
            }
        ]

        # 模拟服务方法
        with patch.object(
            kg_service.ai_service,
            "analyze_student_assessment",
            return_value=ai_analysis,
        ):
            with patch.object(
                kg_service,
                "get_student_graph",
                return_value=None,
            ):
                with patch.object(
                    kg_service,
                    "create_student_graph",
                    return_value=mock_knowledge_graph,
                ):
                    result = await kg_service.diagnose_initial(
                        db=mock_db_session,
                        student_id="student-123",
                        practice_data=practice_data,
                    )

        # 验证结果
        assert result["success"] is True
        assert result["cefr_level"] == "B1"
        assert result["abilities"]["reading"] == 80
        assert len(result["weak_points"]) == 1
        assert result["is_cached"] is False

    @pytest.mark.asyncio
    async def test_diagnose_initial_cached(
        self,
        kg_service,
        mock_db_session,
        mock_knowledge_graph,
    ):
        """测试使用缓存的诊断结果"""
        mock_knowledge_graph.cefr_level = "B1"
        mock_knowledge_graph.abilities = {"reading": 80}
        mock_knowledge_graph.ai_analysis = {
            "weak_points": [{"topic": "语法", "reason": "掌握不足"}],
            "recommendations": [{"priority": "high", "suggestion": "加强练习"}],
        }

        with patch.object(
            kg_service,
            "get_student_graph",
            return_value=mock_knowledge_graph,
        ):
            result = await kg_service.diagnose_initial(
                db=mock_db_session,
                student_id="student-123",
                practice_data=[],
                force_reanalyze=False,
            )

        # 验证返回缓存结果
        assert result["success"] is True
        assert result["cefr_level"] == "B1"
        assert result["is_cached"] is True
        assert result["analysis_summary"] == "使用已有的知识图谱诊断结果"

    @pytest.mark.asyncio
    async def test_diagnose_initial_student_not_found(self, kg_service, mock_db_session):
        """测试学生不存在"""
        mock_db_session.scalar_one_or_none.return_value = None

        with patch.object(
            kg_service,
            "get_student_graph",
            return_value=None,
        ):
            with patch("app.services.knowledge_graph_service.select", return_value=MagicMock()):
                with pytest.raises(ValueError, match="学生不存在"):
                    await kg_service.diagnose_initial(
                        db=mock_db_session,
                        student_id="nonexistent",
                        practice_data=[],
                    )

    @pytest.mark.asyncio
    async def test_update_from_practice_success(
        self,
        kg_service,
        mock_db_session,
        mock_knowledge_graph,
    ):
        """测试从练习更新成功"""
        mock_knowledge_graph.abilities = {"reading": 70.0}

        with patch.object(
            kg_service,
            "get_student_graph",
            return_value=mock_knowledge_graph,
        ):
            practice_record = {
                "content_id": "123",
                "topic": "阅读",
                "difficulty": "intermediate",
                "score": 85,
                "correct_rate": 0.9,
                "time_spent": 200,
            }

            result = await kg_service.update_from_practice(
                db=mock_db_session,
                student_id="student-123",
                practice_record=practice_record,
            )

        # 验证结果
        assert result["success"] is True
        assert "updated_abilities" in result
        assert "changes" in result
        assert result["update_method"] == "rule_engine"
        assert "updated_at" in result

    @pytest.mark.asyncio
    async def test_update_from_practice_no_graph(self, kg_service, mock_db_session):
        """测试知识图谱不存在"""
        with patch.object(
            kg_service,
            "get_student_graph",
            return_value=None,
        ):
            with pytest.raises(ValueError, match="知识图谱不存在"):
                await kg_service.update_from_practice(
                    db=mock_db_session,
                    student_id="student-123",
                    practice_record={},
                )

    @pytest.mark.asyncio
    async def test_get_weak_points(
        self,
        kg_service,
        mock_db_session,
        mock_knowledge_graph,
    ):
        """测试获取薄弱点"""
        mock_knowledge_graph.ai_analysis = {
            "weak_points": [
                {
                    "topic": "语法",
                    "ability": "grammar",
                    "current_level": 45,
                    "reason": "基础薄弱",
                    "priority": "high",
                }
            ]
        }
        mock_knowledge_graph.abilities = {
            "listening": 50,
            "reading": 80,
            "grammar": 45,
        }

        with patch.object(
            kg_service,
            "get_student_graph",
            return_value=mock_knowledge_graph,
        ):
            weak_points = await kg_service.get_weak_points(
                db=mock_db_session,
                student_id="student-123",
                limit=10,
            )

        # 验证结果
        assert len(weak_points) > 0
        # 应该包含AI分析和能力值识别的薄弱点
        assert any(wp["ability"] == "grammar" for wp in weak_points)
        assert any(wp["ability"] == "listening" for wp in weak_points)

    @pytest.mark.asyncio
    async def test_get_recommendations(
        self,
        kg_service,
        mock_db_session,
        mock_knowledge_graph,
    ):
        """测试获取学习建议"""
        mock_knowledge_graph.ai_analysis = {
            "recommendations": [
                {
                    "priority": "high",
                    "suggestion": "加强语法基础训练",
                    "ability": "grammar",
                }
            ]
        }
        mock_knowledge_graph.abilities = {
            "listening": 40,
            "reading": 80,
            "grammar": 45,
        }

        with patch.object(
            kg_service,
            "get_student_graph",
            return_value=mock_knowledge_graph,
        ):
            recommendations = await kg_service.get_recommendations(
                db=mock_db_session,
                student_id="student-123",
                limit=5,
            )

        # 验证结果
        assert len(recommendations) > 0
        # 应该包含高优先级建议
        assert any(rec["priority"] == "high" for rec in recommendations)

    def test_build_graph_nodes(self, kg_service):
        """测试构建知识图谱节点"""
        ai_analysis = {
            "abilities": {
                "listening": 75,
                "reading": 80,
            },
            "weak_points": [
                {"topic": "语法", "reason": "掌握不足"}
            ],
            "exam_readiness": {
                "ready": False,
            },
        }

        nodes = kg_service._build_graph_nodes(
            ai_analysis=ai_analysis,
            target_exam="CET4",
        )

        # 验证节点类型
        ability_nodes = [n for n in nodes if n["type"] == "ability"]
        exam_nodes = [n for n in nodes if n["type"] == "exam"]
        weak_nodes = [n for n in nodes if n["type"] == "weak_point"]

        assert len(ability_nodes) == 2
        assert len(exam_nodes) == 1
        assert len(weak_nodes) == 1

    def test_build_graph_edges(self, kg_service):
        """测试构建知识图谱边"""
        ai_analysis = {}
        practice_data = []

        edges = kg_service._build_graph_edges(
            ai_analysis=ai_analysis,
            practice_data=practice_data,
        )

        # 验证边的关系类型
        assert len(edges) > 0
        assert all("source" in edge and "target" in edge for edge in edges)

    def test_get_ability_level(self, kg_service):
        """测试获取能力等级"""
        assert kg_service._get_ability_level(95) == "excellent"
        assert kg_service._get_ability_level(80) == "good"
        assert kg_service._get_ability_level(65) == "intermediate"
        assert kg_service._get_ability_level(45) == "basic"
        assert kg_service._get_ability_level(20) == "beginner"

    def test_should_trigger_ai_review(self, kg_service, mock_knowledge_graph):
        """测试判断是否需要AI复盘"""
        # 距离上次分析超过7天
        mock_knowledge_graph.last_ai_analysis_at = datetime(2024, 1, 1)
        mock_knowledge_graph.ai_analysis = {}

        # 假设当前是2024年1月10日
        with patch("app.services.knowledge_graph_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2024, 1, 10)
            result = kg_service._should_trigger_ai_review(mock_knowledge_graph)

        assert result is True

        # 不需要复盘
        mock_knowledge_graph.last_ai_analysis_at = datetime(2024, 1, 9)
        with patch("app.services.knowledge_graph_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2024, 1, 10)
            result = kg_service._should_trigger_ai_review(mock_knowledge_graph)

        assert result is False


class TestGetKnowledgeGraphService:
    """测试知识图谱服务单例"""

    def test_get_knowledge_graph_service_singleton(self):
        """测试获取单例"""
        service1 = get_knowledge_graph_service()
        service2 = get_knowledge_graph_service()

        # 验证返回同一个实例
        assert service1 is service2
