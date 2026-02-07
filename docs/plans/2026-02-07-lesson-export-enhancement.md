# 教案导出功能完善实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 完善教案导出功能，实现实际文档生成、模板管理、WebSocket实时进度推送

**架构:** 前后端分离 + 异步任务处理 + WebSocket实时推送 + Jinja2模板引擎

**技术栈:** FastAPI + SQLAlchemy + WebSocket + Jinja2 + python-docx/weasyprint/python-pptx

---

## 概述

本实施计划旨在完善现有的教案导出功能，从目前的"仅创建任务"状态升级为"完整文档生成"系统。

### 现状问题

1. **后端**: 只创建任务对象，没有实际生成文档
2. **存储**: 使用内存字典 `EXPORT_TASKS = {}`，无持久化
3. **进度**: 前端轮询获取进度，无实时推送
4. **模板**: 硬编码模板，无法自定义
5. **格式**: 仅支持API定义，无生成逻辑

### 改进目标

1. ✅ 实现真实的Word/PDF/PPT文档生成
2. ✅ 完整的模板管理系统
3. ✅ WebSocket实时进度推送
4. ✅ 持久化任务存储和文件管理
5. ✅ 优雅的错误处理和重试机制

---

## Phase 1: 数据库和基础设施 (2天)

### Task 1: 创建数据库模型

**文件:**
- Create: `backend/app/models/export_task.py`
- Create: `backend/app/models/export_template.py`
- Create: `backend/alembic/versions/20260207_add_export_system.py`

**Step 1: 创建导出任务模型**

```python
# backend/app/models/export_task.py

from sqlalchemy import Column, String, Integer, Text, BigInteger, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExportFormat(str, Enum):
    WORD = "word"
    PDF = "pdf"
    PPTX = "pptx"
    MARKDOWN = "markdown"

class ExportTask(Base):
    __tablename__ = "export_tasks"

    id = Column(UUID, primary_key=True)
    lesson_id = Column(UUID, ForeignKey("lesson_plans.id"), nullable=False)
    template_id = Column(UUID, ForeignKey("export_templates.id"), nullable=True)
    created_by = Column(UUID, ForeignKey("users.id"), nullable=False)

    format = Column(String(20), nullable=False)
    status = Column(String(20), default=TaskStatus.PENDING)
    progress = Column(Integer, default=0)

    options = Column(JSON, nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    download_url = Column(String(500), nullable=True)

    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)

    created_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    lesson = relationship("LessonPlan", backref="export_tasks")
    template = relationship("ExportTemplate", backref="export_tasks")
    creator = relationship("User", backref="export_tasks")
```

**Step 2: 创建导出模板模型**

```python
# backend/app/models/export_template.py

class ExportTemplate(Base):
    __tablename__ = "export_templates"

    id = Column(UUID, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    format = Column(String(20), nullable=False)

    template_path = Column(String(500), nullable=False)
    preview_path = Column(String(500), nullable=True)

    variables = Column(JSON, nullable=False, default=list)
    is_system = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    created_by = Column(UUID, ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID, ForeignKey("organizations.id"), nullable=True)

    usage_count = Column(Integer, default=0)

    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
```

**Step 3: 创建数据库迁移**

```bash
cd backend
alembic revision -m "add export system"
```

**Step 4: 编写迁移内容**

```python
# backend/alembic/versions/20260207_add_export_system.py

def upgrade():
    op.create_table(
        'export_templates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        # ... (完整表结构)
    )
    op.create_table(
        'export_tasks',
        sa.Column('id', sa.UUID(), nullable=False),
        # ... (完整表结构)
    )
    # 添加索引

def downgrade():
    op.drop_table('export_tasks')
    op.drop_table('export_templates')
```

**Step 5: 运行迁移**

```bash
cd backend
alembic upgrade head
```

**Step 6: 提交**

```bash
git add backend/app/models/ backend/alembic/versions/
git commit -m "feat(export): add export task and template models"
```

---

### Task 2: 创建文件存储基础设施

**文件:**
- Create: `backend/app/services/file_storage_service.py`
- Create: `backend/core/config.py` (add export settings)

**Step 1: 添加配置**

```python
# backend/core/config.py

class Settings(BaseSettings):
    # Export Settings
    EXPORT_DIR: Path = Path("exports")
    EXPORT_MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    EXPORT_FILE_RETENTION_DAYS: int = 30
    EXPORT_TASK_RETENTION_DAYS: int = 7

    MAX_CONCURRENT_EXPORTS: int = 5
    EXPORT_TASK_TIMEOUT: int = 300  # 5 minutes
```

**Step 2: 实现文件存储服务**

```python
# backend/app/services/file_storage_service.py

import os
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import HTTPException

class FileStorageService:
    def __init__(self, export_dir: Path):
        self.export_dir = export_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(
        self,
        content: bytes,
        filename: str,
        format: ExportFormat
    ) -> tuple[str, int]:
        """保存文件并返回(路径, 大小)"""
        # 验证大小
        if len(content) > settings.EXPORT_MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"文件大小超过限制 {settings.EXPORT_MAX_FILE_SIZE/1024/1024}MB"
            )

        # 生成唯一文件名
        ext = self._get_extension(format)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_name = f"{timestamp}_{uuid.uuid4().hex[:8]}_{filename}"
        file_path = self.export_dir / unique_name

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(content)

        return str(file_path), len(content)

    async def get_file(self, file_path: str) -> bytes:
        """读取文件"""
        path = Path(file_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        with open(path, "rb") as f:
            return f.read()

    async def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False

    def _get_extension(self, format: ExportFormat) -> str:
        return {
            ExportFormat.WORD: "docx",
            ExportFormat.PDF: "pdf",
            ExportFormat.PPTX: "pptx",
            ExportFormat.MARKDOWN: "md"
        }[format]
```

