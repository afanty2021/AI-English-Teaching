"""
学习报告服务测试
测试学习报告生成、查询、权限验证等服务层方法
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.learning_report_service import LearningReportService, get_learning_report_service
from app.models import User, UserRole, Student, Teacher, Organization
from app.models.learning_report import LearningReport


class TestLearningReportService:
    """学习报告服务测试类"""

    @pytest.fixture
    async def mock_db(self):
        """创建模拟数据库会话"""
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def service(self, mock_db):
        """创建学习报告服务实例"""
        return LearningReportService(mock_db)

    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_db):
        """测试服务初始化"""
        service = LearningReportService(mock_db)
        assert service.db == mock_db
        assert service.kg_service is not None

    @pytest.mark.asyncio
    async def test_get_learning_report_service(self, mock_db):
        """测试获取服务实例"""
        service = get_learning_report_service(mock_db)
        assert isinstance(service, LearningReportService)
        assert service.db == mock_db

    @pytest.mark.asyncio
    async def test_generate_statistics(self, service, mock_db):
        """测试生成统计数据"""
        # 模拟查询结果
        mock_practice_result = AsyncMock()
        mock_practice_result.scalar_one_or_none.return_value = type('Practice', (), {
            'total_count': 100,
            'completed_count': 80,
            'total_duration': 1200
        })()

        mock_mistake_result = AsyncMock()
        mock_mistake_result.scalar_one_or_none.return_value = type('Mistake', (), {
            'mistake_count': 20,
            'by_type': {'grammar': 10, 'vocabulary': 5, 'reading': 5}
        })()

        # 设置mock返回值
        mock_db.execute.side_effect = [
            mock_practice_result,
            mock_mistake_result
        ]

        # 调用方法
        student_id = uuid.uuid4()
        period_start = datetime.utcnow() - timedelta(days=30)
        period_end = datetime.utcnow()

        statistics = await service.generate_statistics(student_id, period_start, period_end)

        # 验证结果
        assert statistics is not None
        assert isinstance(statistics, dict)
        assert "total_practices" in statistics
        assert "completed_practices" in statistics
        assert "completion_rate" in statistics

    @pytest.mark.asyncio
    async def test_analyze_ability_progress(self, service, mock_db):
        """测试能力分析"""
        # 模拟学生和知识图谱
        mock_student = type('Student', (), {
            'knowledge_graph': type('KnowledgeGraph', (), {
                'nodes': {
                    'abilities': {
                        'listening': {'level': 75, 'confidence': 0.8},
                        'reading': {'level': 80, 'confidence': 0.9},
                        'writing': {'level': 70, 'confidence': 0.7}
                    }
                },
                'updated_at': datetime.utcnow()
            })
        })()

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_student
        mock_db.execute.return_value = mock_result

        # 调用方法
        student_id = uuid.uuid4()
        period_start = datetime.utcnow() - timedelta(days=30)
        period_end = datetime.utcnow()

        analysis = await service.analyze_ability_progress(student_id, period_start, period_end)

        # 验证结果
        assert analysis is not None
        assert isinstance(analysis, dict)
        assert "current_abilities" in analysis
        assert "ability_radar" in analysis
        assert "strongest_area" in analysis
        assert "weakest_area" in analysis

        # 验证雷达图数据
        assert len(analysis["ability_radar"]) > 0
        assert all("name" in item for item in analysis["ability_radar"])
        assert all("value" in item for item in analysis["ability_radar"])

    @pytest.mark.asyncio
    async def test_analyze_weak_points(self, service, mock_db):
        """测试薄弱点分析"""
        # 模拟错题数据
        mock_mistakes = [
            type('Mistake', (), {
                'knowledge_points': ['语法错误', '时态'],
                'topic': '语法',
                'difficulty_level': '中级'
            }),
            type('Mistake', (), {
                'knowledge_points': ['词汇搭配'],
                'topic': '词汇',
                'difficulty_level': '初级'
            })
        ]

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_mistakes
        mock_db.execute.return_value = mock_result

        # 调用方法
        student_id = uuid.uuid4()
        period_start = datetime.utcnow() - timedelta(days=30)
        period_end = datetime.utcnow()

        weak_points = await service.analyze_weak_points(student_id, period_start, period_end)

        # 验证结果
        assert weak_points is not None
        assert isinstance(weak_points, dict)
        assert "total_unmastered" in weak_points
        assert "knowledge_points" in weak_points
        assert "by_topic" in weak_points
        assert "top_weak_points" in weak_points

        # 验证薄弱点统计
        assert weak_points["total_unmastered"] == 2
        assert len(weak_points["knowledge_points"]) > 0

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, service, mock_db):
        """测试生成学习建议"""
        # 模拟统计数据和能力分析
        mock_statistics = {
            "total_practices": 100,
            "completion_rate": 0.8,
            "avg_correct_rate": 0.75
        }

        mock_ability_analysis = {
            "weakest_area": {"name": "writing", "level": 60}
        }

        mock_weak_points = {
            "knowledge_points": {"语法错误": 5, "时态": 3}
        }

        # 调用方法
        student_id = uuid.uuid4()

        recommendations = await service.generate_recommendations(
            student_id, mock_statistics, mock_ability_analysis, mock_weak_points
        )

        # 验证结果
        assert recommendations is not None
        assert isinstance(recommendations, dict)
        assert "rule_based" in recommendations
        assert isinstance(recommendations["rule_based"], list)

        # 验证建议内容
        if recommendations["rule_based"]:
            rec = recommendations["rule_based"][0]
            assert "category" in rec
            assert "priority" in rec
            assert "title" in rec
            assert "description" in rec

    @pytest.mark.asyncio
    async def test_verify_student_belongs_to_teacher_success(self, service, mock_db):
        """测试验证学生属于教师（成功）"""
        # 模拟查询返回计数 > 0
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 1  # 学生属于该教师
        mock_db.execute.return_value = mock_result

        # 调用方法（应该不抛出异常）
        teacher_id = uuid.uuid4()
        student_id = uuid.uuid4()

        await service.verify_student_belongs_to_teacher(teacher_id, student_id)

        # 验证调用
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_student_belongs_to_teacher_failure(self, service, mock_db):
        """测试验证学生属于教师（失败）"""
        # 模拟查询返回计数 = 0
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 0  # 学生不属于该教师
        mock_db.execute.return_value = mock_result

        # 调用方法应该抛出HTTPException
        from fastapi import HTTPException

        teacher_id = uuid.uuid4()
        student_id = uuid.uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await service.verify_student_belongs_to_teacher(teacher_id, student_id)

        assert exc_info.value.status_code == 404
        assert "学生不存在或不属于该教师" in str(exc_info.value.detail)


class TestLearningReportServiceIntegration:
    """学习报告服务集成测试"""

    @pytest.mark.asyncio
    async def test_get_student_reports_for_teacher(self, mock_db):
        """测试教师获取学生报告列表"""
        service = LearningReportService(mock_db)

        # 模拟权限验证通过
        with patch.object(service, 'verify_student_belongs_to_teacher', new_callable=AsyncMock):
            # 模拟查询结果
            mock_reports = [
                type('LearningReport', (), {
                    'id': uuid.uuid4(),
                    'report_type': 'weekly',
                    'period_start': datetime.utcnow() - timedelta(days=7),
                    'period_end': datetime.utcnow(),
                    'status': 'completed',
                    'title': 'Weekly Report'
                })()
            ]

            mock_count_result = AsyncMock()
            mock_count_result.scalar.return_value = 1

            mock_reports_result = AsyncMock()
            mock_reports_result.scalars.return_value.all.return_value = mock_reports

            # 设置mock返回值
            mock_db.execute.side_effect = [mock_count_result, mock_reports_result]

            # 调用方法
            teacher_id = uuid.uuid4()
            student_id = uuid.uuid4()

            reports, total = await service.get_student_reports_for_teacher(
                teacher_id, student_id, limit=10, offset=0
            )

            # 验证结果
            assert total == 1
            assert len(reports) == 1
            assert reports[0].report_type == 'weekly'


class TestLearningReportServiceErrorHandling:
    """学习报告服务错误处理测试"""

    @pytest.mark.asyncio
    async def test_generate_report_database_error(self, mock_db):
        """测试生成报告时数据库错误"""
        service = LearningReportService(mock_db)

        # 模拟数据库错误
        mock_db.commit.side_effect = Exception("Database error")

        # 调用方法应该抛出异常
        student_id = uuid.uuid4()

        with pytest.raises(Exception):
            await service.generate_report(student_id, "weekly")

    @pytest.mark.asyncio
    async def test_analyze_ability_no_student(self, service, mock_db):
        """测试分析能力时学生不存在"""
        # 模拟查询返回None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # 调用方法
        student_id = uuid.uuid4()
        period_start = datetime.utcnow() - timedelta(days=30)
        period_end = datetime.utcnow()

        analysis = await service.analyze_ability_progress(student_id, period_start, period_end)

        # 验证空结果
        assert analysis is not None
        assert "current_abilities" in analysis
        assert analysis["current_abilities"] == {}


class TestLearningReportServiceEdgeCases:
    """学习报告服务边界情况测试"""

    @pytest.mark.asyncio
    async def test_generate_statistics_empty_period(self, service, mock_db):
        """测试生成统计数据时时间段为空"""
        # 模拟空查询结果
        mock_practice_result = AsyncMock()
        mock_practice_result.scalar_one_or_none.return_value = None

        mock_mistake_result = AsyncMock()
        mock_mistake_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_practice_result, mock_mistake_result]

        # 调用方法
        student_id = uuid.uuid4()
        period_start = datetime.utcnow()
        period_end = datetime.utcnow()

        statistics = await service.generate_statistics(student_id, period_start, period_end)

        # 验证空数据处理
        assert statistics is not None
        assert statistics["total_practices"] == 0
        assert statistics["completion_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_analyze_weak_points_no_mistakes(self, service, mock_db):
        """测试薄弱点分析时没有错题"""
        # 模拟空错题列表
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        # 调用方法
        student_id = uuid.uuid4()
        period_start = datetime.utcnow() - timedelta(days=30)
        period_end = datetime.utcnow()

        weak_points = await service.analyze_weak_points(student_id, period_start, period_end)

        # 验证空错题处理
        assert weak_points is not None
        assert weak_points["total_unmastered"] == 0
        assert len(weak_points["knowledge_points"]) == 0
        assert len(weak_points["top_weak_points"]) == 0
