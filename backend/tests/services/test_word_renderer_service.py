"""
Word渲染服务测试 - AI英语教学系统
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.word_renderer_service import WordRendererService, MarkdownElement


class TestWordRendererService:
    """Word渲染服务测试类"""

    @pytest.fixture
    def service(self):
        """创建测试服务实例"""
        return WordRendererService()

    def test_init(self, service):
        """测试初始化"""
        assert service.current_os in ['mac', 'windows', 'linux']
        assert service._styles_initialized is False

    def test_get_chinese_font(self, service):
        """测试中文字体获取"""
        font = service._get_chinese_font()
        assert font is not None
        assert len(font) > 0

    def test_detect_os(self, service):
        """测试操作系统检测"""
        os_type = service._detect_os()
        assert os_type in ['mac', 'windows', 'linux']

    def test_parse_markdown_simple_paragraph(self, service):
        """测试解析普通段落"""
        markdown = "这是一个普通段落。"
        elements = service.parse_markdown(markdown)

        assert len(elements) == 1
        assert elements[0].type == "paragraph"
        assert elements[0].content == "这是一个普通段落。"

    def test_parse_markdown_heading(self, service):
        """测试解析标题"""
        markdown = "## 二级标题"
        elements = service.parse_markdown(markdown)

        assert len(elements) == 1
        assert elements[0].type == "heading"
        assert elements[0].level == 2
        assert elements[0].content == "二级标题"

    def test_parse_markdown_multiple_headings(self, service):
        """测试解析多个标题"""
        markdown = """# 一级标题
## 二级标题
### 三级标题
"""
        elements = service.parse_markdown(markdown)

        assert len(elements) == 3
        assert elements[0].type == "heading"
        assert elements[0].level == 1
        assert elements[1].level == 2
        assert elements[2].level == 3

    def test_parse_markdown_unordered_list(self, service):
        """测试解析无序列表"""
        markdown = """- 项目1
- 项目2
- 项目3
"""
        elements = service.parse_markdown(markdown)

        assert len(elements) == 1
        assert elements[0].type == "list"

    def test_parse_markdown_ordered_list(self, service):
        """测试解析有序列表"""
        markdown = """1. 第一项
2. 第二项
3. 第三项
"""
        elements = service.parse_markdown(markdown)

        assert len(elements) == 1
        assert elements[0].type == "olist"

    def test_parse_markdown_code_block(self, service):
        """测试解析代码块"""
        markdown = """```python
def hello():
    print("Hello, World!")
```
"""
        elements = service.parse_markdown(markdown)

        assert len(elements) == 1
        assert elements[0].type == "code"
        assert "def hello" in elements[0].content

    def test_parse_markdown_quote(self, service):
        """测试解析引用块"""
        markdown = """> 这是一个引用
> 第二行引用
"""
        elements = service.parse_markdown(markdown)

        assert len(elements) == 1
        assert elements[0].type == "quote"

    def test_parse_markdown_table(self, service):
        """测试解析表格"""
        markdown = """| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |
"""
        elements = service.parse_markdown(markdown)

        assert len(elements) == 1
        assert elements[0].type == "table"

    def test_parse_markdown_hr(self, service):
        """测试解析分割线"""
        markdown = """---
"""
        elements = service.parse_markdown(markdown)

        assert len(elements) == 1
        assert elements[0].type == "hr"

    def test_parse_markdown_empty_lines(self, service):
        """测试解析空行"""
        markdown = """段落1

