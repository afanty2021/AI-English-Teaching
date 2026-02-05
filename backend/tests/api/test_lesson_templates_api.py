"""
教案模板API测试
测试模板CRUD、应用、收藏等功能
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from datetime import datetime

from app.models import User, Organization, Teacher, LessonPlanTemplate, Student
from app.core.security import create_access_token


class TestTemplateListAPI:
    """模板列表API测试"""

    @pytest.mark.asyncio
    async def test_list_templates(
        self, test_client, test_teacher, db
    ):
        """测试获取模板列表"""
        # 创建测试模板
        template = LessonPlanTemplate(
            id=uuid4(),
            name="阅读理解模板",
            description="用于阅读理解教学的模板",
            level="B1",
            template_structure={
                "sections": [
                    {"key": "warm_up", "label": "热身活动", "duration": 10, "required": True}
                ]
            },
            is_system=False,
            is_public=True,
            created_by=test_teacher.user_id
        )
        db.add(template)
        await db.commit()

        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.get(
            "/api/v1/lesson-templates",
            params={"page": 1, "page_size": 20},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    @pytest.mark.asyncio
    async def test_list_templates_with_search(
        self, test_client, test_teacher, db
    ):
        """测试带搜索的模板列表"""
        template = LessonPlanTemplate(
            id=uuid4(),
            name="阅读理解模板",
            description="测试模板",
            level="B1",
            template_structure={"sections": []},
            is_system=False,
            is_public=True,
            created_by=test_teacher.user_id
        )
        db.add(template)
        await db.commit()

        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.get(
            "/api/v1/lesson-templates",
            params={"search": "阅读", "is_public": True},
            headers=headers
        )
        assert response.status_code == 200


class TestTemplateDetailAPI:
    """模板详情API测试"""

    @pytest.mark.asyncio
    async def test_get_template_detail(
        self, test_client, test_teacher, db
    ):
        """测试获取模板详情"""
        template = LessonPlanTemplate(
            id=uuid4(),
            name="阅读理解模板",
            description="测试模板",
            level="B1",
            template_structure={"sections": []},
            is_system=False,
            is_public=True,
            created_by=test_teacher.user_id
        )
        db.add(template)
        await db.commit()

        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.get(
            f"/api/v1/lesson-templates/{template.id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "template" in data
        assert data["template"]["name"] == "阅读理解模板"

    @pytest.mark.asyncio
    async def test_get_template_not_found(
        self, test_client, test_teacher
    ):
        """测试获取不存在的模板"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        fake_id = str(uuid4())
        response = await test_client.get(
            f"/api/v1/lesson-templates/{fake_id}",
            headers=headers
        )
        assert response.status_code == 404


class TestTemplateCreateAPI:
    """创建模板API测试"""

    @pytest.mark.asyncio
    async def test_create_template(
        self, test_client, test_teacher
    ):
        """测试创建模板"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.post(
            "/api/v1/lesson-templates",
            json={
                "name": "新模板",
                "description": "测试创建的模板",
                "category_key": "reading",
                "level": "B2",
                "duration": 60,
                "structure": {
                    "sections": [
                        {"key": "presentation", "label": "讲解", "duration": 30, "required": True}
                    ]
                },
                "is_public": True
            },
            headers=headers
        )
        assert response.status_code == 201
        data = response.json()
        assert "template" in data
        assert data["template"]["name"] == "新模板"

    @pytest.mark.asyncio
    async def test_student_cannot_create_template(
        self, test_client, test_student
    ):
        """测试学生不能创建模板"""
        token = create_access_token(data={"sub": str(test_student.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.post(
            "/api/v1/lesson-templates",
            json={
                "name": "学生模板",
                "level": "B1",
                "structure": {"sections": []}
            },
            headers=headers
        )
        assert response.status_code == 403


class TestTemplateUpdateAPI:
    """更新模板API测试"""

    @pytest.mark.asyncio
    async def test_update_template(
        self, test_client, test_teacher, db
    ):
        """测试更新模板"""
        template = LessonPlanTemplate(
            id=uuid4(),
            name="原模板",
            description="原描述",
            level="B1",
            template_structure={"sections": []},
            is_system=False,
            is_public=True,
            created_by=test_teacher.user_id
        )
        db.add(template)
        await db.commit()

        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.put(
            f"/api/v1/lesson-templates/{template.id}",
            json={"name": "更新后的模板", "description": "更新描述"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "template" in data


class TestTemplateDeleteAPI:
    """删除模板API测试"""

    @pytest.mark.asyncio
    async def test_delete_template(
        self, test_client, test_teacher
    ):
        """测试删除模板"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        # 先创建模板
        response = await test_client.post(
            "/api/v1/lesson-templates",
            json={
                "name": "待删除模板",
                "level": "B1",
                "structure": {"sections": []}
            },
            headers=headers
        )
        assert response.status_code == 201
        template_id = response.json()["template"]["id"]

        # 删除模板
        response = await test_client.delete(
            f"/api/v1/lesson-templates/{template_id}",
            headers=headers
        )
        assert response.status_code == 204


class TestTemplateDuplicateAPI:
    """复制模板API测试"""

    @pytest.mark.asyncio
    async def test_duplicate_template(
        self, test_client, test_teacher, db
    ):
        """测试复制模板"""
        template = LessonPlanTemplate(
            id=uuid4(),
            name="原模板",
            description="测试模板",
            level="B1",
            template_structure={"sections": []},
            is_system=False,
            is_public=True,
            created_by=test_teacher.user_id
        )
        db.add(template)
        await db.commit()

        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.post(
            f"/api/v1/lesson-templates/{template.id}/duplicate",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "template" in data
        assert "副本" in data["template"]["name"]


class TestTemplateApplyAPI:
    """应用模板API测试"""

    @pytest.mark.asyncio
    async def test_apply_template(
        self, test_client, test_teacher, db
    ):
        """测试应用模板生成教案"""
        template = LessonPlanTemplate(
            id=uuid4(),
            name="测试模板",
            description="测试",
            level="B1",
            template_structure={"sections": []},
            is_system=False,
            is_public=True,
            created_by=test_teacher.user_id
        )
        db.add(template)
        await db.commit()

        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.post(
            f"/api/v1/lesson-templates/{template.id}/apply",
            json={
                "title": "基于模板的教案",
                "topic": "阅读理解"
            },
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "lesson_plan_id" in data
        assert "lesson_plan" in data


class TestTemplateFavoriteAPI:
    """收藏模板API测试"""

    @pytest.mark.asyncio
    async def test_toggle_favorite(
        self, test_client, test_teacher, db
    ):
        """测试切换收藏状态"""
        template = LessonPlanTemplate(
            id=uuid4(),
            name="测试模板",
            description="测试",
            level="B1",
            template_structure={"sections": []},
            is_system=False,
            is_public=True,
            created_by=test_teacher.user_id
        )
        db.add(template)
        await db.commit()

        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.post(
            f"/api/v1/lesson-templates/{template.id}/favorite",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "favorited" in data


class TestTemplateCategoriesAPI:
    """模板分类API测试"""

    @pytest.mark.asyncio
    async def test_get_categories(
        self, test_client, test_teacher
    ):
        """测试获取模板分类"""
        token = create_access_token(data={"sub": str(test_teacher.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.get(
            "/api/v1/lesson-templates/categories",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for category in data:
            assert "key" in category
            assert "label" in category
