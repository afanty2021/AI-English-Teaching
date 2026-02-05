"""
教案导出API测试
测试导出任务管理、模板等功能
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from datetime import datetime

from app.models import User, Organization, Teacher, Student
from app.core.security import create_access_token


class TestExportTemplatesAPI:
    """导出模板API测试"""

    @pytest.mark.asyncio
    async def test_get_export_templates(
        self, test_client, test_teacher
    ):
        """测试获取导出模板列表"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.get(
            "/api/v1/lesson-export/templates",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)

    @pytest.mark.asyncio
    async def test_export_templates_structure(
        self, test_client, test_teacher
    ):
        """测试导出模板结构"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.get(
            "/api/v1/lesson-export/templates",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        for template in data["templates"]:
            assert "id" in template
            assert "name" in template
            assert "format" in template


class TestExportTaskCreateAPI:
    """创建导出任务API测试"""

    @pytest.mark.asyncio
    async def test_create_export_task(
        self, test_client, test_teacher
    ):
        """测试创建导出任务"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.post(
            "/api/v1/lesson-export/tasks",
            params={"lesson_id": str(uuid4()), "format": "word"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "task" in data
        assert "id" in data["task"]
        assert "status" in data["task"]

    @pytest.mark.asyncio
    async def test_create_export_task_with_options(
        self, test_client, test_teacher
    ):
        """测试创建带选项的导出任务"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.post(
            "/api/v1/lesson-export/tasks",
            params={
                "lesson_id": str(uuid4()),
                "format": "pdf",
                "sections": "overview,objectives,vocabulary",
                "include_teacher_notes": True,
                "include_answers": False,
                "language": "zh",
                "include_page_numbers": True,
                "include_toc": True
            },
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "task" in data

    @pytest.mark.asyncio
    async def test_create_export_task_invalid_format(
        self, test_client, test_teacher
    ):
        """测试创建无效格式的导出任务"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.post(
            "/api/v1/lesson-export/tasks",
            params={
                "lesson_id": str(uuid4()),
                "format": "invalid_format"
            },
            headers=headers
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_student_cannot_create_export_task(
        self, test_client, test_student
    ):
        """测试学生不能创建导出任务"""
        token = create_access_token(data={"sub": str(test_student.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.post(
            "/api/v1/lesson-export/tasks",
            params={"lesson_id": str(uuid4()), "format": "word"},
            headers=headers
        )
        assert response.status_code == 403


class TestExportTaskBatchCreateAPI:
    """批量创建导出任务API测试"""

    @pytest.mark.asyncio
    async def test_create_batch_export_tasks(
        self, test_client, test_teacher
    ):
        """测试批量创建导出任务"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        lesson_ids = [str(uuid4()), str(uuid4()), str(uuid4())]
        response = await test_client.post(
            "/api/v1/lesson-export/tasks/batch",
            params={"lesson_ids": lesson_ids, "format": "pdf"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert data["total"] == len(lesson_ids)


class TestExportTaskGetAPI:
    """获取导出任务API测试"""

    @pytest.mark.asyncio
    async def test_get_export_task(
        self, test_client, test_teacher
    ):
        """测试获取导出任务"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        # 先创建任务
        create_response = await test_client.post(
            "/api/v1/lesson-export/tasks",
            params={"lesson_id": str(uuid4()), "format": "word"},
            headers=headers
        )
        task_id = create_response.json()["task"]["id"]

        # 获取任务
        response = await test_client.get(
            f"/api/v1/lesson-export/tasks/{task_id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "task" in data
        assert data["task"]["id"] == task_id

    @pytest.mark.asyncio
    async def test_get_export_task_not_found(
        self, test_client, test_teacher
    ):
        """测试获取不存在的任务"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        fake_id = str(uuid4())
        response = await test_client.get(
            f"/api/v1/lesson-export/tasks/{fake_id}",
            headers=headers
        )
        assert response.status_code == 404


class TestExportTaskListAPI:
    """导出任务列表API测试"""

    @pytest.mark.asyncio
    async def test_get_export_tasks(
        self, test_client, test_teacher
    ):
        """测试获取导出任务列表"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.get(
            "/api/v1/lesson-export/tasks",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_export_tasks_with_filters(
        self, test_client, test_teacher
    ):
        """测试带过滤的导出任务列表"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.get(
            "/api/v1/lesson-export/tasks",
            params={
                "lesson_id": str(uuid4()),
                "status": "completed",
                "limit": 10,
                "offset": 0
            },
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data


class TestExportTaskCancelAPI:
    """取消导出任务API测试"""

    @pytest.mark.asyncio
    async def test_cancel_export_task(
        self, test_client, test_teacher
    ):
        """测试取消导出任务"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        # 先创建任务
        create_response = await test_client.post(
            "/api/v1/lesson-export/tasks",
            params={"lesson_id": str(uuid4()), "format": "word"},
            headers=headers
        )
        task_id = create_response.json()["task"]["id"]

        # 取消任务
        response = await test_client.post(
            f"/api/v1/lesson-export/tasks/{task_id}/cancel",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestExportTaskDeleteAPI:
    """删除导出任务API测试"""

    @pytest.mark.asyncio
    async def test_delete_export_task(
        self, test_client, test_teacher
    ):
        """测试删除导出任务"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        # 先创建任务
        create_response = await test_client.post(
            "/api/v1/lesson-export/tasks",
            params={"lesson_id": str(uuid4()), "format": "word"},
            headers=headers
        )
        task_id = create_response.json()["task"]["id"]

        # 删除任务
        response = await test_client.delete(
            f"/api/v1/lesson-export/tasks/{task_id}",
            headers=headers
        )
        assert response.status_code == 200


class TestExportFormatValidation:
    """导出格式验证测试"""

    @pytest.mark.asyncio
    async def test_valid_formats(self, test_client, test_teacher):
        """测试支持的导出格式"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        valid_formats = ["word", "pdf", "pptx", "markdown"]

        for format_type in valid_formats:
            response = await test_client.post(
                "/api/v1/lesson-export/tasks",
                params={"lesson_id": str(uuid4()), "format": format_type},
                headers=headers
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_format(self, test_client, test_teacher):
        """测试不支持的导出格式"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.post(
            "/api/v1/lesson-export/tasks",
            params={"lesson_id": str(uuid4()), "format": "excel"},
            headers=headers
        )
        assert response.status_code == 400


class TestExportSectionsValidation:
    """导出章节验证测试"""

    @pytest.mark.asyncio
    async def test_valid_sections(
        self, test_client, test_teacher
    ):
        """测试有效的导出章节"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.post(
            "/api/v1/lesson-export/tasks",
            params={
                "lesson_id": str(uuid4()),
                "format": "word",
                "sections": "overview,objectives,vocabulary,grammar,structure"
            },
            headers=headers
        )
        assert response.status_code == 200