**Step 3: 添加下载端点**

```python
# backend/app/api/v1/lesson_export.py

@router.get("/exports/{filename}")
async def download_export_file(filename: str):
    file_path = settings.EXPORT_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=filename
    )
```

**Step 4: 编写测试**

```python
# tests/services/test_file_storage_service.py

import pytest
from app.services.file_storage_service import FileStorageService
from pathlib import Path

@pytest.mark.asyncio
async def test_save_file():
    service = FileStorageService(Path("/tmp/exports"))
    content = b"test content"
    path, size = await service.save_file(content, "test.docx", ExportFormat.WORD)

    assert Path(path).exists()
    assert size == len(content)

@pytest.mark.asyncio
async def test_file_size_limit():
    service = FileStorageService(Path("/tmp/exports"))
    large_content = b"x" * (51 * 1024 * 1024)

    with pytest.raises(HTTPException) as exc_info:
        await service.save_file(large_content, "test.docx", ExportFormat.WORD)

    assert exc_info.value.status_code == 413
```

**Step 5: 提交**

```bash
git add backend/app/services/file_storage_service.py backend/core/config.py tests/services/test_file_storage_service.py
git commit -m "feat(export): add file storage service with size limit"
```

---

## Phase 2: 文档生成服务 (3天)

### Task 3: 实现内容渲染服务

**文件:**
- Create: `backend/app/services/content_renderer.py`
- Create: `tests/services/test_content_renderer.py`

**Step 1: 定义内容结构**

```python
# backend/app/services/content_renderer.py

from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import LessonPlan

class ContentRenderer:
    async def render(
        self,
        lesson: LessonPlan,
        sections: List[str]
    ) -> Dict[str, Any]:
        """渲染教案为结构化数据"""
        content = {}

        if "overview" in sections:
            content["overview"] = await self._render_overview(lesson)

        if "objectives" in sections:
            content["objectives"] = await self._render_objectives(lesson)

        if "vocabulary" in sections:
            content["vocabulary"] = await self._render_vocabulary(lesson)

        # ... 其他章节

        return content

    async def _render_overview(self, lesson: LessonPlan) -> Dict[str, Any]:
        return {
            "title": lesson.title,
            "description": lesson.description,
            "level": lesson.level,
            "duration": lesson.duration_minutes
        }

    async def _render_objectives(self, lesson: LessonPlan) -> List[Dict[str, str]]:
        return [
            {"text": obj.text, "priority": obj.priority}
            for obj in lesson.learning_objectives
        ]

    async def _render_vocabulary(self, lesson: LessonPlan) -> List[Dict[str, str]]:
        return [
            {
                "word": vocab.word,
                "translation": vocab.translation,
                "phonetic": vocab.phonetic
            }
            for vocab in lesson.vocabulary_list
        ]
```

**Step 2: 编写测试**

```python
# tests/services/test_content_renderer.py

@pytest.mark.asyncio
async def test_render_content():
    renderer = ContentRenderer()
    lesson = create_mock_lesson()

    content = await renderer.render(
        lesson,
        ["overview", "objectives", "vocabulary"]
    )

    assert "overview" in content
    assert content["vocabulary"][0]["word"] == "apple"
```

**Step 3: 提交**

```bash
git add backend/app/services/content_renderer.py tests/services/test_content_renderer.py
git commit -m "feat(export): add content renderer service"
```

---

### Task 4: 实现 Word 文档生成

**文件:**
- Create: `backend/app/services/document_generators/word_generator.py`
- Create: `backend/app/services/document_generators/__init__.py`
- Create: `tests/services/test_word_generator.py`

**Step 1: 安装依赖**

```bash
pip install python-docx
```

**Step 2: 实现 Word 生成器**

```python
# backend/app/services/document_generators/word_generator.py

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

class WordDocumentGenerator:
    def generate(self, content: Dict[str, Any], template_vars: Dict[str, Any]) -> bytes:
        """生成Word文档"""
        doc = Document()

        # 标题
        title = content.get("overview", {}).get("title", "教案")
        doc.add_heading(title, 0)

        # 概述
        if "overview" in content:
            self._add_overview(doc, content["overview"])

        # 教学目标
        if "objectives" in content:
            self._add_objectives(doc, content["objectives"])

        # 词汇
        if "vocabulary" in content:
            self._add_vocabulary_table(doc, content["vocabulary"])

        # 保存到字节
        from io import BytesIO
        doc_bytes = BytesIO()
        doc.save(doc_bytes)
        return doc_bytes.getvalue()

    def _add_overview(self, doc: Document, overview: Dict):
        p = doc.add_paragraph()
        p.add_run("课程概述").bold().size(Pt(14))

        p = doc.add_paragraph()
        p.add_run(f"标题: {overview.get('title', '')}")
        p.add_run(f"\n描述: {overview.get('description', '')}")
        p.add_run(f"\n级别: {overview.get('level', '')}")
        p.add_run(f"\n时长: {overview.get('duration', '')}分钟")

    def _add_objectives(self, doc: Document, objectives: List[Dict]):
        doc.add_heading("教学目标", level=1)
        for i, obj in enumerate(objectives, 1):
            p = doc.add_paragraph()
            p.add_run(f"{i}. {obj['text']}", style="List Bullet")
```

**Step 3: 编写测试**

```python
# tests/services/test_word_generator.py

@pytest.mark.asyncio
async def test_generate_word_document():
    generator = WordDocumentGenerator()
    content = create_mock_content()

    result = generator.generate(content, {})

    assert isinstance(result, bytes)
    assert len(result) > 0

    # 验证是有效的DOCX文件
    from docx import Document
    from io import BytesIO
    doc = Document(BytesIO(result))
    assert len(doc.paragraphs) > 0
```

