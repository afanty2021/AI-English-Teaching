"""
PDF渲染服务测试 - AI英语教学系统
测试 markdown2 + weasyprint 的 PDF 生成功能
"""
import os
from unittest.mock import MagicMock, Mock, patch

import pytest

# 检查是否安装了必要依赖
pytest.importorskip("markdown2")
pytest.importorskip("weasyprint")

from jinja2 import Environment
from weasyprint import CSS

from app.services.pdf_renderer_service import (
    PdfRendererService,
    get_pdf_renderer_service,
)


@pytest.fixture
def template_env():
    """创建 Jinja2 模板环境"""
    env = Environment(loader=None)
    return env


@pytest.fixture
def pdf_service(template_env):
    """创建 PDF 渲染服务实例"""
    return PdfRendererService(template_env)


class TestPdfRendererService:
    """PDF 渲染服务测试类"""

    def test_init_with_template_env(self, template_env):
        """测试带模板环境的服务初始化"""
        service = PdfRendererService(template_env)

        assert service.template_env == template_env
        assert service.markdowner is not None
        assert service.font_config is not None
        assert service._cached_css is None

    def test_init_without_template_env(self):
        """测试不带模板环境的服务初始化"""
        service = PdfRendererService()

        assert service.template_env is None
        assert service.markdowner is not None

    @pytest.mark.asyncio
    async def test_markdown_to_html_basic(self, pdf_service):
        """测试基础 Markdown 转 HTML"""
        markdown = "# 标题\n\n这是一段内容。"
        html = await pdf_service.markdown_to_html(markdown)

        assert "<h1" in html
        assert "标题" in html
        assert "<p" in html or "这是一段内容" in html

    @pytest.mark.asyncio
    async def test_markdown_to_html_table(self, pdf_service):
        """测试表格转换"""
        markdown = """| 列1 | 列2 |
|-----|-----|
| A   | B   |"""
        html = await pdf_service.markdown_to_html(markdown)

        assert "<table" in html or ("列1" in html and "列2" in html)

    @pytest.mark.asyncio
    async def test_markdown_to_html_fenced_code(self, pdf_service):
        """测试代码块转换"""
        markdown = """```\nprint("Hello")\n```"""
        html = await pdf_service.markdown_to_html(markdown)

        assert "<pre" in html or "<code" in html

    @pytest.mark.asyncio
    async def test_markdown_to_html_empty(self, pdf_service):
        """测试空内容处理"""
        html = await pdf_service.markdown_to_html("")

        assert html == ""

    @pytest.mark.asyncio
    async def test_apply_pdf_styles(self, pdf_service):
        """测试 PDF 样式应用"""
        html_content = "<h1>测试标题</h1><p>测试内容</p>"
        styled_html = await pdf_service.apply_pdf_styles(html_content, "测试文档")

        assert "<!DOCTYPE html>" in styled_html
        assert "<html" in styled_html
        assert "<head>" in styled_html
        assert "<body>" in styled_html
        assert html_content in styled_html
        assert "测试文档" in styled_html

    @pytest.mark.asyncio
    async def test_get_pdf_css_cached(self, pdf_service):
        """测试 CSS 缓存机制"""
        css1 = await pdf_service._get_pdf_css()
        css2 = await pdf_service._get_pdf_css()

        # 应该返回同一个 CSS 对象（缓存）
        assert css1 is css2

    @pytest.mark.asyncio
    async def test_get_pdf_css_after_clear(self, pdf_service):
        """测试清除缓存后的 CSS 重新加载"""
        css1 = await pdf_service._get_pdf_css()
        pdf_service.clear_cache()
        css2 = await pdf_service._get_pdf_css()

        # 清除缓存后应该是不同的对象
        assert css1 is not css2

    @pytest.mark.asyncio
    async def test_render_markdown_to_pdf_basic(self, pdf_service):
        """测试基本的 Markdown 到 PDF 转换"""
        markdown = """# 测试标题

这是一段测试内容。

| 列1 | 列2 |
|-----|-----|
| A   | B   |
"""

        pdf_bytes = await pdf_service.render_markdown_to_pdf(markdown, "测试")

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        # PDF 文件应该以 %PDF 开头
        assert pdf_bytes.startswith(b"%PDF")

    @pytest.mark.asyncio
    async def test_render_markdown_to_pdf_chinese(self, pdf_service):
        """测试中文字符支持"""
        markdown = """# 中文标题

这是中文内容。包含特殊字符：你好，世界！

| 姓名 | 年龄 |
|------|------|
| 张三 | 25   |
| 李四 | 30   |
"""

        pdf_bytes = await pdf_service.render_markdown_to_pdf(markdown, "中文测试")

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")

    @pytest.mark.asyncio
    async def test_render_markdown_to_pdf_empty_error(self, pdf_service):
        """测试空内容错误处理"""
        with pytest.raises(ValueError, match="cannot be empty"):
            await pdf_service.render_markdown_to_pdf("", "测试")

    @pytest.mark.asyncio
    async def test_render_markdown_to_pdf_complex(self, pdf_service):
        """测试复杂文档渲染"""
        markdown = """# 主标题

## 二级标题

这是正文内容。

### 列表
- 项目1
- 项目2
  - 子项目2.1
  - 子项目2.2

### 引用块
> 这是一段引用内容
> 可以有多行

### 代码块
```python
def hello():
    print("Hello, World!")
```

### 表格
| 姓名 | 年龄 | 城市 |
|------|------|------|
| 张三 | 25   | 北京 |
| 李四 | 30   | 上海 |
"""

        pdf_bytes = await pdf_service.render_markdown_to_pdf(markdown, "复杂文档")

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")

    @pytest.mark.asyncio
    async def test_render_template_to_pdf_error(self, pdf_service):
        """测试没有模板环境时的错误"""
        # 没有 template_env 的情况下应该抛出错误
        service = PdfRendererService()  # 不传入 template_env

        with pytest.raises(ValueError, match="Template environment not initialized"):
            await service.render_template_to_pdf("test.md", {})


