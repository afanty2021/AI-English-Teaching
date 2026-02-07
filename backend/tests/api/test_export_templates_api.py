"""
导出模板API单元测试
测试模板API的端点和响应
"""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User, UserRole
from app.models.export_template import ExportTemplate, TemplateFormat


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def mock_teacher_user():
    """创建模拟教师用户"""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.username = "test_teacher"
    user.email = "teacher@test.com"
    user.role = UserRole.TEACHER
    user.is_active = True
    user.is_superuser = False
    user.organization_id = None
    user.organization = None
    return user


@pytest.fixture
def mock_student_user():
    """创建模拟学生用户"""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.username = "test_student"
    user.email = "student@test.com"
    user.role = UserRole.STUDENT
    user.is_active = True
    user.is_superuser = False
    user.organization_id = None
    user.organization = None
    return user


@pytest.fixture
def mock_admin_user():
    """创建模拟管理员用户"""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.username = "admin"
    user.email = "admin@test.com"
    user.role = UserRole.ADMIN
    user.is_active = True
    user.is_superuser = True
    user.organization_id = None
    user.organization = None
    return user


@pytest.fixture
def mock_template():
    """创建模拟模板"""
    template = MagicMock(spec=ExportTemplate)
    template.id = uuid.uuid4()
    template.name = "测试模板"
    template.description = "这是一个测试模板"
    template.format = TemplateFormat.WORD.value
    template.template_path = "/templates/test.docx"
    template.preview_path = "/previews/test.png"
    template.variables = [
        {"name": "title", "type": "text", "label": "标题", "required": True},
        {"name": "content", "type": "textarea", "label": "内容", "required": False},
    ]
    template.is_system = False
    template.is_default = False
    template.is_active = True
    template.usage_count = 0
    template.created_by = uuid.uuid4()
    template.organization_id = None
    return template


@pytest.mark.asyncio
async def test_list_templates_success(client, mock_teacher_user, mock_template):
    """测试列出模板 - 成功"""
    # 模拟依赖注入
    async def mock_get_db():
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_template]
        db.execute.return_value = mock_result
        yield db

    async def mock_get_current_user():
        return mock_teacher_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.get("/api/v1/export-templates")

    # 验证响应
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "测试模板"


@pytest.mark.asyncio
async def test_list_templates_with_filter(client, mock_teacher_user, mock_template):
    """测试带过滤条件列出模板"""
    async def mock_get_db():
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_template]
        db.execute.return_value = mock_result
        yield db

    async def mock_get_current_user():
        return mock_teacher_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.get("/api/v1/export-templates?format=word&is_system=false")

    # 验证响应
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_create_template_success(client, mock_teacher_user, mock_template):
    """测试创建模板 - 成功"""
    template_data = {
        "name": "新模板",
        "description": "新模板描述",
        "format": "word",
        "template_path": "/templates/new.docx",
        "variables": [{"name": "title", "type": "text", "label": "标题"}],
    }

    async def mock_get_db():
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = MagicMock()

        # 模拟返回创建的模板
        new_template = MagicMock(spec=ExportTemplate)
        new_template.id = uuid.uuid4()
        new_template.name = template_data["name"]
        new_template.description = template_data["description"]
        new_template.format = TemplateFormat.WORD.value
        new_template.template_path = template_data["template_path"]
        new_template.variables = template_data["variables"]
        new_template.is_system = False
        new_template.is_default = False
        new_template.is_active = True
        new_template.usage_count = 0
        new_template.created_by = mock_teacher_user.id
        new_template.organization_id = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = new_template
        db.execute.return_value = mock_result

        yield db

    async def mock_get_current_user():
        return mock_teacher_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.post("/api/v1/export-templates", json=template_data)

    # 验证响应
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "新模板"


@pytest.mark.asyncio
async def test_create_template_student_forbidden(client, mock_student_user):
    """测试学生创建模板 - 权限不足"""
    template_data = {
        "name": "新模板",
        "format": "word",
        "template_path": "/templates/new.docx",
    }

    async def mock_get_db():
        db = AsyncMock()
        yield db

    async def mock_get_current_user():
        return mock_student_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.post("/api/v1/export-templates", json=template_data)

    # 验证响应
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_get_template_success(client, mock_teacher_user, mock_template):
    """测试获取模板详情 - 成功"""
    async def mock_get_db():
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        db.execute.return_value = mock_result
        yield db

    async def mock_get_current_user():
        return mock_teacher_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.get(f"/api/v1/export-templates/{mock_template.id}")

    # 验证响应
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "测试模板"


