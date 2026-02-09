"""
导出模板服务单元测试
测试模板服务的CRUD操作和业务逻辑
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.models.export_template import ExportTemplate, TemplateFormat
from app.services.template_service import (
    ExportTemplateService,
    TemplateCreateRequest,
    TemplateUpdateRequest,
)


@pytest.fixture
def template_service():
    """创建模板服务实例"""
    return ExportTemplateService()


@pytest.fixture
def mock_template():
    """创建模拟模板对象"""
    template = MagicMock(spec=ExportTemplate)
    template.id = uuid.uuid4()
    template.name = "测试模板"
    template.description = "这是一个测试模板"
    template.format = TemplateFormat.WORD.value
    template.template_path = "templates/test.docx"  # 使用相对路径
    template.preview_path = "previews/test.png"  # 使用相对路径
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
    template.created_at = datetime.now()
    template.updated_at = datetime.now()
    return template


@pytest.mark.asyncio
async def test_create_template(template_service, mock_db):
    """测试创建模板"""
    # 使用 Mock 而不是真实的 SQLAlchemy 模型
    mock_template_result = MagicMock()
    mock_template_result.id = uuid.uuid4()
    mock_template_result.name = "新模板"
    mock_template_result.description = "新模板描述"
    mock_template_result.format = TemplateFormat.WORD.value
    mock_template_result.created_by = uuid.uuid4()

    # 模拟 db.add 和 commit
    async def mock_commit():
        pass

    async def mock_refresh(obj):
        pass

    mock_db.commit = mock_commit
    mock_db.refresh = mock_refresh

    # 使用 patch 来避免 SQLAlchemy 模型初始化问题
    with patch("app.services.template_service.ExportTemplate") as MockExportTemplate:
        MockExportTemplate.return_value = mock_template_result

        template_data = {
            "name": "新模板",
            "description": "新模板描述",
            "format": "word",
            "template_path": "templates/new.docx",  # 使用相对路径
            "variables": [{"name": "title", "type": "text", "label": "标题"}],
            "is_default": False,
        }
        created_by = uuid.uuid4()

        # 执行创建
        result = await template_service.create_template(template_data, created_by, mock_db)

        # 验证
        assert result.name == "新模板"
        assert result.description == "新模板描述"
        assert result.format == TemplateFormat.WORD.value


@pytest.mark.asyncio
async def test_create_template_invalid_format(template_service, mock_db):
    """测试创建模板时使用无效格式"""
    template_data = {
        "name": "新模板",
        "format": "invalid_format",
        "template_path": "/templates/new.docx",
    }
    created_by = uuid.uuid4()

    # 执行并验证异常
    with pytest.raises(Exception) as exc_info:
        await template_service.create_template(template_data, created_by, mock_db)

    assert "无效的格式" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_list_templates(template_service, mock_db, mock_template):
    """测试列出模板"""
    # 设置模拟查询结果
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_template]
    mock_db.execute.return_value = mock_result

    # 执行查询
    result = await template_service.list_templates(db=mock_db)

    # 验证
    assert len(result) == 1
    assert result[0].name == "测试模板"


@pytest.mark.asyncio
async def test_list_templates_with_filter(template_service, mock_db):
    """测试带过滤条件的模板列表"""
    # 设置模拟查询结果
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    # 执行查询（带格式过滤）
    result = await template_service.list_templates(
        format_filter="word", is_system=False, db=mock_db
    )

    # 验证
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_get_template(template_service, mock_db, mock_template):
    """测试获取模板详情"""
    # 设置模拟查询结果
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_template
    mock_db.execute.return_value = mock_result

    # 执行查询
    result = await template_service.get_template(mock_template.id, mock_db)

    # 验证
    assert result.id == mock_template.id
    assert result.name == "测试模板"


@pytest.mark.asyncio
async def test_get_template_not_found(template_service, mock_db):
    """测试获取不存在的模板"""
    # 设置模拟查询结果为None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    # 执行并验证异常
    with pytest.raises(Exception) as exc_info:
        await template_service.get_template(uuid.uuid4(), mock_db)

    assert "模板不存在" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_template(template_service, mock_db, mock_template):
    """测试更新模板"""
    # 设置模拟查询结果
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_template
    mock_db.execute.return_value = mock_result

    # 模拟 commit 和 refresh
    async def mock_commit():
        pass

    async def mock_refresh(obj):
        pass

    mock_db.commit = mock_commit
    mock_db.refresh = mock_refresh

    update_data = {
        "name": "更新后的名称",
        "description": "更新后的描述",
    }

    # 执行更新
    result = await template_service.update_template(mock_template.id, update_data, mock_db)

    # 验证
    assert result.name == "更新后的名称"
    assert result.description == "更新后的描述"


@pytest.mark.asyncio
async def test_update_system_template_restricted(template_service, mock_db, mock_template):
    """测试更新系统模板时的字段限制"""
    # 设置为系统模板
    mock_template.is_system = True

    # 设置模拟查询结果
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_template
    mock_db.execute.return_value = mock_result

    # 模拟 commit 和 refresh
    async def mock_commit():
        pass

    async def mock_refresh(obj):
        pass

    mock_db.commit = mock_commit
    mock_db.refresh = mock_refresh

    update_data = {
        "name": "不应该更新",
        "is_active": True,  # 只有这个应该被更新
        "created_by": uuid.uuid4(),  # 这个不应该被更新
    }

    # 执行更新
    result = await template_service.update_template(mock_template.id, update_data, mock_db)

    # 验证
    assert result.is_active == True  # 这个应该被更新
    # 系统模板的 name 不应该被更新
    assert result.name != "不应该更新"


@pytest.mark.asyncio
async def test_delete_template(template_service, mock_db, mock_template):
    """测试删除模板（软删除）"""
    # 设置模拟查询结果
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_template
    mock_db.execute.return_value = mock_result

    # 执行删除
    result = await template_service.delete_template(mock_template.id, mock_db)

    # 验证
    assert result is True
    assert mock_template.is_active is False


@pytest.mark.asyncio
async def test_delete_system_template_forbidden(template_service, mock_db, mock_template):
    """测试删除系统模板被禁止"""
    # 设置为系统模板
    mock_template.is_system = True

    # 设置模拟查询结果
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_template
    mock_db.execute.return_value = mock_result

    # 执行并验证异常
    with pytest.raises(Exception) as exc_info:
        await template_service.delete_template(mock_template.id, mock_db)

    assert "系统模板不能删除" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_increment_usage(template_service, mock_db, mock_template):
    """测试增加使用次数"""
    # 设置模拟查询结果
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_template
    mock_db.execute.return_value = mock_result

    # 初始使用次数
    initial_count = mock_template.usage_count

    # 执行增加
    await template_service.increment_usage(mock_template.id, mock_db)

    # 验证
    assert mock_template.usage_count == initial_count + 1


@pytest.mark.asyncio
async def test_get_default_template(template_service, mock_db, mock_template):
    """测试获取默认模板"""
    # 设置模拟查询结果
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_template
    mock_db.execute.return_value = mock_result

    # 执行查询
    result = await template_service.get_default_template("word", mock_db)

    # 验证
    assert result is not None
    assert result.format == TemplateFormat.WORD.value


@pytest.mark.asyncio
async def test_set_default_template(template_service, mock_db, mock_template):
    """测试设置默认模板"""
    # 设置模拟查询结果
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_template
    # 模拟返回同格式的其他默认模板
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    # 模拟 commit 和 refresh
    async def mock_commit():
        pass

    async def mock_refresh(obj):
        pass

    mock_db.commit = mock_commit
    mock_db.refresh = mock_refresh

    # 执行设置
    result = await template_service.set_default_template(mock_template.id, mock_db)

    # 验证
    assert result.is_default is True


@pytest.mark.asyncio
async def test_validate_template_variables_valid(template_service, mock_db, mock_template):
    """测试验证模板变量 - 有效"""
    # 设置模拟查询结果
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_template
    mock_db.execute.return_value = mock_result

    # 提供所有必需变量
    provided_vars = {"title": "测试标题"}

    # 执行验证
    is_valid, missing = await template_service.validate_template_variables(
        mock_template.id, provided_vars, mock_db
    )

    # 验证
    assert is_valid is True
    assert len(missing) == 0


@pytest.mark.asyncio
async def test_validate_template_variables_missing_required(
    template_service, mock_db, mock_template
):
    """测试验证模板变量 - 缺少必需变量"""
    # 设置模拟查询结果
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_template
    mock_db.execute.return_value = mock_result

    # 不提供必需变量
    provided_vars = {}

    # 执行验证
    is_valid, missing = await template_service.validate_template_variables(
        mock_template.id, provided_vars, mock_db
    )

    # 验证
    assert is_valid is False
    assert "title" in missing


@pytest.mark.skip("SQLAlchemy mock issue - requires actual database model")
@pytest.mark.asyncio
async def test_clone_template(template_service, mock_db, mock_template):
    """测试克隆模板"""
    # 创建一个新模板的 Mock
    new_template_mock = MagicMock(spec=ExportTemplate)
    new_template_mock.id = uuid.uuid4()
    new_template_mock.name = "克隆的模板"
    new_template_mock.is_system = False
    new_template_mock.is_default = False
    new_template_mock.created_by = uuid.uuid4()

    # 设置模拟查询结果
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_template
    mock_db.execute.return_value = mock_result

    # 模拟 commit 和 refresh
    async def mock_commit():
        pass

    async def mock_refresh(obj):
        # 设置新模板的属性
        if hasattr(obj, "id"):
            obj.id = new_template_mock.id
        if hasattr(obj, "name"):
            obj.name = new_template_mock.name
        if hasattr(obj, "is_system"):
            obj.is_system = new_template_mock.is_system
        if hasattr(obj, "is_default"):
            obj.is_default = new_template_mock.is_default
        if hasattr(obj, "created_by"):
            obj.created_by = new_template_mock.created_by

    mock_db.commit = mock_commit
    mock_db.refresh = mock_refresh

    # 使用 patch 来避免 SQLAlchemy 模型初始化问题
    with patch("app.services.template_service.ExportTemplate") as MockExportTemplate:
        MockExportTemplate.return_value = new_template_mock

        new_name = "克隆的模板"
        created_by = uuid.uuid4()

        # 执行克隆
        new_template = await template_service.clone_template(
            mock_template.id, new_name, created_by, mock_db
        )

        # 验证
        assert new_template.name == new_name
        assert new_template.is_system is False
        assert new_template.is_default is False
        assert new_template.created_by == created_by


@pytest.fixture
def mock_db():
    """创建模拟数据库会话"""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db