**Step 4: 提交**

```bash
git add backend/app/services/document_generators/ tests/services/test_word_generator.py
git commit -m "feat(export): add Word document generator"
```

---

### Task 5: 实现 PDF 文档生成

**文件:**
- Create: `backend/app/services/document_generators/pdf_generator.py`
- Create: `backend/templates/lesson_pdf.j2`
- Modify: `backend/app/services/pdf_renderer_service.py` (extend)
- Create: `tests/services/test_pdf_generator.py`

**Step 1: 复用现有PDF渲染服务**

```python
# backend/app/services/document_generators/pdf_generator.py

from app.services.pdf_renderer_service import PDFRendererService

class PDFDocumentGenerator:
    def __init__(self):
        self.pdf_service = PDFRendererService()

    def generate(self, content: Dict[str, Any], template_vars: Dict[str, Any]) -> bytes:
        """生成PDF文档"""
        # 渲染为Markdown
        markdown = self._render_to_markdown(content)

        # 使用PDF渲染服务
        pdf_bytes = self.pdf_service.render_markdown_to_pdf(markdown)

        return pdf_bytes

    def _render_to_markdown(self, content: Dict[str, Any]) -> str:
        """将内容渲染为Markdown"""
        lines = []

        # 标题
        overview = content.get("overview", {})
        lines.append(f"# {overview.get('title', '教案')}\n")

        # 概述
        if "overview" in content:
            lines.append("## 课程概述\n")
            lines.append(f"- **标题**: {overview.get('title', '')}")
            lines.append(f"- **级别**: {overview.get('level', '')}")
            lines.append(f"- **时长**: {overview.get('duration', '')}分钟\n")

        # 其他章节...

        return "\n".join(lines)
```

**Step 2: 创建PDF模板**

```jinja2
{# backend/templates/lesson_pdf.j2 #}
# {{ lesson_title }}

{% if overview %}
## 课程概述

**标题**: {{ overview.title }}
**级别**: {{ overview.level }}
**时长**: {{ overview.duration }}分钟

{{ overview.description }}
{% endif %}

{% if objectives %}
## 教学目标

{% for obj in objectives %}
{{ loop.index }}. {{ obj.text }}
{% endfor %}
{% endif %}

{% if vocabulary %}
## 词汇表

| 单词 | 翻译 | 音标 |
|------|------|------|
{% for vocab in vocabulary %}
| {{ vocab.word }} | {{ vocab.translation }} | {{ vocab.phonetic or '-' }} |
{% endfor %}
{% endif %}
```

**Step 3: 编写测试**

```python
# tests/services/test_pdf_generator.py

@pytest.mark.asyncio
async def test_generate_pdf_document():
    generator = PDFDocumentGenerator()
    content = create_mock_content()

    result = generator.generate(content, {})

    assert isinstance(result, bytes)
    assert len(result) > 0
```

**Step 4: 提交**

```bash
git add backend/app/services/document_generators/pdf_generator.py backend/templates/lesson_pdf.j2
git commit -m "feat(export): add PDF document generator with Jinja2 template"
```

---

### Task 6: 实现 PPTX 文档生成

**文件:**
- Create: `backend/app/services/document_generators/pptx_generator.py`
- Create: `tests/services/test_pptx_generator.py`

**Step 1: 安装依赖**

```bash
pip install python-pptx
```

**Step 2: 实现PPTX生成器**

```python
# backend/app/services/document_generators/pptx_generator.py

from pptx import Presentation
from pptx.util import Inches, Pt

class PPTXDocumentGenerator:
    def generate(self, content: Dict[str, Any], template_vars: Dict[str, Any]) -> bytes:
        """生成PPTX文档"""
        prs = Presentation()

        # 标题页
        title_slide = prs.slides.add_slide(0)
        self._add_title(title_slide, content.get("overview", {}))

        # 教学目标页
        if "objectives" in content:
            slide = prs.slides.add_slide(len(prs.slides))
            self._add_objectives_slide(slide, content["objectives"])

        # 词汇页
        if "vocabulary" in content:
            slide = prs.slides.add_slide(len(prs.slides))
            self._add_vocabulary_slide(slide, content["vocabulary"])

        # 保存到字节
        from io import BytesIO
        prs_bytes = BytesIO()
        prs.save(prs_bytes)
        return prs_bytes.getvalue()

    def _add_title(self, slide, overview: Dict):
        title = overview.get("title", "教案")
        subtitle = f"{overview.get('level', '')} · {overview.get('duration', '')}分钟"

        title_shape = slide.shapes.title
        title_shape.text = title

        subtitle_shape = slide.placeholders[0]
        subtitle_shape.text = subtitle
```

**Step 3: 编写测试**

```python
# tests/services/test_pptx_generator.py

@pytest.mark.asyncio
async def test_generate_pptx_document():
    generator = PPTXDocumentGenerator()
    content = create_mock_content()

    result = generator.generate(content, {})

    assert isinstance(result, bytes)
    assert len(result) > 0
```

**Step 4: 提交**

```bash
git add backend/app/services/document_generators/pptx_generator.py tests/services/test_pptx_generator.py
git commit -m "feat(export): add PPTX document generator"
```

---

## Phase 3: 模板管理系统 (2天)

### Task 7: 实现模板服务

**文件:**
- Create: `backend/app/services/template_service.py`
- Create: `backend/app/api/v1/export_templates_api.py`
- Create: `tests/services/test_template_service.py`
- Create: `tests/api/test_export_templates_api.py`

**Step 1: 创建模板变量类型**