@pytest.mark.asyncio
async def test_get_template_not_found(client, mock_teacher_user):
    """测试获取不存在的模板"""
    template_id = uuid.uuid4()

    async def mock_get_db():
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result
        yield db

    async def mock_get_current_user():
        return mock_teacher_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.get(f"/api/v1/export-templates/{template_id}")

    # 验证响应
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_default_template_success(client, mock_teacher_user, mock_template):
    """测试获取默认模板 - 成功"""
    async def mock_get_db():
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        db.execute.return_value = mock_result
        yield db

    async def mock_get_current_user():
        return mock_teacher_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.get("/api/v1/export-templates/default/word")

    # 验证响应
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_update_template_success(client, mock_teacher_user, mock_template):
    """测试更新模板 - 成功"""
    update_data = {"name": "更新后的名称"}

    async def mock_get_db():
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        db.execute.return_value = mock_result
        db.commit = AsyncMock()
        db.refresh = MagicMock()
        yield db

    async def mock_get_current_user():
        return mock_teacher_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.put(f"/api/v1/export-templates/{mock_template.id}", json=update_data)

    # 验证响应
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_delete_template_success(client, mock_teacher_user, mock_template):
    """测试删除模板 - 成功"""
    async def mock_get_db():
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        db.execute.return_value = mock_result
        db.commit = AsyncMock()
        yield db

    async def mock_get_current_user():
        return mock_teacher_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.delete(f"/api/v1/export-templates/{mock_template.id}")

    # 验证响应
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_system_template_forbidden(client, mock_teacher_user, mock_template):
    """测试删除系统模板 - 禁止"""
    mock_template.is_system = True

    async def mock_get_db():
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        db.execute.return_value = mock_result
        yield db

    async def mock_get_current_user():
        return mock_teacher_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.delete(f"/api/v1/export-templates/{mock_template.id}")

    # 验证响应
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_set_default_template_admin_success(client, mock_admin_user, mock_template):
    """测试设置默认模板 - 管理员成功"""
    async def mock_get_db():
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result
        db.commit = AsyncMock()
        db.refresh = MagicMock()
        yield db

    async def mock_get_current_user():
        return mock_admin_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.post(f"/api/v1/export-templates/{mock_template.id}/set-default")

    # 验证响应
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_set_default_template_teacher_forbidden(client, mock_teacher_user, mock_template):
    """测试设置默认模板 - 教师权限不足"""
    async def mock_get_db():
        db = AsyncMock()
        yield db

    async def mock_get_current_user():
        return mock_teacher_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.post(f"/api/v1/export-templates/{mock_template.id}/set-default")

    # 验证响应
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_validate_template_variables_valid(client, mock_teacher_user, mock_template):
    """测试验证模板变量 - 有效"""
    variables = {"title": "测试标题"}

    async def mock_get_db():
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        db.execute.return_value = mock_result
        yield db

    async def mock_get_current_user():
        return mock_teacher_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.post(
                f"/api/v1/export-templates/{mock_template.id}/validate",
                json=variables,
            )

    # 验证响应
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_valid"] is True


@pytest.mark.asyncio
async def test_clone_template_success(client, mock_teacher_user, mock_template):
    """测试克隆模板 - 成功"""
    new_name = "克隆的模板"

    async def mock_get_db():
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        db.execute.return_value = mock_result
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = MagicMock()
        yield db

    async def mock_get_current_user():
        return mock_teacher_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.post(
                f"/api/v1/export-templates/{mock_template.id}/clone?new_name={new_name}"
            )

    # 验证响应
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
async def test_increment_template_usage(client, mock_teacher_user, mock_template):
    """测试增加模板使用次数"""
    async def mock_get_db():
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        db.execute.return_value = mock_result
        db.commit = AsyncMock()
        yield db

    async def mock_get_current_user():
        return mock_teacher_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.post(f"/api/v1/export-templates/{mock_template.id}/usage")

    # 验证响应
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_template_preview_markdown_success(client, mock_teacher_user, mock_template):
    """测试模板预览 - Markdown 格式成功"""
    from datetime import datetime
    from app.models.lesson_plan import LessonPlan

    # 设置模板为 Markdown 格式
    mock_template.format = "markdown"

    # 创建模拟教案
    mock_lesson = MagicMock(spec=LessonPlan)
    mock_lesson.id = uuid.uuid4()
    mock_lesson.teacher_id = mock_teacher_user.id
    mock_lesson.title = "测试教案"
    mock_lesson.topic = "过去完成时"
    mock_lesson.level = "B1"
    mock_lesson.duration = 45
    mock_lesson.target_exam = "CET4"
    mock_lesson.objectives = {"language_knowledge": ["学习目标"]}
    mock_lesson.vocabulary = {"noun": [{"word": "test", "meaning_cn": "测试"}]}
    mock_lesson.grammar_points = []
    mock_lesson.teaching_structure = {}
    mock_lesson.leveled_materials = {}
    mock_lesson.exercises = {}
    mock_lesson.ppt_outline = []
    mock_lesson.resources = {}
    mock_lesson.teaching_notes = "教学反思"
    mock_lesson.is_public = False
    mock_lesson.is_shared = False
    mock_lesson.created_at = datetime.now()

    async def mock_get_db():
        db = AsyncMock()
        # 返回模板
        template_result = MagicMock()
        template_result.scalar_one_or_none.return_value = mock_template
        # 返回教案
        lesson_result = MagicMock()
        lesson_result.scalar_one_or_none.return_value = mock_lesson

        def execute_side_effect(query):
            if "lesson_plans" in str(query):
                return lesson_result
            return template_result

        db.execute.side_effect = execute_side_effect
        yield db

    async def mock_get_current_user():
        return mock_teacher_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.post(
                f"/api/v1/export-templates/{mock_template.id}/preview",
                params={"lesson_id": str(mock_lesson.id)}
            )

    # 验证响应
    assert response.status_code == status.HTTP_200_OK
    assert len(response.content) > 0
    assert response.headers.get("content-type") == "text/markdown; charset=utf-8"
    assert "preview_" in response.headers.get("x-preview-filename", "")