段落2
"""
        elements = service.parse_markdown(markdown)

        # 空行应该被跳过
        assert len(elements) == 2

    def test_parse_markdown_bold_text(self, service):
        """测试解析粗体文本"""
        markdown = "这是**粗体**文本"
        elements = service.parse_markdown(markdown)

        assert len(elements) == 1
        # 粗体标记应该被移除
        assert "**" not in elements[0].content

    def test_parse_markdown_italic_text(self, service):
        """测试解析斜体文本（下划线格式）"""
        markdown = "这是_斜体_文本"
        elements = service.parse_markdown(markdown)

        assert len(elements) == 1
        # 下划线格式的斜体标记应该被移除
        assert "_" not in elements[0].content

    def test_parse_markdown_asterisk_literal(self, service):
        """测试解析字面星号（不是斜体标记）"""
        markdown = "这是*星号*文本"
        elements = service.parse_markdown(markdown)

        assert len(elements) == 1
        # 单星号是字面字符，不应该被移除
        assert "*" in elements[0].content

    def test_parse_markdown_inline_code(self, service):
        """测试解析行内代码"""
        markdown = "这是`代码`文本"
        elements = service.parse_markdown(markdown)

        assert len(elements) == 1
        # 行内代码标记应该被移除
        assert "`" not in elements[0].content

    def test_parse_markdown_complex(self, service):
        """测试解析复杂Markdown"""
        markdown = """# 标题

这是一个段落。

- 项目1
- 项目2

```python
print("hello")
```

| 列1 | 列2 |
|-----|-----|
| 数据 | 测试 |
"""
        elements = service.parse_markdown(markdown)

        # 应该解析出：标题、段落、列表、代码块、表格
        assert len(elements) >= 5

        # 验证元素类型
        types = [e.type for e in elements]
        assert "heading" in types
        assert "paragraph" in types
        assert "list" in types
        assert "code" in types
        assert "table" in types

    def test_markdown_to_docx_bytes_simple(self, service):
        """测试简单Markdown转Word字节"""
        markdown = "# 测试文档\n\n这是一个测试段落。"
        result = service.markdown_to_docx_bytes(markdown, title="测试文档")

        assert isinstance(result, bytes)
        assert len(result) > 0

        # 验证是有效的ZIP文件头（DOCX是ZIP格式）
        assert result[:4] == b'PK\x03\x04'

    def test_markdown_to_docx_bytes_with_list(self, service):
        """测试带列表的Markdown转Word字节"""
        markdown = """# 测试列表

- 项目1
- 项目2
- 项目3
"""
        result = service.markdown_to_docx_bytes(markdown, title="列表测试")

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:4] == b'PK\x03\x04'

    def test_markdown_to_docx_bytes_with_table(self, service):
        """测试带表格的Markdown转Word字节"""
        markdown = """| 姓名 | 年龄 |
|-----|-----|
| 张三 | 25 |
| 李四 | 30 |
"""
        result = service.markdown_to_docx_bytes(markdown, title="表格测试")

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_markdown_to_docx_bytes_empty(self, service):
        """测试空Markdown转Word字节"""
        result = service.markdown_to_docx_bytes("", title="空文档")

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_markdown_to_docx_bytes_special_chars(self, service):
        """测试特殊字符Markdown转Word字节"""
        markdown = """# 中文标题

这是中文内容，包含特殊字符：？！；：「」『』【】（）〔〕

- 项目1
- 项目2
"""
        result = service.markdown_to_docx_bytes(markdown, title="中文测试")

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_markdown_to_docx_file(self, service, tmp_path):
        """测试保存Word文件"""
        markdown = "# 测试文件\n\n这是一个测试。"
        output_path = tmp_path / "test.docx"

        service.markdown_to_docx_file(
            markdown=markdown,
            output_path=str(output_path),
            title="测试文件"
        )

        assert output_path.exists()
        assert output_path.stat().st_size > 0


class TestMarkdownElement:
    """Markdown元素测试类"""

    def test_create_element(self):
        """测试创建元素"""
        element = MarkdownElement(
            type="heading",
            level=2,
            content="测试标题"
        )

        assert element.type == "heading"
        assert element.level == 2
        assert element.content == "测试标题"

    def test_element_defaults(self):
        """测试元素默认值"""
        element = MarkdownElement(type="paragraph")

        assert element.level == 1
        assert element.content == ""
        assert element.children is None