```python
# backend/app/services/template_service.py

from typing import List, Dict, Any
from pydantic import BaseModel

class TemplateVariable(BaseModel):
    name: str
    type: str  # text, textarea, number, date, select, checkbox
    label: str
    default: Any = None
    required: bool = False
    options: List[str] = []  # for select type

class ExportTemplateService:
    async def create_template(self, template_data: Dict[str, Any], created_by: str) -> ExportTemplate:
        """创建新模板"""
        template = ExportTemplate(
            id=uuid.uuid4(),
            name=template_data["name"],
            description=template_data.get("description", ""),
            format=template_data["format"],
            template_path=template_data["template_path"],
            variables=template_data.get("variables", []),
            created_by=created_by,
            is_system=False
        )

        db.add(template)
        await db.commit()
        return template

    async def list_templates(
        self,
        format: Optional[str] = None,
        is_system: Optional[bool] = None
    ) -> List[ExportTemplate]:
        """列出模板"""
        query = select(ExportTemplate)

        if format:
            query = query.where(ExportTemplate.format == format)
        if is_system is not None:
            query = query.where(ExportTemplate.is_system == is_system)

        query = query.where(ExportTemplate.is_active == True)
        query = query.order_by(ExportTemplate.usage_count.desc())

        result = await db.execute(query)
        return result.scalars().all()

    async def get_template(self, template_id: str) -> ExportTemplate:
        """获取模板详情"""
        query = select(ExportTemplate).where(ExportTemplate.id == template_id)
        result = await db.execute(query)

        template = result.scalar_one_or_none()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")

        return template
```

**Step 2: 编写API端点**

```python
# backend/app/api/v1/export_templates_api.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user

router = APIRouter()

@router.get("/templates")
async def list_templates(
    format: Optional[str] = None,
    is_system: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ExportTemplateService()
    templates = await service.list_templates(format, is_system)
    return {"templates": templates}

@router.post("/templates")
async def create_template(
    template_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ExportTemplateService()
    template = await service.create_template(template_data, current_user.id)
    return {"template": template}
```

**Step 3: 编写测试**

```python
# tests/services/test_template_service.py

@pytest.mark.asyncio
async def test_create_template():
    service = ExportTemplateService()

    template_data = {
        "name": "自定义模板",
        "format": "word",
        "template_path": "/templates/custom.docx",
        "variables": [
            {"name": "lesson_title", "type": "text", "label": "教案标题", "required": True}
        ]
    }

    template = await service.create_template(template_data, "user-123")

    assert template.name == "自定义模板"
    assert template.is_system == False
```

**Step 4: 提交**

```bash
git add backend/app/services/template_service.py backend/app/api/v1/export_templates_api.py tests/
git commit -m "feat(export): add template service and API endpoints"
```

---

### Task 8: 实现模板预览功能

**文件:**
- Create: `backend/app/api/v1/export_templates_api.py` (add preview endpoint)
- Create: `tests/api/test_template_preview.py`

**Step 1: 添加预览端点**

```python
# backend/app/api/v1/export_templates_api.py

@router.post("/templates/{template_id}/preview")
async def preview_template(
    template_id: str,
    lesson_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """预览模板效果"""
    # 获取模板
    template_service = ExportTemplateService()
    template = await template_service.get_template(template_id)

    # 获取教案数据
    lesson_service = LessonService()
    lesson = await lesson_service.get_by_id(lesson_id, db)

    # 渲染内容
    content_service = ContentRenderer()
    content = await content_service.render(
        lesson,
        template.variables.map(lambda v: v["name"])
    )

    # 生成预览
    generator = get_document_generator(template.format)
    preview_bytes = generator.generate(content, {})

    # 返回预览URL或直接返回文件
    return Response(
        content=preview_bytes,
        media_type=get_media_type(template.format)
    )
```

**Step 2: 编写测试**

```python
# tests/api/test_template_preview.py

@pytest.mark.asyncio
async def test_template_preview():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 登录
        token = await login_as_teacher(client)
        headers = {"Authorization": f"Bearer {token}"}

        # 创建预览请求
        response = await client.post(
            f"/api/v1/export-templates/{template_id}/preview",
            headers=headers,
            json={"lesson_id": "lesson-123"}
        )

        assert response.status_code == 200
        assert len(response.content) > 0
```

**Step 3: 提交**

```bash
git add tests/api/test_template_preview.py
git commit -m "feat(export): add template preview functionality"
```

---

## Phase 4: 异步任务处理 (2天)

### Task 9: 实现任务处理器

**文件:**
- Create: `backend/app/services/task_processor.py`
- Create: `tests/services/test_task_processor.py`

**Step 1: 创建任务处理器**

```python
# backend/app/services/task_processor.py

import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

class LessonExportTaskProcessor:
    async def process_task(
        self,
        task_id: str,
        db: AsyncSession
    ):
        """处理导出任务"""
        task = await self._get_task(task_id, db)

        try:
            # 更新状态
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.utcnow()
            await db.commit()

            # 1. 加载数据
            await self._notify_progress(task_id, 10, "加载教案数据...")
            lesson = await self._load_lesson(task.lesson_id, db)
            template = await self._load_template(task.template_id, db)

            # 2. 渲染内容
            await self._notify_progress(task_id, 30, "渲染教案内容...")
            content_service = ContentRenderer()
            content = await content_service.render(
                lesson,
                self._parse_sections(task.options["sections"])
            )

            # 3. 生成文档
            await self._notify_progress(task_id, 50, "生成文档...")
            generator = self._get_generator(task.format)
            document_bytes = generator.generate(content, template.variables)

            # 4. 保存文件
            await self._notify_progress(task_id, 80, "保存文档...")
            file_service = FileStorageService(settings.EXPORT_DIR)
            filename = f"{lesson.title}.{self._get_extension(task.format)}"
            file_path, file_size = await file_service.save_file(
                document_bytes,
                filename,
                task.format
            )

            # 5. 更新任务状态
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            task.file_path = file_path
            task.file_size = file_size
            task.download_url = f"/api/v1/lesson-export/exports/{Path(file_path).name}"
            task.completed_at = datetime.utcnow()

            # 更新模板使用次数
            if template:
                template.usage_count += 1

            await db.commit()

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            await db.commit()
            raise

    async def _notify_progress(self, task_id: str, progress: int, message: str):
        """通知进度"""
        # WebSocket推送或轮询更新
        await progress_notifier.notify(task_id, {
            "type": "progress",
            "progress": progress,
            "message": message
        })
```