@pytest.mark.asyncio
async def test_template_preview_lesson_not_found(client, mock_teacher_user, mock_template):
    """测试模板预览 - 教案不存在"""
    lesson_id = uuid.uuid4()

    async def mock_get_db():
        db = AsyncMock()
        # 返回模板
        template_result = MagicMock()
        template_result.scalar_one_or_none.return_value = mock_template
        # 返回教案不存在
        lesson_result = MagicMock()
        lesson_result.scalar_one_or_none.return_value = None

        def execute_side_effect(query):
            if "lesson_plans" in str(query):
                return lesson_result
            return template_result

        db.execute.side_effect = execute_side_effect
        yield db

    async def mock_get_current_user():
        return mock_teacher_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.post(
                f"/api/v1/export-templates/{mock_template.id}/preview",
                params={"lesson_id": str(lesson_id)}
            )

    # 验证响应
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_template_preview_permission_denied(client, mock_teacher_user, mock_student_user, mock_template):
    """测试模板预览 - 权限不足"""
    from datetime import datetime
    from app.models.lesson_plan import LessonPlan

    # 创建另一个教师的教案
    other_teacher_id = uuid.uuid4()

    mock_lesson = MagicMock(spec=LessonPlan)
    mock_lesson.id = uuid.uuid4()
    mock_lesson.teacher_id = other_teacher_id  # 不是当前用户
    mock_lesson.title = "其他教师的教案"
    mock_lesson.is_public = False
    mock_lesson.is_shared = False
    mock_lesson.created_at = datetime.now()

    async def mock_get_db():
        db = AsyncMock()
        # 返回模板
        template_result = MagicMock()
        template_result.scalar_one_or_none.return_value = mock_template
        # 返回教案
        lesson_result = MagicMock()
        lesson_result.scalar_one_or_none.return_value = mock_lesson

        def execute_side_effect(query):
            if "lesson_plans" in str(query):
                return lesson_result
            return template_result

        db.execute.side_effect = execute_side_effect
        yield db

    async def mock_get_current_user():
        return mock_student_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.post(
                f"/api/v1/export-templates/{mock_template.id}/preview",
                params={"lesson_id": str(mock_lesson.id)}
            )

    # 验证响应
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_template_preview_unsupported_format(client, mock_teacher_user, mock_template):
    """测试模板预览 - 不支持的格式"""
    mock_template.format = "html"  # 不支持的格式

    lesson_id = uuid.uuid4()

    async def mock_get_db():
        db = AsyncMock()
        template_result = MagicMock()
        template_result.scalar_one_or_none.return_value = mock_template
        db.execute.return_value = template_result
        yield db

    async def mock_get_current_user():
        return mock_teacher_user

    from unittest.mock import patch

    with patch("app.api.v1.export_templates.get_db", mock_get_db):
        with patch("app.api.v1.export_templates.get_current_user", mock_get_current_user):
            response = client.post(
                f"/api/v1/export-templates/{mock_template.id}/preview",
                params={"lesson_id": str(lesson_id)}
            )

    # 验证响应
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "不支持的预览格式" in response.json()["detail"]
