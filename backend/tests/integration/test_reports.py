"""
报告系统集成测试 - AI英语教学系统
测试学习报告的完整功能流程
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4, UUID

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import User, Student
from app.models.async_task import AsyncTask, AsyncTaskStatus, AsyncTaskType
from app.models.learning_report import LearningReport
from app.services.async_task_service import AsyncTaskService
from app.services.chart_data_service import ChartDataService
from app.services.learning_report_service import LearningReportService


# ============ Fixture ============

@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """创建测试用户"""
    # 使用已有的测试用户或创建新的
    user = User(
        id=uuid4(),
        username="test_student",
        email="student@test.com",
        hashed_password="hashed_password",
        role="student",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_student(db: AsyncSession, test_user: User) -> Student:
    """创建测试学生档案"""
    student = Student(
        id=test_user.id,
        user_id=test_user.id,
        student_id="S2024001",
        grade="大一",
        target_exam="CET4",
        target_score=500,
        current_level="B1",
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


@pytest_asyncio.fixture
async def test_report(db: AsyncSession, test_student: Student) -> LearningReport:
    """创建测试报告"""
    report = LearningReport(
        id=uuid4(),
        student_id=test_student.id,
        report_type="weekly",
        period_start=datetime.utcnow() - timedelta(days=7),
        period_end=datetime.utcnow(),
        title="周学习报告",
        description="测试周报告",
        status="completed",
        statistics={
            "total_practices": 50,
            "completion_rate": 85.5,
            "avg_correct_rate": 78.2,
        },
        ability_analysis={
            "vocabulary": 75,
            "grammar": 68,
            "reading": 82,
        },
        weak_points={
            "total_unmastered": 5,
            "knowledge_points": {"动词时态": 3, "介词搭配": 2},
        },
        recommendations=[
            {
                "category": "vocabulary",
                "priority": "high",
                "title": "加强动词时态练习",
                "description": "建议每天练习10道动词时态题目",
            }
        ],
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


# ============ API 测试 ============

class TestReportAPI:
    """报告API测试"""

    @pytest.mark.asyncio
    async def test_get_reports_list(self, client: AsyncClient, test_student: Student):
        """测试获取报告列表"""
        response = await client.get(
            "/api/v1/reports/me",
          headers={"Authorization": f"Bearer {test_student.id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "items" in data["data"]

    @pytest.mark.asyncio
    async def test_get_report_detail(
        self, client: AsyncClient, test_report: LearningReport
    ):
        """测试获取报告详情"""
        response = await client.get(
            f"/api/v1/reports/{test_report.id}",
            headers={"Authorization": f"Bearer {test_report.student_id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["id"] == str(test_report.id)

    @pytest.mark.asyncio
    async def test_get_nonexistent_report(self, client: AsyncClient, test_student: Student):
        """测试获取不存在的报告"""
        fake_id = str(uuid4())
        response = await client.get(
            f"/api/v1/reports/{fake_id}",
            headers={"Authorization": f"Bearer {test_student.id}"}
        )

        assert response.status_code == 404


class TestChartAPI:
    """图表API测试"""

    @pytest.mark.asyncio
    async def test_get_learning_trend(
        self, client: AsyncClient, test_report: LearningReport
    ):
        """测试获取学习趋势数据"""
        response = await client.get(
            f"/api/v1/reports/{test_report.id}/charts/learning-trend?period=30d&metrics=practices,correctRate",
            headers={"Authorization": f"Bearer {test_report.student_id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "data" in data

    @pytest.mark.asyncio
    async def test_get_ability_radar(
        self, client: AsyncClient, test_report: LearningReport
    ):
        """测试获取能力雷达图数据"""
        response = await client.get(
            f"/api/v1/reports/{test_report.id}/charts/ability-radar?compare_with=class_avg",
            headers={"Authorization": f"Bearer {test_report.student_id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

    @pytest.mark.asyncio
    async def test_get_knowledge_heatmap(
        self, client: AsyncClient, test_report: LearningReport
    ):
        """测试获取知识热力图数据"""
        response = await client.get(
            f"/api/v1/reports/{test_report.id}/charts/knowledge-heatmap?filter_by_ability=vocabulary",
            headers={"Authorization": f"Bearer {test_report.student_id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0


class TestExportAPI:
    """导出API测试"""

    @pytest.mark.asyncio
    async def test_export_report(
        self, client: AsyncClient, test_report: LearningReport
    ):
        """测试导出报告"""
        response = await client.post(
            f"/api/v1/reports/{test_report.id}/export?format=pdf",
            headers={"Authorization": f"Bearer {test_report.student_id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "taskId" in data["data"]


class TestTaskAPI:
    """任务API测试"""

    @pytest.mark.asyncio
    async def test_get_task_status(
        self, client: AsyncClient, db: AsyncSession, test_report: LearningReport
    ):
        """测试获取任务状态"""
        # 先创建任务
        async_task_service = AsyncTaskService(db)
        task = await async_task_service.create_task(
            user_id=test_report.student_id,
            task_type=AsyncTaskType.REPORT_EXPORT.value,
            input_params={"report_id": str(test_report.id)},
        )

        response = await client.get(
            f"/api/v1/tasks/{task.id}",
            headers={"Authorization": f"Bearer {test_report.student_id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["id"] == str(task.id)

    @pytest.mark.asyncio
    async def test_list_tasks(
        self, client: AsyncClient, test_report: LearningReport
    ):
        """测试列出任务"""
        response = await client.get(
            "/api/v1/tasks?status_filter=pending&limit=10",
            headers={"Authorization": f"Bearer {test_report.student_id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "items" in data["data"]

    @pytest.mark.asyncio
    async def test_cancel_task(
        self, client: AsyncClient, db: AsyncSession, test_report: LearningReport
    ):
        """测试取消任务"""
        # 先创建任务
        async_task_service = AsyncTaskService(db)
        task = await async_task_service.create_task(
            user_id=test_report.student_id,
            task_type=AsyncTaskType.REPORT_GENERATE.value,
        )

        response = await client.delete(
            f"/api/v1/tasks/{task.id}/cancel",
            headers={"Authorization": f"Bearer {test_report.student_id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

    @pytest.mark.asyncio
    async def test_retry_task(
        self, client: AsyncClient, db: AsyncSession, test_report: LearningReport
    ):
        """测试重试任务"""
        # 先创建失败的任务
        async_task_service = AsyncTaskService(db)
        task = await async_task_service.create_task(
            user_id=test_report.student_id,
            task_type=AsyncTaskType.REPORT_GENERATE.value,
        )
        await async_task_service.fail_task(task.id, "测试错误")

        response = await client.post(
            f"/api/v1/tasks/{task.id}/retry",
            headers={"Authorization": f"Bearer {test_report.student_id}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0


# ============ 服务测试 ============

class TestLearningReportService:
    """学习报告服务测试"""

    @pytest.mark.asyncio
    async def test_generate_report(
        self, db: AsyncSession, test_student: Student
    ):
        """测试生成报告"""
        report_service = LearningReportService(db)

        report = await report_service.generate_report(
            student_id=test_student.id,
            report_type="weekly",
            period_start=datetime.utcnow() - timedelta(days=7),
            period_end=datetime.utcnow(),
        )

        assert report is not None
        assert report.student_id == test_student.id
        assert report.report_type == "weekly"
        assert report.status == "completed"

    @pytest.mark.asyncio
    async def test_get_report_by_id(
        self, db: AsyncSession, test_report: LearningReport
    ):
        """测试通过ID获取报告"""
        report_service = LearningReportService(db)

        report = await report_service.get_report_by_id(test_report.id)

        assert report is not None
        assert report.id == test_report.id


class TestChartDataService:
    """图表数据服务测试"""

    @pytest.mark.asyncio
    async def test_get_learning_trend_data(
        self, db: AsyncSession, test_student: Student
    ):
        """测试获取学习趋势数据"""
        chart_service = ChartDataService(db)

        data = await chart_service.get_learning_trend_data(
            student_id=test_student.id,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
            metrics=["practices", "correctRate", "duration"],
        )

        assert data is not None
        assert "period" in data
        assert "metrics" in data

    @pytest.mark.asyncio
    async def test_get_ability_radar_data(
        self, db: AsyncSession, test_student: Student
    ):
        """测试获取能力雷达图数据"""
        chart_service = ChartDataService(db)

        data = await chart_service.get_ability_radar_data(
            student_id=test_student.id,
            compare_with="class_avg",
        )

        assert data is not None
        assert "abilities" in data

    @pytest.mark.asyncio
    async def test_get_knowledge_heatmap_data(
        self, db: AsyncSession, test_student: Student
    ):
        """测试获取知识热力图数据"""
        chart_service = ChartDataService(db)

        data = await chart_service.get_knowledge_heatmap_data(
            student_id=test_student.id,
            filter_by_ability="vocabulary",
        )

        assert data is not None
        assert "topics" in data or data == []


# ============ 端到端测试 ============

class TestReportE2E:
    """报告系统端到端测试"""

    @pytest.mark.asyncio
    async def test_complete_report_flow(
        self, client: AsyncClient, db: AsyncSession, test_student: Student
    ):
        """测试完整报告流程"""
        # 1. 生成报告
        generate_response = await client.post(
            "/api/v1/reports/generate?report_type=weekly",
            headers={"Authorization": f"Bearer {test_student.id}"}
        )
        assert generate_response.status_code == 200
        task_id = generate_response.json()["data"]["taskId"]

        # 2. 查询任务状态
        status_response = await client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {test_student.id}"}
        )
        assert status_response.status_code == 200

        # 3. 获取报告列表
        list_response = await client.get(
            "/api/v1/reports/me",
            headers={"Authorization": f"Bearer {test_student.id}"}
        )
        assert list_response.status_code == 200

        # 4. 获取图表数据
        # 需要先获取报告ID
        if list_response.json()["data"]["items"]:
            report_id = list_response.json()["data"]["items"][0]["id"]

            chart_response = await client.get(
                f"/api/v1/reports/{report_id}/charts/ability-radar",
                headers={"Authorization": f"Bearer {test_student.id}"}
            )
            assert chart_response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_flow(
        self, client: AsyncClient, db: AsyncSession, test_report: LearningReport
    ):
        """测试导出流程"""
        # 1. 提交导出任务
        export_response = await client.post(
            f"/api/v1/reports/{test_report.id}/export?format=pdf",
            headers={"Authorization": f"Bearer {test_report.student_id}"}
        )
        assert export_response.status_code == 200
        task_id = export_response.json()["data"]["taskId"]

        # 2. 查询导出任务状态
        status_response = await client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {test_report.student_id}"}
        )
        assert status_response.status_code == 200


# ============ 性能测试 ============

class TestReportPerformance:
    """报告系统性能测试"""

    @pytest.mark.asyncio
    async def test_api_response_time(self, client: AsyncClient, test_report: LearningReport):
        """测试API响应时间"""
        import time

        # 测量报告详情API响应时间
        start = time.time()
        response = await client.get(
            f"/api/v1/reports/{test_report.id}",
            headers={"Authorization": f"Bearer {test_report.student_id}"}
        )
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0  # 应该小于1秒

    @pytest.mark.asyncio
    async def test_chart_api_performance(self, client: AsyncClient, test_report: LearningReport):
        """测试图表API性能"""
        import time

        start = time.time()
        response = await client.get(
            f"/api/v1/reports/{test_report.id}/charts/ability-radar",
            headers={"Authorization": f"Bearer {test_report.student_id}"}
        )
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 2.0  # 应该小于2秒


# ============ 并发测试 ============

class TestReportConcurrency:
    """报告系统并发测试"""

    @pytest.mark.asyncio
    async def test_concurrent_export_requests(
        self, client: AsyncClient, test_report: LearningReport
    ):
        """测试并发导出请求"""
        import asyncio

        async def make_export_request():
            return await client.post(
                f"/api/v1/reports/{test_report.id}/export?format=pdf",
                headers={"Authorization": f"Bearer {test_report.student_id}"}
            )

        # 并发发送3个请求
        responses = await asyncio.gather(
            make_export_request(),
            make_export_request(),
            make_export_request(),
        )

        # 所有请求都应该成功
        for response in responses:
            assert response.status_code == 200