**Step 2: 编写测试**

```python
# tests/services/test_task_processor.py

@pytest.mark.asyncio
async def test_process_task_success():
    processor = LessonExportTaskProcessor()
    task = await create_mock_task(status=TaskStatus.PENDING)

    await processor.process_task(task.id, db)

    # 验证任务状态
    updated_task = await get_task(task.id)
    assert updated_task.status == TaskStatus.COMPLETED
    assert updated_task.download_url is not None

@pytest.mark.asyncio
async def test_process_task_with_error():
    processor = LessonExportTaskProcessor()
    task = await create_mock_task_with_invalid_lesson()

    with pytest.raises(Exception):
        await processor.process_task(task.id, db)

    updated_task = await get_task(task.id)
    assert updated_task.status == TaskStatus.FAILED
```

**Step 3: 提交**

```bash
git add backend/app/services/task_processor.py tests/services/test_task_processor.py
git commit -m "feat(export): add async task processor"
```

---

## Phase 5: WebSocket实时推送 (2天)

### Task 10: 实现WebSocket服务

**文件:**
- Create: `backend/app/api/v1/export_websocket.py`
- Create: `backend/app/services/progress_notifier.py`
- Create: `tests/api/test_export_websocket.py`

**Step 1: 创建WebSocket管理器**

```python
# backend/app/api/v1/export_websocket.py

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[task_id] = websocket

        # 发送连接确认
        await websocket.send_json({
            "type": "connected",
            "task_id": task_id,
            "status": "pending"
        })

    def disconnect(self, task_id: str):
        if task_id in self.active_connections:
            del self.active_connections[task_id]

    async def send_progress(self, task_id: str, message: Dict):
        if task_id in self.active_connections:
            await self.active_connections[task_id].send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/lesson-export/{task_id}")
async def export_progress_websocket(
    websocket: WebSocket,
    task_id: str,
    token: str
):
    await manager.connect(task_id, websocket)

    try:
        # 保持连接活跃
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(task_id)
    except Exception as e:
        manager.disconnect(task_id)
        raise
```

**Step 2: 创建进度通知服务**

```python
# backend/app/services/progress_notifier.py

class ProgressNotifier:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    async def notify(
        self,
        task_id: str,
        message: Dict[str, Any]
    ):
        """发送进度通知"""
        await self.manager.send_progress(task_id, message)

    async def notify_complete(
        self,
        task_id: str,
        task: ExportTask
    ):
        """通知任务完成"""
        await self.manager.send_progress(task_id, {
            "type": "completed",
            "task_id": task_id,
            "status": task.status,
            "download_url": task.download_url
        })

    async def notify_error(
        self,
        task_id: str,
        error_message: str
    ):
        """通知错误"""
        await self.manager.send_progress(task_id, {
            "type": "error",
            "task_id": task_id,
            "error_message": error_message
        })
```

**Step 3: 编写测试**

```python
# tests/api/test_export_websocket.py

@pytest.mark.asyncio
async def test_websocket_connection():
    async with client.websocket_connect(
        f"/ws/lesson-export/{task_id}"
    ) as websocket:
        # 接收连接消息
        data = websocket.receive_json()
        assert data["type"] == "connected"
```

**Step 4: 提交**

```bash
git add backend/app/api/v1/export_websocket.py backend/app/services/progress_notifier.py tests/api/test_export_websocket.py
git commit -m "feat(export): add WebSocket real-time progress push"
```

---

## Phase 6: 前端UI增强 (3天)

### Task 11: 增强导出选项面板

**文件:**
- Modify: `frontend/src/components/ExportOptionsPanel.vue`
- Modify: `frontend/src/views/teacher/LessonExportView.vue`

**Step 1: 更新ExportOptionsPanel组件**

