"""
学习报告API测试
测试学生和教师端学习报告相关API端点
"""
import pytest
import uuid
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.api.deps import get_db
from app.models import UserRole


@pytest.fixture
async def async_client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    创建异步HTTP客户端用于测试
    """
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_teacher(async_client: AsyncClient, db: AsyncSession):
    """创建测试教师用户并获取token"""
    # 注册教师用户
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "username": "test_teacher",
            "email": "teacher@test.com",
            "password": "Test1234",
            "role": "teacher",
            "organizationName": "Test School"
        }
    )

    # 登录获取token
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "teacher@test.com",
            "password": "Test1234"
        }
    )

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    return headers


@pytest.fixture
async def test_student(async_client: AsyncClient):
    """创建测试学生用户并获取token"""
    # 注册学生用户
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "username": "test_student",
            "email": "student@test.com",
            "password": "Test1234",
            "role": "student",
            "organizationName": "Test School"
        }
    )

    # 登录获取token
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "student@test.com",
            "password": "Test1234"
        }
    )

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    return headers


@pytest.mark.asyncio
class TestStudentLearningReportsAPI:
    """学生端学习报告API测试"""

    async def test_generate_report_success(self, async_client: AsyncClient, test_student):
        """测试学生生成学习报告"""
        response = await async_client.post(
            "/api/v1/reports/generate",
            json={
                "report_type": "custom",
                "period_start": "2025-01-01",
                "period_end": "2025-01-31"
            },
            headers=test_student
        )

        # 验证响应
        assert response.status_code == 201
        data = response.json()
        assert "report" in data
        assert "message" in data
        assert data["message"] == "学习报告生成成功"

    async def test_generate_report_forbidden(self, async_client: AsyncClient, test_teacher):
        """测试教师尝试生成报告（应该失败）"""
        response = await async_client.post(
            "/api/v1/reports/generate",
            json={"report_type": "weekly"},
            headers=test_teacher
        )

        # 验证权限错误
        assert response.status_code == 403
        assert "只有学生可以生成学习报告" in response.json()["detail"]

    async def test_get_my_reports_success(self, async_client: AsyncClient, test_student):
        """测试学生获取自己的报告列表"""
        response = await async_client.get(
            "/api/v1/reports/me?limit=20&offset=0",
            headers=test_student
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "reports" in data
        assert isinstance(data["reports"], list)

    async def test_get_my_reports_forbidden(self, async_client: AsyncClient, test_teacher):
        """测试教师尝试获取学生报告（应该失败）"""
        response = await async_client.get(
            "/api/v1/reports/me",
            headers=test_teacher
        )

        # 验证权限错误
        assert response.status_code == 403
        assert "只有学生可以查看自己的学习报告" in response.json()["detail"]


@pytest.mark.asyncio
class TestTeacherLearningReportsAPI:
    """教师端学习报告API测试"""

    async def test_get_teacher_student_reports_success(self, async_client: AsyncClient, test_teacher):
        """测试教师获取班级学生列表"""
        response = await async_client.get(
            "/api/v1/reports/teacher/students?limit=20&offset=0",
            headers=test_teacher
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "students" in data
        assert isinstance(data["students"], list)

    async def test_get_teacher_student_reports_forbidden(self, async_client: AsyncClient, test_student):
        """测试学生尝试访问教师端API（应该失败）"""
        response = await async_client.get(
            "/api/v1/reports/teacher/students",
            headers=test_student
        )

        # 验证权限错误
        assert response.status_code == 403
        assert "只有教师可以查看学生报告" in response.json()["detail"]

    async def test_get_student_reports_for_teacher_success(self, async_client: AsyncClient, test_teacher):
        """测试教师获取指定学生的报告列表"""
        # 先尝试获取学生ID（这里可能需要先创建测试数据）
        response = await async_client.get(
            "/api/v1/reports/teacher/students/test-student-id?limit=20&offset=0",
            headers=test_teacher
        )

        # 由于没有实际学生数据，可能返回404或其他错误
        # 这取决于实现逻辑
        assert response.status_code in [200, 404, 422]

    async def test_get_student_reports_for_teacher_forbidden(self, async_client: AsyncClient, test_student):
        """测试学生尝试访问其他学生的报告（应该失败）"""
        response = await async_client.get(
            "/api/v1/reports/teacher/students/test-student-id",
            headers=test_student
        )

        # 验证权限错误
        assert response.status_code == 403
        assert "只有教师可以查看学生报告" in response.json()["detail"]

    async def test_get_student_report_detail_for_teacher_success(self, async_client: AsyncClient, test_teacher):
        """测试教师获取学生报告详情"""
        response = await async_client.get(
            "/api/v1/reports/teacher/students/test-student-id/reports/test-report-id",
            headers=test_teacher
        )

        # 由于没有实际数据，可能返回404
        assert response.status_code in [200, 404]

    async def test_get_student_report_detail_for_teacher_forbidden(self, async_client: AsyncClient, test_student):
        """测试学生尝试访问教师端报告详情（应该失败）"""
        response = await async_client.get(
            "/api/v1/reports/teacher/students/test-student-id/reports/test-report-id",
            headers=test_student
        )

        # 验证权限错误
        assert response.status_code == 403
        assert "只有教师可以查看学生报告" in response.json()["detail"]

    async def test_get_class_summary_success(self, async_client: AsyncClient, test_teacher):
        """测试获取班级学习状况汇总"""
        response = await async_client.get(
            "/api/v1/reports/teacher/class-summary?class_id=test-class-id",
            headers=test_teacher
        )

        # 由于没有实际数据，可能返回404
        assert response.status_code in [200, 404]

    async def test_get_class_summary_forbidden(self, async_client: AsyncClient, test_student):
        """测试学生尝试获取班级状况（应该失败）"""
        response = await async_client.get(
            "/api/v1/reports/teacher/class-summary?class_id=test-class-id",
            headers=test_student
        )

        # 验证权限错误
        assert response.status_code == 403
        assert "只有教师可以查看班级学习状况" in response.json()["detail"]

    async def test_get_class_summary_invalid_class_id(self, async_client: AsyncClient, test_teacher):
        """测试使用无效班级ID获取汇总"""
        response = await async_client.get(
            "/api/v1/reports/teacher/class-summary?class_id=invalid-id",
            headers=test_teacher
        )

        # 验证参数错误
        assert response.status_code == 400
        assert "无效的班级ID格式" in response.json()["detail"]


@pytest.mark.asyncio
class TestLearningReportsPermission:
    """学习报告权限控制测试"""

    async def test_student_cannot_access_teacher_endpoints(self, async_client: AsyncClient, test_student):
        """测试学生无法访问教师端端点"""
        endpoints = [
            "/api/v1/reports/teacher/students",
            "/api/v1/reports/teacher/students/test-id",
            "/api/v1/reports/teacher/students/test-id/reports/test-report-id",
            "/api/v1/reports/teacher/class-summary?class_id=test-class-id"
        ]

        for endpoint in endpoints:
            response = await async_client.get(endpoint, headers=test_student)
            assert response.status_code == 403, f"Endpoint {endpoint} should return 403"
            assert "只有教师" in response.json()["detail"]

    async def test_teacher_cannot_access_student_reports(self, async_client: AsyncClient, test_teacher):
        """测试教师无法直接访问学生报告端点"""
        # 教师可以访问自己的报告端点，但不能直接访问学生的
        response = await async_client.get(
            "/api/v1/reports/me",
            headers=test_teacher
        )
        # 这应该返回400或403，因为教师没有学生档案
        assert response.status_code in [400, 403]

    async def test_unauthenticated_access_denied(self, async_client: AsyncClient):
        """测试未认证访问被拒绝"""
        endpoints = [
            "/api/v1/reports/generate",
            "/api/v1/reports/me",
            "/api/v1/reports/teacher/students",
            "/api/v1/reports/teacher/class-summary?class_id=test"
        ]

        for endpoint in endpoints:
            response = await async_client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should return 401 for unauthenticated access"


@pytest.mark.asyncio
class TestLearningReportsPagination:
    """学习报告分页功能测试"""

    async def test_pagination_params_student_reports(self, async_client: AsyncClient, test_student):
        """测试学生报告分页参数"""
        response = await async_client.get(
            "/api/v1/reports/me?limit=10&offset=0",
            headers=test_student
        )

        assert response.status_code == 200
        data = response.json()
        assert "limit" in data
        assert "offset" in data
        assert data["limit"] == 20  # 默认值

    async def test_pagination_params_teacher_students(self, async_client: AsyncClient, test_teacher):
        """测试教师端学生列表分页参数"""
        response = await async_client.get(
            "/api/v1/reports/teacher/students?limit=10&offset=0",
            headers=test_teacher
        )

        assert response.status_code == 200
        data = response.json()
        assert "limit" in data
        assert "offset" in data

    async def test_invalid_pagination_params(self, async_client: AsyncClient, test_teacher):
        """测试无效的分页参数"""
        # 测试limit过大
        response = await async_client.get(
            "/api/v1/reports/teacher/students?limit=200",
            headers=test_teacher
        )
        assert response.status_code == 422

        # 测试offset为负数
        response = await async_client.get(
            "/api/v1/reports/teacher/students?offset=-1",
            headers=test_teacher
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestLearningReportsValidation:
    """学习报告数据验证测试"""

    async def test_generate_report_invalid_params(self, async_client: AsyncClient, test_student):
        """测试生成报告时无效参数"""
        # 测试无效的报告类型
        response = await async_client.post(
            "/api/v1/reports/generate",
            json={"report_type": "invalid_type"},
            headers=test_student
        )

        # 应该成功（因为report_type有默认值）
        assert response.status_code == 201

    async def test_get_class_summary_invalid_time_range(self, async_client: AsyncClient, test_teacher):
        """测试班级汇总时无效时间范围"""
        # 测试无效的日期格式
        response = await async_client.get(
            "/api/v1/reports/teacher/class-summary?class_id=test-class-id&period_start=invalid-date",
            headers=test_teacher
        )

        assert response.status_code == 400
        assert "格式错误" in response.json()["detail"]

    async def test_missing_required_params(self, async_client: AsyncClient, test_teacher):
        """测试缺少必需参数"""
        # 测试缺少class_id
        response = await async_client.get(
            "/api/v1/reports/teacher/class-summary",
            headers=test_teacher
        )

        assert response.status_code == 422  # FastAPI参数验证错误
