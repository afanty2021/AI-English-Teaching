"""
PDF渲染服务 - AI英语教学系统
使用 markdown2 + weasyprint 实现 Markdown 到 PDF 的转换
"""
import io
import logging
from typing import Any, Dict, Optional

from jinja2 import Environment, Template
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

try:
    import markdown2
except ImportError:
    raise ImportError(
        "markdown2 is required for PDF export. "
        "Install it with: pip install markdown2"
    )

logger = logging.getLogger(__name__)


class PdfRendererService:
    """
    PDF渲染服务类

    核心功能：
    1. Markdown 到 HTML 的转换（使用 markdown2）
    2. CSS 样式注入和应用
    3. HTML 到 PDF 的渲染（使用 weasyprint）
    4. 中文字体支持和配置
    """

    # 默认的 markdown2 扩展功能
    MARKDOWN_EXTRAS = [
        "tables",           # 支持表格
        "fenced-code-blocks",  # 支持围栏代码块
        "header-ids",       # 标题自动生成 ID
        "footnotes",        # 脚注支持
        "strike",           # 删除线支持
        "task_list",        # 任务列表
        "code-friendly",    # 代码友好
        "spoiler",          # 剧透隐藏
        "markdown-in-html", # HTML 中的 Markdown
    ]

    def __init__(self, template_env: Optional[Environment] = None):
        """
        初始化 PDF 渲染服务

        Args:
            template_env: Jinja2 模板环境（可选）
        """
        self.template_env = template_env

        # 初始化 markdown2 转换器
        self.markdowner = markdown2.Markdown(extras=self.MARKDOWN_EXTRAS)

        # 字体配置
        self.font_config = FontConfiguration()

        # 缓存 CSS 样式
        self._cached_css: Optional[CSS] = None

    async def markdown_to_html(
        self,
        markdown_content: str,
    ) -> str:
        """
        将 Markdown 内容转换为 HTML

        Args:
            markdown_content: Markdown 格式的文本

        Returns:
            HTML 格式的文本
        """
        if not markdown_content:
            return ""

        # 重置转换器状态（处理多次调用）
        self.markdowner.reset()

        # 执行转换
        html_content = self.markdowner.convert(markdown_content)

        return html_content

    async def _load_css_template(self) -> str:
        """
        加载 CSS 样式模板

        Returns:
            CSS 样式字符串
        """
        if self.template_env:
            try:
                template = self.template_env.get_template("pdf_styles.css.j2")
                return template.render()
            except Exception as e:
                logger.warning(f"Failed to load CSS template: {e}, using fallback")

        # 后备样式
        return self._get_fallback_css()

    def _get_fallback_css(self) -> str:
        """
        获取后备 CSS 样式

        Returns:
            CSS 样式字符串
        """
        return """
        @page {
            size: A4;
            margin: 2cm;
        }

        body {
            font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }

        h1, h2, h3, h4, h5, h6 {
            page-break-after: avoid;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }

        h1 {
            font-size: 24pt;
            border-bottom: 2px solid #eee;
            padding-bottom: 0.3em;
        }

        h2 {
            font-size: 18pt;
            border-bottom: 1px solid #eee;
            padding-bottom: 0.2em;
        }

        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
            page-break-inside: avoid;
        }

        th, td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }

        th {
            background-color: #f5f5f5;
            font-weight: bold;
        }

        tr:nth-child(even) {
            background-color: #f9f9f9;
        }

        blockquote {
            border-left: 4px solid #ddd;
            padding-left: 1em;
            margin: 1em 0;
            color: #666;
        }

        code {
            background-color: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }

        pre {
            background-color: #f5f5f5;
            padding: 1em;
            border-radius: 5px;
            overflow-x: auto;
            page-break-inside: avoid;
        }

        a {
            color: #0066cc;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }
        """

    async def _get_pdf_css(self) -> CSS:
        """
        获取 PDF 样式对象

        Returns:
            weasyprint CSS 对象
        """
        if self._cached_css is None:
            css_string = await self._load_css_template()
            self._cached_css = CSS(string=css_string, font_config=self.font_config)

        return self._cached_css

    async def apply_pdf_styles(
        self,
        html_content: str,
        title: str = "错题本",
    ) -> str:
        """
        为 HTML 内容应用 PDF 样式

        Args:
            html_content: HTML 内容
            title: 文档标题（用于页眉）

        Returns:
            应用样式后的完整 HTML 文档
        """
        # 构建完整的 HTML 文档
        full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        /* 基础重置样式 */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        html, body {{
            height: 100%;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""

        return full_html

    async def html_to_pdf(
        self,
        html_content: str,
    ) -> bytes:
        """
        将 HTML 内容转换为 PDF

        Args:
            html_content: HTML 内容

        Returns:
            PDF 字节数据
        """
        # 获取 CSS 样式
        pdf_css = await self._get_pdf_css()

        # 创建 HTML 对象并生成 PDF
        html_doc = HTML(
            string=html_content,
            base_url=".",  # 基础 URL，用于解析相对路径
            encoding="utf-8",
        )

        # 生成 PDF 字节流
        pdf_bytes = html_doc.write_pdf(
            stylesheets=[pdf_css],
            font_config=self.font_config,
            optimize_images=False,  # 不优化图片，保持原始质量
        )

        return pdf_bytes

    async def render_markdown_to_pdf(
        self,
        markdown_content: str,
        title: str = "错题本",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        完整流程：将 Markdown 内容渲染为 PDF

        Args:
            markdown_content: Markdown 格式的文本
            title: 文档标题
            metadata: 额外的元数据（传递给模板）

        Returns:
            PDF 字节数据

        Raises:
            ValueError: 输入内容为空
            RuntimeError: PDF 生成失败
        """
        if not markdown_content:
            raise ValueError("Markdown content cannot be empty")

        try:
            # 步骤 1: Markdown → HTML
            logger.debug("Converting Markdown to HTML...")
            html_content = await self.markdown_to_html(markdown_content)

            # 步骤 2: 应用 PDF 样式
            logger.debug("Applying PDF styles...")
            styled_html = await self.apply_pdf_styles(html_content, title)

            # 步骤 3: HTML → PDF
            logger.debug("Rendering PDF...")
            pdf_bytes = await self.html_to_pdf(styled_html)

            logger.info(f"PDF generated successfully: {len(pdf_bytes)} bytes")
            return pdf_bytes

        except Exception as e:
            logger.error(f"Failed to render PDF: {e}")
            raise RuntimeError(f"PDF rendering failed: {e}") from e

    async def render_template_to_pdf(
        self,
        template_name: str,
        context: Dict[str, Any],
        title: str = "错题本",
    ) -> bytes:
        """
        从 Jinja2 模板渲染 PDF

        Args:
            template_name: 模板名称
            context: 模板上下文变量
            title: 文档标题

        Returns:
            PDF 字节数据

        Raises:
            ValueError: 模板环境未初始化或模板不存在
        """
        if not self.template_env:
            raise ValueError("Template environment not initialized")

        # 渲染 Markdown 模板
        template = self.template_env.get_template(template_name)
        markdown_content = template.render(**context)

        # 转换为 PDF
        return await self.render_markdown_to_pdf(markdown_content, title)

    def clear_cache(self):
        """清除缓存的 CSS 和其他资源"""
        self._cached_css = None
        if hasattr(self.markdowner, "reset"):
            self.markdowner.reset()


# 创建服务工厂函数
def get_pdf_renderer_service(template_env: Optional[Environment] = None) -> PdfRendererService:
    """
    获取 PDF 渲染服务实例

    Args:
        template_env: Jinja2 模板环境（可选）

    Returns:
        PdfRendererService: PDF 渲染服务实例
    """
    return PdfRendererService(template_env)