```vue
<!-- frontend/src/components/ExportOptionsPanel.vue -->
<template>
  <el-form :model="localOptions" label-width="120px">
    <!-- 格式选择 -->
    <el-form-item label="导出格式">
      <el-radio-group v-model="localOptions.format">
        <el-radio-button value="word">
          <el-icon><Document /></el-icon>
          Word
        </el-radio-button>
        <el-radio-button value="pdf">
          <el-icon><Notebook /></el-icon>
          PDF
        </el-radio-button>
        <el-radio-button value="pptx">
          <el-icon><Present /></el-icon>
          PPT
        </el-radio-button>
      </el-radio-group>
    </el-form-item>

    <!-- 模板选择 -->
    <el-form-item label="使用模板">
      <el-select
        v-model="localOptions.template_id"
        placeholder="选择模板"
        clearable
        @change="handleTemplateChange"
      >
        <el-option
          v-for="template in templates"
          :key="template.id"
          :label="template.name"
          :value="template.id"
        >
          <div class="template-option">
            <span>{{ template.name }}</span>
            <el-tag size="small">{{ template.format }}</el-tag>
          </div>
        </el-option>
      </el-select>
      <el-button
        @click="openTemplateManager"
        text
        type="primary"
      >
        管理模板
      </el-button>
    </el-form-item>

    <!-- 章节选择 -->
    <el-form-item label="导出章节">
      <el-checkbox-group v-model="localOptions.sections">
        <el-checkbox label="overview">课程概述</el-checkbox>
        <el-checkbox label="objectives">教学目标</el-checkbox>
        <el-checkbox label="vocabulary">词汇表</el-checkbox>
        <el-checkbox label="grammar">语法重点</el-checkbox>
        <el-checkbox label="structure">教学结构</el-checkbox>
        <el-checkbox label="materials">教学材料</el-checkbox>
        <el-checkbox label="exercises">练习题</el-checkbox>
      </el-checkbox-group>
    </el-form-item>

    <!-- 其他选项 -->
    <el-form-item label="其他选项">
      <el-space direction="vertical" :size="8">
        <el-checkbox v-model="localOptions.include_teacher_notes">
          包含教师备注
        </el-checkbox>
        <el-checkbox v-model="localOptions.include_answers">
          包含练习答案
        </el-checkbox>
        <el-checkbox v-model="localOptions.include_page_numbers">
          显示页码
        </el-checkbox>
        <el-checkbox v-model="localOptions.include_toc">
          包含目录
        </el-checkbox>
      </el-space>
    </el-form-item>

    <!-- 预览按钮 -->
    <el-form-item>
      <el-button
        @click="handlePreview"
        :disabled="!canPreview"
        :loading="previewLoading"
      >
        <el-icon><View /></el-icon>
        预览效果
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Document, Notebook, Present, View } from '@element-plus/icons-vue'
import type { ExportOptions, ExportTemplate } from '@/types/lessonExport'

interface Props {
  modelValue: ExportOptions
  templates?: ExportTemplate[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: ExportOptions]
}>()

const localOptions = ref<ExportOptions>({ ...props.modelValue })
const templates = ref<ExportTemplate[]>(props.templates || [])
const previewLoading = ref(false)

// 计算属性
const canPreview = computed(() => {
  return localOptions.value.template_id !== undefined
})

// 监听变化
watch(localOptions, (newValue) => {
  emit('update:modelValue', newValue)
}, { deep: true })

// 方法
const handleTemplateChange = (templateId: string) => {
  const template = templates.value.find(t => t.id === templateId)
  if (template) {
    // 更新可用章节
    updateAvailableSections(template)
  }
}

const updateAvailableSections = (template: ExportTemplate) => {
  // 根据模板变量更新可用章节
  // ...
}

const handlePreview = async () => {
  previewLoading.value = true
  try {
    // 调用预览API
    emit('preview', localOptions.value)
  } finally {
    previewLoading.value = false
  }
}
</script>
```

**Step 2: 提交**

```bash
git add frontend/src/components/ExportOptionsPanel.vue
git commit -m "feat(export): enhance export options panel with template support"
```

---

### Task 12: 实时进度对话框

**文件:**
- Create: `frontend/src/components/ExportProgressDialog.vue`
- Modify: `frontend/src/views/teacher/LessonExportView.vue`

**Step 1: 创建进度对话框组件**

```vue
<!-- frontend/src/components/ExportProgressDialog.vue -->
<template>
  <el-dialog
    v-model="visible"
    title="导出进度"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    width="500px"
  >
    <div class="export-progress">
      <!-- 总体进度 -->
      <el-progress
        :percentage="overallProgress"
        :status="progressStatus"
      >
        <template #default="{ percentage }">
          <span class="progress-text">{{ percentage }}%</span>
        </template>
      </el-progress>

      <!-- 当前步骤 -->
      <div class="current-step">
        <el-icon v-if="isProcessing" class="is-loading">
          <Loading />
        </el-icon>
        <span>{{ currentMessage }}</span>
      </div>

      <!-- 步骤时间线 -->
      <el-timeline class="step-timeline">
        <el-timeline-item
          v-for="step in steps"
          :key="step.name"
          :type="getStepStatus(step.status)"
          :icon="getStepIcon(step.status)"
        >
          <div class="step-content">
            <span class="step-name">{{ step.name }}</span>
            <span v-if="step.duration" class="step-duration">{{ step.duration }}</span>
          </div>
        </el-timeline-item>
      </el-timeline>

      <!-- 完成后显示下载按钮 -->
      <div v-if="isCompleted" class="complete-actions">
        <el-button type="primary" @click="handleDownload">
          立即下载
        </el-button>
        <el-button @click="handleClose">关闭</el-button>
      </div>

      <!-- 失败后显示错误信息 -->
      <div v-if="isFailed" class="error-actions">
        <el-alert
          type="error"
          :title="errorMessage"
          :closable="false"
        />
        <el-button @click="handleRetry">重试</el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { useExportWebSocket } from '@/composables/useExportWebSocket'

interface Props {
  modelValue: boolean
  taskId: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'download': []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// WebSocket 连接
const { progress, currentMessage, steps, isProcessing, isCompleted, isFailed, errorMessage } =
  useExportWebSocket(props.taskId)

// 计算属性
const overallProgress = computed(() => progress.value)
const progressStatus = computed(() => {
  if (isFailed.value) return 'exception'
  if (isCompleted.value) return 'success'
  return undefined
})

// 方法
const handleDownload = () => {
  emit('download')
}

const handleClose = () => {
  visible.value = false
}

const getStepStatus = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': 'info',
    'processing': 'primary',
    'completed': 'success',
    'failed': 'danger'
  }
  return statusMap[status] || 'info'
}

const getStepIcon = (status: string) => {
  return status === 'completed' ? 'CircleCheck' : 'Clock'
}
</script>
```

**Step 2: 创建WebSocket组合式函数**

