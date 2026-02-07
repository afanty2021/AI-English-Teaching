"""
导出模板模型测试
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import MagicMock

from app.models.export_template import ExportTemplate


class TestExportTemplate:
    """导出模板模型测试"""

    def test_template_creation(self):
        """测试模板创建"""
        template = ExportTemplate(
            id=uuid.uuid4(),
            name="标准教案模板",
            description="用于导出标准格式的教案",
            format="word",
            template_path="templates/standard.docx",
            variables=[{"name": "title", "type": "text", "required": True}]
        )

        assert template.name == "标准教案模板"
        assert template.format == "word"
        assert template.template_path == "templates/standard.docx"
        assert template.is_system is False
        assert template.is_active is True

    def test_template_default_values(self):
        """测试模板默认值"""
        template = ExportTemplate(
            name="测试模板",
            format="pdf",
            template_path="templates/test.pdf"
        )

        assert template.is_system is False
        assert template.is_active is True
        assert template.is_default is False
        assert template.usage_count == 0
        assert template.variables == []
        assert template.created_by is None
        assert template.organization_id is None
        assert template.preview_path is None

    def test_is_custom_property(self):
        """测试 is_custom 属性"""
        custom_template = ExportTemplate(
            name="自定义模板",
            format="word",
            template_path="templates/custom.docx",
            is_system=False
        )
        assert custom_template.is_custom is True

        system_template = ExportTemplate(
            name="系统模板",
            format="word",
            template_path="templates/system.docx",
            is_system=True
        )
        assert system_template.is_custom is False

    def test_word_format_property(self):
        """测试 word_format 属性"""
        word_template = ExportTemplate(
            name="Word模板",
            format="word",
            template_path="templates/doc.docx"
        )
        assert word_template.word_format is True
        assert word_template.pdf_format is False

    def test_pdf_format_property(self):
        """测试 pdf_format 属性"""
        pdf_template = ExportTemplate(
            name="PDF模板",
            format="pdf",
            template_path="templates/doc.pdf"
        )
        assert pdf_template.pdf_format is True
        assert pdf_template.word_format is False

    def test_pptx_format_property(self):
        """测试 pptx_format 属性"""
        pptx_template = ExportTemplate(
            name="PPTX模板",
            format="pptx",
            template_path="templates/doc.pptx"
        )
        assert pptx_template.pptx_format is True
        assert pdf_template.word_format is False

    def test_markdown_format_property(self):
        """测试 markdown_format 属性"""
        md_template = ExportTemplate(
            name="Markdown模板",
            format="markdown",
            template_path="templates/doc.md"
        )
        assert md_template.markdown_format is True
        assert md_template.word_format is False

    def test_repr(self):
        """测试 __repr__ 方法"""
        template_id = uuid.uuid4()
        template = ExportTemplate(
            id=template_id,
            name="测试模板",
            format="word",
            template_path="templates/test.docx",
            is_system=False
        )

        repr_str = repr(template)
        assert "ExportTemplate" in repr_str
        assert str(template_id) in repr_str
        assert "测试模板" in repr_str
        assert "word" in repr_str


class TestExportTemplateVariables:
    """模板变量测试"""

    def test_variable_names_property(self):
        """测试 variable_names 属性"""
        variables = [
            {"name": "title", "type": "text"},
            {"name": "description", "type": "textarea"},
            {"name": "level", "type": "select", "options": ["A1", "A2", "B1"]}
        ]
        template = ExportTemplate(
            name="测试模板",
            format="word",
            template_path="templates/test.docx",
            variables=variables
        )

        names = template.variable_names
        assert "title" in names
        assert "description" in names
        assert "level" in names

    def test_get_variable(self):
        """测试 get_variable 方法"""
        variables = [
            {"name": "title", "type": "text", "label": "标题"},
            {"name": "level", "type": "select", "label": "等级"}
        ]
        template = ExportTemplate(
            name="测试模板",
            format="word",
            template_path="templates/test.docx",
            variables=variables
        )

        title_var = template.get_variable("title")
        assert title_var is not None
        assert title_var["type"] == "text"
        assert title_var["label"] == "标题"

        nonexistent = template.get_variable("nonexistent")
        assert nonexistent is None

    def test_increment_usage(self):
        """测试 increment_usage 方法"""
        template = ExportTemplate(
            name="测试模板",
            format="word",
            template_path="templates/test.docx"
        )

        assert template.usage_count == 0

        template.increment_usage()
        assert template.usage_count == 1

        template.increment_usage()
        assert template.usage_count == 2


class TestExportTemplateRelationships:
    """模板关系测试"""

    def test_export_tasks_relationship(self):
        """测试与导出任务的关系"""
        template = ExportTemplate(
            name="测试模板",
            format="word",
            template_path="templates/test.docx"
        )

        # 验证关系字段存在
        assert hasattr(template, 'export_tasks')
        assert hasattr(template, 'creator')
        assert hasattr(template, 'organization')

    def test_creator_relationship(self):
        """测试与创建者的关系"""
        user_id = uuid.uuid4()
        template = ExportTemplate(
            name="测试模板",
            format="word",
            template_path="templates/test.docx",
            created_by=user_id
        )

        assert template.created_by == user_id

    def test_organization_relationship(self):
        """测试与组织的关系"""
        org_id = uuid.uuid4()
        template = ExportTemplate(
            name="测试模板",
            format="word",
            template_path="templates/test.docx",
            organization_id=org_id
        )

        assert template.organization_id == org_id
