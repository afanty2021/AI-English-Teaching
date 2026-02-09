"""
导出模板服务 - AI英语教学系统
提供教案导出模板的CRUD操作和管理功能
"""
import os
import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.export_template import ExportTemplate, TemplateFormat
from app.utils.path_validation import (
    validate_template_path,
    PathValidationError,
)

# 获取允许的模板基础目录
_TEMPLATE_BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "templates"
)


class TemplateVariable(BaseModel):
    """模板变量定义"""

    model_config = ConfigDict(from_attributes=True)

    name: str
    type: str  # text, textarea, number, date, select, checkbox
    label: str
    default: Any = None
    required: bool = False
    options: List[str] = []  # for select type
    description: Optional[str] = None


class TemplateCreateRequest(BaseModel):
    """创建模板请求"""

    name: str
    description: Optional[str] = None
    format: str  # word, pdf, pptx, markdown
    template_path: str
    preview_path: Optional[str] = None
    variables: List[Dict[str, Any]] = []
    is_default: bool = False


class TemplateUpdateRequest(BaseModel):
    """更新模板请求"""

    name: Optional[str] = None
    description: Optional[str] = None
    template_path: Optional[str] = None
    preview_path: Optional[str] = None
    variables: Optional[List[Dict[str, Any]]] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class TemplateResponse(BaseModel):
    """模板响应"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str]
    format: str
    template_path: str
    preview_path: Optional[str]
    variables: List[Dict[str, Any]]
    is_system: bool
    is_default: bool
    is_active: bool
    usage_count: int
    created_by: Optional[uuid.UUID]
    organization_id: Optional[uuid.UUID]


class ExportTemplateService:
    """导出模板服务"""

    async def create_template(
        self,
        template_data: Dict[str, Any],
        created_by: uuid.UUID,
        db: AsyncSession,
    ) -> ExportTemplate:
        """
        创建新模板

        Args:
            template_data: 模板数据
            created_by: 创建者ID
            db: 数据库会话

        Returns:
            创建的模板对象

        Raises:
            HTTPException: 格式无效时
        """
        # 验证格式
        try:
            template_format = TemplateFormat(template_data["format"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的格式: {template_data.get('format')}",
            )

        # 验证模板路径安全性（防止路径遍历攻击）
        template_path_raw = template_data.get("template_path", "")
        if template_path_raw:
            try:
                validated_path = validate_template_path(
                    template_path_raw,
                    allowed_base_dir=_TEMPLATE_BASE_DIR
                )
                template_path = validated_path
            except PathValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的模板路径: {str(e)}",
                )
        else:
            template_path = ""

        # 验证预览路径安全性（可选）
        preview_path_raw = template_data.get("preview_path")
        if preview_path_raw:
            try:
                preview_path = validate_template_path(
                    preview_path_raw,
                    allowed_base_dir=_TEMPLATE_BASE_DIR
                )
            except PathValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的预览路径: {str(e)}",
                )
        else:
            preview_path = None

        template = ExportTemplate(
            name=template_data["name"],
            description=template_data.get("description", ""),
            format=template_format.value,
            template_path=template_path,
            preview_path=preview_path,
            variables=template_data.get("variables", []),
            created_by=created_by,
            is_system=template_data.get("is_system", False),
            is_default=template_data.get("is_default", False),
            organization_id=template_data.get("organization_id"),
        )

        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    async def list_templates(
        self,
        format_filter: Optional[str] = None,
        is_system: Optional[bool] = None,
        is_active: Optional[bool] = None,
        organization_id: Optional[uuid.UUID] = None,
        db: Optional[AsyncSession] = None,
    ) -> List[ExportTemplate]:
        """
        列出模板

        Args:
            format_filter: 按格式过滤
            is_system: 是否为系统模板
            is_active: 是否激活
            organization_id: 组织ID（可选）
            db: 数据库会话

        Returns:
            模板列表
        """
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="数据库会话未提供",
            )

        query = select(ExportTemplate)

        if format_filter:
            query = query.where(ExportTemplate.format == format_filter)
        if is_system is not None:
            query = query.where(ExportTemplate.is_system == is_system)
        if is_active is not None:
            query = query.where(ExportTemplate.is_active == is_active)

        # 组织过滤：系统模板或无组织限制或属于该组织
        if organization_id:
            query = query.where(
                (ExportTemplate.is_system == True)
                | (ExportTemplate.organization_id == None)
                | (ExportTemplate.organization_id == organization_id)
            )

        query = query.order_by(ExportTemplate.usage_count.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_template(
        self,
        template_id: uuid.UUID,
        db: AsyncSession,
    ) -> ExportTemplate:
        """
        获取模板详情

        Args:
            template_id: 模板ID
            db: 数据库会话

        Returns:
            模板对象

        Raises:
            HTTPException: 模板不存在
        """
        query = select(ExportTemplate).where(ExportTemplate.id == template_id)
        result = await db.execute(query)

        template = result.scalar_one_or_none()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模板不存在",
            )

        return template

    async def get_default_template(
        self,
        format_value: str,
        db: AsyncSession,
    ) -> Optional[ExportTemplate]:
        """
        获取指定格式的默认模板

        Args:
            format_value: 模板格式
            db: 数据库会话

        Returns:
            默认模板对象，如果不存在则返回None
        """
        query = (
            select(ExportTemplate)
            .where(ExportTemplate.format == format_value)
            .where(ExportTemplate.is_default == True)
            .where(ExportTemplate.is_active == True)
        )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update_template(
        self,
        template_id: uuid.UUID,
        update_data: Dict[str, Any],
        db: AsyncSession,
    ) -> ExportTemplate:
        """
        更新模板

        Args:
            template_id: 模板ID
            update_data: 更新数据
            db: 数据库会话

        Returns:
            更新后的模板对象

        Raises:
            HTTPException: 模板不存在或系统模板不允许修改
        """
        template = await self.get_template(template_id, db)

        # 系统模板只能修改部分字段
        protected_fields = {"id", "created_at", "created_by", "is_system"}
        if template.is_system:
            # 系统模板只允许更新 is_active 和 is_default
            allowed_updates = {"is_active", "is_default"}
            for key in list(update_data.keys()):
                if key not in allowed_updates:
                    update_data.pop(key)
        else:
            # 非系统模板可以更新更多字段
            for key in list(update_data.keys()):
                if key in protected_fields:
                    update_data.pop(key)

        # 验证模板路径（如果正在更新）
        if "template_path" in update_data and update_data["template_path"]:
            try:
                update_data["template_path"] = validate_template_path(
                    update_data["template_path"],
                    allowed_base_dir=_TEMPLATE_BASE_DIR
                )
            except PathValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的模板路径: {str(e)}",
                )

        # 验证预览路径（如果正在更新）
        if "preview_path" in update_data and update_data["preview_path"]:
            try:
                update_data["preview_path"] = validate_template_path(
                    update_data["preview_path"],
                    allowed_base_dir=_TEMPLATE_BASE_DIR
                )
            except PathValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的预览路径: {str(e)}",
                )

        for key, value in update_data.items():
            if hasattr(template, key):
                setattr(template, key, value)

        await db.commit()
        await db.refresh(template)
        return template

    async def delete_template(
        self,
        template_id: uuid.UUID,
        db: AsyncSession,
    ) -> bool:
        """
        删除模板（软删除）

        Args:
            template_id: 模板ID
            db: 数据库会话

        Returns:
            删除成功

        Raises:
            HTTPException: 模板不存在或系统模板不能删除
        """
        template = await self.get_template(template_id, db)

        if template.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统模板不能删除",
            )

        template.is_active = False
        await db.commit()
        return True

    async def increment_usage(
        self,
        template_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        """
        增加模板使用次数

        Args:
            template_id: 模板ID
            db: 数据库会话
        """
        template = await self.get_template(template_id, db)
        template.usage_count += 1
        await db.commit()

    async def set_default_template(
        self,
        template_id: uuid.UUID,
        db: AsyncSession,
    ) -> ExportTemplate:
        """
        设置默认模板（同一格式只能有一个默认模板）

        Args:
            template_id: 模板ID
            db: 数据库会话

        Returns:
            更新后的模板对象
        """
        template = await self.get_template(template_id, db)

        # 取消同格式的其他默认模板
        query = select(ExportTemplate).where(
            ExportTemplate.format == template.format,
            ExportTemplate.is_default == True,
            ExportTemplate.id != template_id,
        )
        result = await db.execute(query)
        other_defaults = result.scalars().all()

        for other in other_defaults:
            other.is_default = False

        # 设置新默认模板
        template.is_default = True

        await db.commit()
        await db.refresh(template)
        return template

    async def validate_template_variables(
        self,
        template_id: uuid.UUID,
        provided_variables: Dict[str, Any],
        db: AsyncSession,
    ) -> tuple[bool, List[str]]:
        """
        验证提供的变量是否满足模板要求

        Args:
            template_id: 模板ID
            provided_variables: 提供的变量字典
            db: 数据库会话

        Returns:
            (是否有效, 缺失的必需变量列表)
        """
        template = await self.get_template(template_id, db)

        missing_vars = []
        for var_def in template.variables:
            if isinstance(var_def, dict):
                var_name = var_def.get("name")
                required = var_def.get("required", False)

                if required and var_name not in provided_variables:
                    missing_vars.append(var_name)

        return len(missing_vars) == 0, missing_vars

    async def clone_template(
        self,
        template_id: uuid.UUID,
        new_name: str,
        created_by: uuid.UUID,
        db: AsyncSession,
    ) -> ExportTemplate:
        """
        克隆模板

        Args:
            template_id: 原模板ID
            new_name: 新模板名称
            created_by: 创建者ID
            db: 数据库会话

        Returns:
            新模板对象
        """
        original = await self.get_template(template_id, db)

        new_template = ExportTemplate(
            name=new_name,
            description=original.description,
            format=original.format,
            template_path=original.template_path,
            preview_path=original.preview_path,
            variables=original.variables.copy(),
            created_by=created_by,
            is_system=False,  # 克隆的模板不是系统模板
            is_default=False,
            organization_id=original.organization_id,
        )

        db.add(new_template)
        await db.commit()
        await db.refresh(new_template)
        return new_template