```typescript
// frontend/src/composables/useExportWebSocket.ts

export function useExportWebSocket(taskId: string) {
  const progress = ref(0)
  const currentMessage = ref('')
  const steps = ref<Step[]>([])
  const isProcessing = ref(false)
  const isCompleted = ref(false)
  const isFailed = ref(false)
  const errorMessage = ref('')

  let ws: WebSocket | null = null

  const connect = () => {
    const wsUrl = `ws://localhost:8000/api/v1/ws/lesson-export/${taskId}`
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      handleMessage(message)
    }

    ws.onerror = () => {
      console.error('WebSocket error')
      isFailed.value = true
      errorMessage.value = '连接失败'
    }

    ws.onclose = () => {
      console.log('WebSocket closed')
      if (!isCompleted.value && !isFailed.value) {
        // 尝试重连
        setTimeout(() => connect(), 1000)
      }
    }
  }

  const handleMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'connected':
        console.log('Connected to task:', message.task_id)
        break
      case 'progress':
        progress.value = message.progress
        currentMessage.value = message.message
        updateSteps(message.message)
        break
      case 'completed':
        isCompleted.value = true
        progress.value = 100
        break
      case 'error':
        isFailed.value = true
        errorMessage.value = message.error_message
        break
    }
  }

  const disconnect = () => {
    if (ws) {
      ws.close()
      ws = null
    }
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    progress,
    currentMessage,
    steps,
    isProcessing,
    isCompleted,
    isFailed,
    errorMessage,
    disconnect
  }
}
```

**Step 3: 提交**

```bash
git add frontend/src/components/ExportProgressDialog.vue frontend/src/composables/useExportWebSocket.ts
git commit -m "feat(export): add real-time progress dialog with WebSocket"
```

---

## Phase 7: 模板管理界面 (2天)

### Task 13: 实现模板管理对话框

**文件:**
- Create: `frontend/src/components/TemplateManagerDialog.vue`
- Create: `frontend/src/components/TemplateEditor.vue`
- Modify: `frontend/src/views/teacher/LessonExportView.vue`

**Step 1: 创建模板管理器对话框**

```vue
<!-- frontend/src/components/TemplateManagerDialog.vue -->
<template>
  <el-dialog
    v-model="visible"
    title="模板管理"
    width="900px"
  >
    <div class="template-manager">
      <!-- 工具栏 -->
      <div class="toolbar">
        <el-button type="primary" @click="handleCreateTemplate">
          <el-icon><Plus /></el-icon>
          新建模板
        </el-button>
        <el-button @click="refreshTemplates">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <!-- 模板列表 -->
      <el-table :data="templates" style="width: 100%">
        <el-table-column prop="name" label="模板名称" width="200" />
        <el-table-column prop="format" label="格式" width="100">
          <template #default="{ row }">
            <el-tag>{{ formatLabel(row.format) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="usage_count" label="使用次数" width="80" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button link @click="handleEdit(row)">编辑</el-button>
            <el-button link @click="handlePreview(row)">预览</el-button>
            <el-button
              v-if="!row.is_system"
              link
              type="danger"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
const visible = ref(false)
const templates = ref([])

const handleCreateTemplate = () => {
  // 打开模板编辑器
}

const handleEdit = (template: ExportTemplate) => {
  // 加载模板到编辑器
}

const handleDelete = async (template: ExportTemplate) => {
  // 删除模板
}
</script>
```

**Step 2: 提交**

```bash
git add frontend/src/components/TemplateManagerDialog.vue
git commit -m "feat(export): add template manager dialog"
```

---

### Task 14: 实现模板编辑器

**文件:**
- Create: `frontend/src/components/TemplateEditor.vue`

**Step 1: 创建模板编辑器**

```vue
<!-- frontend/src/components/TemplateEditor.vue -->
<template>
  <el-dialog
    v-model="visible"
    :title="isEditing ? '编辑模板' : '新建模板'"
    width="800px"
  >
    <el-form :model="templateForm" :rules="rules" label-width="120px">
      <el-form-item label="模板名称" prop="name">
        <el-input v-model="templateForm.name" placeholder="输入模板名称" />
      </el-form-item>

      <el-form-item label="导出格式" prop="format">
        <el-select v-model="templateForm.format">
          <el-option label="Word" value="word" />
          <el-option label="PDF" value="pdf" />
          <el-option label="PPT" value="pptx" />
        </el-select>
      </el-form-item>

      <el-form-item label="模板描述">
        <el-input
          v-model="templateForm.description"
          type="textarea"
          :rows="3"
        />
      </el-form-item>

      <!-- 模板变量 -->
      <el-form-item label="模板变量">
        <div class="variables-list">
          <div
            v-for="(variable, index) in templateForm.variables"
            :key="index"
            class="variable-item"
          >
            <el-input
              v-model="variable.name"
              placeholder="变量名"
              style="width: 200px"
            />
            <el-select v-model="variable.type" style="width: 120px">
              <el-option label="文本" value="text" />
              <el-option label="多行文本" value="textarea" />
              <el-option label="数字" value="number" />
            </el-select>
            <el-input
              v-model="variable.label"
              placeholder="显示名称"
            />
            <el-button @click="removeVariable(index)" text type="danger">
              删除
            </el-button>
          </div>
        </div>
        <el-button @click="addVariable" text>
          + 添加变量
        </el-button>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleSave">
        保存模板
      </el-button>
    </template>
  </el-dialog>
</template>
```

**Step 2: 提交**

```bash
git add frontend/src/components/TemplateEditor.vue
git commit -m "feat(export): add template editor component"
```

---

## Phase 8: 集成测试与文档 (2天)

### Task 15: 端到端测试

**文件:**
- Create: `frontend/tests/e2e/lesson-export.spec.ts`
- Modify: `frontend/tests/e2e/fixtures.ts` (add export test fixtures)

**Step 1: 创建E2E测试**

```typescript
// frontend/tests/e2e/lesson-export.spec.ts

import { test, expect } from '@playwright/test'

test.describe('教案导出 E2E', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('http://localhost:5173/login')
    await page.fill('input[name="username"]', 'test_teacher')
    await page.fill('input[name="password"]', 'Test1234')
    await page.click('button[type="submit"]')

    // 等待跳转
    await page.waitForURL('**/dashboard')
  })

  test('完整导出流程', async ({ page }) => {
    // 1. 进入教案导出页面
    await page.goto('http://localhost:5173/teacher/lesson-export')

    // 2. 选择教案
    await page.click('button:has-text("添加教案")')
    await page.click('.lesson-item:first-child')
    await page.click('button:has-text("确认")')

    // 3. 配置导出选项
    await page.check('input[value="word"][checked=true]')
    await page.check('input[value="pdf"][checked=true]')

    // 4. 开始导出
    await page.click('button:has-text("开始导出")')

    // 5. 等待WebSocket进度更新
    await page.waitForSelector('.export-progress', { state: 'visible' })

    // 6. 验证进度更新
    await page.waitForSelector('.el-progress', { state: 'visible' })

    // 7. 等待完成
    await page.waitForSelector('.complete-actions', { state: 'visible' })

    // 8. 点击下载
    const downloadPromise = page.waitForEvent('download')
    await page.click('button:has-text("立即下载")')
    await downloadPromise
  })

  test('模板创建和使用流程', async ({ page }) => {
    // 1. 打开模板管理
    await page.goto('http://localhost:5173/teacher/lesson-export')
    await page.click('button:has-text("管理模板")')

    // 2. 创建新模板
    await page.click('button:has-text("新建模板")')
    await page.fill('input[name="name"]', '我的测试模板')
    await page.select('select[name="format"]', 'word')
    await page.click('button:has-text("保存模板")')

    // 3. 使用新模板导出
    await page.goto('http://localhost:5173/teacher/lesson-export')
    await page.click('button:has-text("添加教案")')
    await page.click('.lesson-item:first-child')

    // 选择自定义模板
    await page.click('.template-selector')
    await page.click(`text=我的测试模板`)

    // 4. 开始导出
    await page.click('button:has-text("开始导出")')

    // 5. 验证导出成功
    await page.waitForSelector('.complete-actions', { state: 'visible' })
  })
})
```

**Step 2: 提交**

```bash
git add frontend/tests/e2e/lesson-export.spec.ts
git commit -m "test(export): add end-to-end tests for lesson export"
```

---

### Task 16: 更新用户文档

**文件:**
- Create: `docs/lesson-export-guide.md`
- Update: `docs/plans/2026-02-01-mvp-implementation-plan.md`

**Step 1: 创建用户指南**

```markdown
# 教案导出功能使用指南