class TestPdfRendererServiceFactory:
    """PDF 渲染服务工厂函数测试"""

    def test_get_pdf_renderer_service_without_env(self):
        """测试不带参数创建服务"""
        service = get_pdf_renderer_service()

        assert service is not None
        assert isinstance(service, PdfRendererService)
        assert service.template_env is None

    def test_get_pdf_renderer_service_with_env(self, template_env):
        """测试带模板环境创建服务"""
        service = get_pdf_renderer_service(template_env)

        assert service is not None
        assert isinstance(service, PdfRendererService)
        assert service.template_env == template_env


class TestPdfHelpers:
    """PDF 辅助工具测试"""

    def test_get_chinese_fonts(self):
        """测试获取中文字体列表"""
        from app.utils.pdf_helpers import get_chinese_fonts

        fonts = get_chinese_fonts()

        assert isinstance(fonts, list)
        assert len(fonts) > 0
        # 应该包含至少一个已知的中文字体
        assert any("PingFang" in f or "YaHei" in f or "Noto" in f for f in fonts)

    def test_check_font_availability(self):
        """检查字体可用性"""
        from app.utils.pdf_helpers import check_font_availability

        font_info = check_font_availability()

        assert "system" in font_info
        assert "font_families" in font_info
        assert isinstance(font_info["font_families"], list)

    def test_get_css_font_families(self):
        """测试获取 CSS 字体族字符串"""
        from app.utils.pdf_helpers import get_css_font_families

        css_fonts = get_css_font_families()

        assert isinstance(css_fonts, str)
        assert len(css_fonts) > 0
        # 应该包含引号和逗号
        assert '"' in css_fonts or "," in css_fonts

    def test_generate_font_css(self):
        """测试生成字体 CSS"""
        from app.utils.pdf_helpers import generate_font_css

        css = generate_font_css()

        assert isinstance(css, str)
        assert "font-family" in css
        assert "body" in css


@pytest.mark.integration
class TestPdfRenderingIntegration:
    """集成测试：完整的 PDF 生成流程"""

    @pytest.mark.asyncio
    async def test_full_mistake_report_pdf(self, pdf_service):
        """测试生成完整的错题报告 PDF"""
        markdown = """# 张三的英语错题本

> **学号**: 2024001
> **英语水平**: B1
> **导出时间**: 2026年02月03日
> **错题数量**: 2 道

---

## 学习概况

### 学生信息

| 项目 | 信息 |
|------|------|
| 姓名 | 张三 |
| 英文名 | Tom |
| 学号 | 2024001 |
| 英语水平 | B1 |

### 整体统计

| 统计项 | 数值 |
|--------|------|
| **错题总数** | 2 道 |
| **已掌握** | 0 道 (0%) |
| **待复习** | 2 道 |

---

## 错题详情

### 语法 (2 道)

#### 错题详情

**【题目内容】**

> He ___ to school yesterday.

**【答题情况】**

| 项目 | 内容 |
|------|------|
| ❌ 你的答案 | go |
| ✅ 正确答案 | went |
| 📚 题目类型 | 语法 |
| 🏷️ 状态 | 待复习 |
| 📊 错误次数 | 1 次 |

---

**【AI分析】**

##### 错误分类

> **时态错误** · 严重程度: 中等

##### 详细解释

这是一道过去时态的题目。句子中有明确的时间状语 "yesterday"（昨天），表示动作发生在过去，因此需要使用一般过去时。"go" 的过去式是 "went"。

##### 正确方法

一般过去时表示过去某个时间发生的动作或状态：
- 规则动词加 -ed：walk → walked
- 不规则动词需特殊记忆：go → went, do → did

---

#### 错题详情

**【题目内容】**

> She ___ English every day.

**【答题情况】**

| 项目 | 内容 |
|------|------|
| ❌ 你的答案 | study |
| ✅ 正确答案 | studies |
| 📚 题目类型 | 语法 |
| 🏷️ 状态 | 待复习 |
| 📊 错误次数 | 1 次 |

---

**【AI分析】**

##### 错误分类

> **主谓一致错误** · 严重程度: 中等

##### 详细解释

这是一道考查第三人称单数的题目。主语 "She" 是第三人称单数，在一般现在时中，动词需要加 -s。"study" 以辅音字母 y 结尾，变第三人称单数时需要将 y 变为 i 加 -es，即 "studies"。

---

## 学习建议

### 复习计划

基于当前错题情况，建议采用以下复习策略：

1. **优先级排序**: 关注语法时态和主谓一致问题
2. **复习频率**: 每天练习5-10道类似题目
3. **复习方法**: 先理解规则，再做练习

---

> 📝 本报告由 **AI赋能英语教学系统** 自动生成
"""

        pdf_bytes = await pdf_service.render_markdown_to_pdf(
            markdown,
            "张三的英语错题本"
        )

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")
        # 合理大小的 PDF（100KB - 5MB）
        assert 100_000 < len(pdf_bytes) < 5_000_000