## 概述

教案导出功能允许教师将教案导出为多种格式（Word、PDF、PPT、Markdown），支持自定义模板和实时进度追踪。

## 功能特性

### 支持的导出格式

| 格式 | 描述 | 适用场景 |
|------|------|----------|
| Word (.docx) | 可编辑文档，保留格式 | 教师自定义、进一步编辑 |
| PDF (.pdf) | 固定格式，专业呈现 | 打印、分发 |
| PPT (.pptx) | 演示文稿 | 课堂展示 |
| Markdown (.md) | 文本格式 | 版本控制、协作编辑 |

### 模板管理

- 系统预设模板：开箱即用
- 自定义模板：满足个性化需求
- 模板变量系统：动态插入内容
- 模板预览：实时预览效果

### 实时进度追踪

- WebSocket实时推送进度更新
- 详细的步骤时间线
- 断线自动重连
- 多任务并发处理

## 使用方法

### 单个教案导出

1. 进入「教案导出」页面
2. 点击「添加教案」选择教案
3. 配置导出选项（格式、章节、其他选项）
4. 点击「开始导出」
5. 实时查看进度
6. 导出完成后点击「立即下载」

### 批量导出

1. 选择多个教案
2. 统一配置导出选项
3. 一键创建多个导出任务
4. 分别下载生成的文件

### 自定义模板

1. 进入「模板管理」
2. 点击「新建模板」
3. 填写模板信息和变量
4. 保存模板
5. 在导出时选择自定义模板
```

**Step 2: 更新MVP计划文档**

```bash
git add docs/lesson-export-guide.md docs/plans/2026-02-01-mvp-implementation-plan.md
git commit -m "docs(export): add lesson export user guide and update MVP plan"
```

---

## 验收标准总结

### 功能完整性

- [ ] 支持4种导出格式（Word/PDF/PPT/Markdown）
- [ ] 完整的模板管理系统
- [ ] WebSocket实时进度推送
- [ ] 持久化任务存储
- [ ] 文件管理和下载

### 测试覆盖

- [ ] 单元测试覆盖率 ≥ 80%
- [ ] API集成测试覆盖率 ≥ 75%
- [ ] E2E测试覆盖主要用户路径
- [ ] 所有测试通过

### 文档完整性

- [ ] 用户使用指南
- [ ] API文档更新
- [ ] 代码注释完整

### 性能指标

- [ ] 单个文档生成 < 30秒
- [ ] WebSocket延迟 < 500ms
- [ ] 支持并发5个导出任务

---

## 依赖安装

```bash
# 后端依赖
cd backend
pip install python-docx python-pptx

# 前端依赖
cd frontend
npm install  # 已有依赖
```

---

## 执行方式

本计划包含16个任务，预计14天完成。

**推荐执行方式**: Subagent-Driven（当前会话）

使用 `superpowers:executing-plans` 或 `superpowers:subagent-driven-development` 技能执行本计划。

---

**下一步**: 是否开始执行此实施计划？
