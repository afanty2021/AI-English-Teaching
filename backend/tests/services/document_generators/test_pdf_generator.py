"""
PDF文档生成器测试
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.services.document_generators.pdf_generator import (
    PDFDocumentGenerator,
    get_pdf_generator,
)


class MockLessonPlan:
    """模拟教案对象用于测试"""

    def __init__(
        self,
        id=None,
        title="测试教案",
        topic="英语学习",
        level="B1",
        duration=45,
        target_exam="CET4",
        created_at=None,
        objectives=None,
        vocabulary=None,
        grammar_points=None,
        teaching_structure=None,
        leveled_materials=None,
        exercises=None,
        ppt_outline=None,
        resources=None,
        teaching_notes=None,
    ):
        self.id = id or uuid4()
        self.title = title
        self.topic = topic
        self.level = level
        self.duration = duration
        self.target_exam = target_exam
        self.created_at = created_at or datetime.now(timezone.utc)
        self.objectives = objectives
        self.vocabulary = vocabulary
        self.grammar_points = grammar_points
        self.teaching_structure = teaching_structure
        self.leveled_materials = leveled_materials
        self.exercises = exercises
        self.ppt_outline = ppt_outline
        self.resources = resources
        self.teaching_notes = teaching_notes


class TestPDFDocumentGenerator:
    """PDF文档生成器测试"""

    @pytest.fixture
    def generator(self):
        """创建PDF生成器实例"""
        return PDFDocumentGenerator()

    @pytest.fixture
    def sample_lesson_plan(self):
        """创建测试用教案对象"""
        return MockLessonPlan(
            title="英语阅读理解技巧",
            topic="阅读技巧",
            level="B2",
            duration=60,
            target_exam="CET6",
            objectives={
                "overall": "掌握英语阅读理解的基本技巧",
                "specific": ["理解文章主旨", "识别细节信息", "推断词义"],
                "outcomes": ["能够快速定位关键信息", "提高阅读速度"],
            },
            vocabulary={
                "words": [
                    {
                        "word": "comprehension",
                        "definition": "理解",
                        "example": "Reading comprehension is important.",
                    },
                    {"word": "skim", "definition": "略读", "example": "Skim the passage first."},
                ],
                "phrases": ["figure out", "in terms of"],
            },
            grammar_points={
                "points": [
                    {
                        "name": "定语从句",
                        "explanation": "用来修饰名词的从句",
                        "examples": [
                            "The book that I read yesterday was interesting.",
                            "This is the place where we met.",
                        ],
                    },
                ]
            },
            teaching_structure={
                "stages": [
                    {"name": "导入", "duration": 5, "activities": ["提问导入", "图片展示"]},
                    {"name": "讲解", "duration": 20, "activities": ["技巧讲解", "例句分析"]},
                    {"name": "练习", "duration": 25, "activities": ["小组讨论", "个人练习"]},
                    {"name": "总结", "duration": 10, "activities": ["要点回顾"]},
                ],
                "total_duration": 60,
            },
            leveled_materials={
                "basic": {"title": "基础材料", "content": "This is a simple text for beginners."},
                "intermediate": {
                    "title": "中等材料",
                    "content": "This passage discusses the importance of reading in language learning.",
                },
                "advanced": {
                    "title": "进阶材料",
                    "content": "While the significance of reading comprehension cannot be overstated, it is equally crucial to develop critical thinking skills when analyzing complex texts.",
                },
            },
            exercises={
                "type": "阅读理解",
                "items": [
                    {
                        "question": "What is the main idea of the passage?",
                        "options": ["A", "B", "C", "D"],
                        "answer": "A",
                    },
                    {
                        "question": "According to the author, reading helps to?",
                        "options": ["A", "B", "C", "D"],
                        "answer": "C",
                    },
                ],
            },
            ppt_outline={
                "slides": [
                    {"title": "课程导入", "bullet_points": ["阅读的重要性", "本课目标"]},
                    {"title": "阅读技巧", "bullet_points": ["略读", "扫读", "精读"]},
                    {"title": "练习", "bullet_points": ["小组活动", "个人练习"]},
                ],
                "total_slides": 5,
            },
            resources={
                "links": ["https://example.com/reading-tips"],
                "attachments": ["reading_materials.pdf"],
                "references": ["《英语阅读教学指南》"],
            },
            teaching_notes="学生反应积极，建议增加更多练习时间。",
        )

    def test_init(self, generator):
        """测试初始化"""
        assert generator is not None
        assert generator.pdf_service is not None
        assert generator.content_service is not None

    def test_supported_sections(self, generator):
        """测试支持的章节列表"""
        expected_sections = [
            "metadata",
            "objectives",
            "vocabulary",
            "grammar",
            "teaching_structure",
            "leveled_materials",
            "exercises",
            "ppt_outline",
            "resources",
            "teaching_notes",
        ]
        assert generator.SUPPORTED_SECTIONS == expected_sections

    @pytest.mark.asyncio
    async def test_generate_from_lesson_plan_basic(self, generator, sample_lesson_plan):
        """测试从教案生成PDF（基本功能）"""
        pdf_bytes = await generator.generate_from_lesson_plan(sample_lesson_plan)

        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # PDF文件以%PDF开头
        assert pdf_bytes.startswith(b"%PDF")

    @pytest.mark.asyncio
    async def test_generate_from_lesson_plan_with_sections_filter(
        self, generator, sample_lesson_plan
    ):
        """测试从教案生成PDF（章节过滤）"""
        pdf_bytes = await generator.generate_from_lesson_plan(
            sample_lesson_plan,
            include_sections=["metadata", "objectives", "vocabulary"],
        )

        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    @pytest.mark.asyncio
    async def test_generate_from_lesson_plan_empty_title_raises(self, generator):
        """测试空标题教案抛出异常"""
        empty_plan = MockLessonPlan(title="")

        with pytest.raises(ValueError, match="教案标题不能为空"):
            await generator.generate_from_lesson_plan(empty_plan)

    @pytest.mark.asyncio
    async def test_generate_from_lesson_plan_invalid_sections_raises(
        self, generator, sample_lesson_plan
    ):
        """测试无效章节抛出异常"""
        with pytest.raises(ValueError, match="不支持的章节"):
            await generator.generate_from_lesson_plan(
                sample_lesson_plan,
                include_sections=["metadata", "invalid_section"],
            )

    @pytest.mark.asyncio
    async def test_generate_from_dict_content(self, generator):
        """测试从字典内容生成PDF"""
        content = {
            "title": "测试教案",
            "level": "B1",
            "topic": "英语语法",
            "duration": 45,
            "objectives": {
                "overall": "掌握基本语法",
                "specific": ["理解时态", "正确使用动词"],
            },
            "vocabulary": {
                "words": [
                    {"word": "test", "definition": "测试", "example": "This is a test."},
                ]
            },
        }

        pdf_bytes = await generator.generate(content)

        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    @pytest.mark.asyncio
    async def test_generate_with_template_vars(self, generator):
        """测试带模板变量的PDF生成"""
        content = {
            "title": "测试教案",
            "level": "B1",
            "topic": "英语语法",
            "duration": 45,
        }

        template_vars = {
            "teacher_name": "张老师",
            "school": "XX中学",
            "date": "2026-02-07",
        }

        pdf_bytes = await generator.generate(content, template_vars)

        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    @pytest.mark.asyncio
    async def test_generate_empty_title_raises(self, generator):
        """测试空标题内容抛出异常"""
        content = {"level": "B1", "topic": "英语"}

        with pytest.raises(ValueError, match="教案标题不能为空"):
            await generator.generate(content)

    def test_render_to_markdown_basic(self, generator):
        """测试Markdown渲染（基本功能）"""
        content = {
            "title": "测试教案",
            "level": "B1",
            "topic": "英语",
            "duration": 45,
        }

        markdown = generator._render_to_markdown(content)

        assert "# 测试教案" in markdown
        assert "## 基本信息" in markdown
        assert "等级" in markdown
        assert "B1" in markdown

    def test_render_objectives_markdown(self, generator):
        """测试教学目标Markdown渲染"""
        objectives = {
            "overall": "掌握阅读技巧",
            "specific": ["理解文章结构", "提高速度"],
        }

        markdown_lines = generator._render_objectives_markdown(objectives)
        markdown = "\n".join(markdown_lines)

        assert "## 教学目标" in markdown
        assert "掌握阅读技巧" in markdown or "理解文章结构" in markdown

    def test_render_vocabulary_markdown(self, generator):
        """测试词汇Markdown渲染"""
        vocabulary = {
            "words": [
                {"word": "test", "definition": "测试", "example": "This is a test."},
            ],
            "phrases": ["test phrase"],
        }

        markdown_lines = generator._render_vocabulary_markdown(vocabulary)
        markdown = "\n".join(markdown_lines)

        assert "## 核心词汇" in markdown
        assert "test" in markdown
        assert "短语" in markdown

    def test_render_grammar_markdown(self, generator):
        """测试语法点Markdown渲染"""
        grammar_points = {
            "points": [
                {
                    "name": "时态",
                    "explanation": "描述动作发生的时间",
                    "examples": ["I eat breakfast every day."],
                }
            ]
        }

        markdown_lines = generator._render_grammar_markdown(grammar_points)
        markdown = "\n".join(markdown_lines)

        assert "## 语法点" in markdown
        assert "时态" in markdown

    def test_render_teaching_structure_markdown(self, generator):
        """测试教学流程Markdown渲染"""
        structure = {
            "stages": [
                {"name": "导入", "duration": 5, "activities": ["提问"]},
            ],
            "total_duration": 60,
        }

        markdown_lines = generator._render_teaching_structure_markdown(structure)
        markdown = "\n".join(markdown_lines)

        assert "## 教学流程" in markdown
        assert "导入" in markdown
        assert "60" in markdown

    def test_render_leveled_materials_markdown(self, generator):
        """测试分层材料Markdown渲染"""
        materials = {
            "basic": {"title": "基础材料", "content": "Basic content."},
            "advanced": {"title": "进阶材料", "content": "Advanced content."},
        }

        markdown_lines = generator._render_leveled_materials_markdown(materials)
        markdown = "\n".join(markdown_lines)

        assert "## 分层阅读材料" in markdown
        assert "基础材料" in markdown or "进阶材料" in markdown

    def test_render_exercises_markdown(self, generator):
        """测试练习题Markdown渲染"""
        exercises = {
            "items": [
                {"question": "What is X?", "options": ["A", "B"], "answer": "A"},
            ]
        }

        markdown_lines = generator._render_exercises_markdown(exercises)
        markdown = "\n".join(markdown_lines)

        assert "## 练习题" in markdown
        assert "What is X?" in markdown

    def test_render_ppt_outline_markdown(self, generator):
        """测试PPT大纲Markdown渲染"""
        ppt_outline = {
            "slides": [
                {"title": "Slide 1", "bullet_points": ["Point 1", "Point 2"]},
            ],
            "total_slides": 3,
        }

        markdown_lines = generator._render_ppt_outline_markdown(ppt_outline)
        markdown = "\n".join(markdown_lines)

        assert "## PPT大纲" in markdown
        assert "Slide 1" in markdown

    def test_render_to_markdown_with_all_sections(self, generator):
        """测试完整内容的Markdown渲染"""
        content = {
            "title": "完整教案",
            "level": "B2",
            "topic": "英语阅读",
            "duration": 60,
            "objectives": {"overall": "掌握阅读技巧"},
            "vocabulary": {"words": [{"word": "test", "definition": "测试"}]},
            "grammar_points": {"points": [{"name": "时态", "explanation": "时间描述"}]},
            "teaching_structure": {"stages": [{"name": "导入", "duration": 5}]},
            "leveled_materials": {"basic": {"title": "基础", "content": "Basic"}},
            "exercises": {"items": [{"question": "Test?"}]},
            "ppt_outline": {"slides": [{"title": "Slide 1"}]},
            "teaching_notes": "Good lesson!",
        }

        markdown = generator._render_to_markdown(content)

        assert "# 完整教案" in markdown
        assert "## 教学目标" in markdown
        assert "## 核心词汇" in markdown
        assert "## 语法点" in markdown
        assert "## 教学流程" in markdown
        assert "## 分层阅读材料" in markdown
        assert "## 练习题" in markdown
        assert "## PPT大纲" in markdown
        assert "## 教学反思" in markdown


class TestPDFDocumentGeneratorChineseContent:
    """PDF文档生成器中文内容测试"""

    @pytest.fixture
    def generator(self):
        """创建PDF生成器实例"""
        return PDFDocumentGenerator()

    @pytest.mark.asyncio
    async def test_chinese_content_pdf_generation(self, generator):
        """测试中文内容PDF生成"""
        lesson_plan = MockLessonPlan(
            title="英语阅读理解技巧",
            topic="阅读技巧",
            level="B2",
            vocabulary={
                "words": [
                    {"word": "阅读", "definition": "reading", "example": "我喜欢阅读英语文章。"},
                ]
            },
            teaching_notes="学生反应积极，中文显示正常。",
        )

        pdf_bytes = await generator.generate_from_lesson_plan(lesson_plan)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0

    def test_chinese_markdown_rendering(self, generator):
        """测试中文Markdown渲染"""
        content = {
            "title": "中文教案标题",
            "level": "B1",
            "topic": "英语教学",
            "duration": 45,
            "objectives": {"overall": "掌握基础英语对话"},
            "vocabulary": {
                "words": [
                    {"word": "你好", "definition": "hello", "example": "你好，很高兴见到你。"},
                ]
            },
            "teaching_notes": "教学反思：学生表现良好",
        }

        markdown = generator._render_to_markdown(content)

        assert "# 中文教案标题" in markdown
        assert "你好" in markdown
        assert "教学反思" in markdown


class TestPDFDocumentGeneratorEdgeCases:
    """PDF文档生成器边界情况测试"""

    @pytest.fixture
    def generator(self):
        """创建PDF生成器实例"""
        return PDFDocumentGenerator()

    def test_render_empty_objectives(self, generator):
        """测试空教学目标"""
        markdown = generator._render_objectives_markdown({})
        # 空字典应该仍然返回标题
        assert "## 教学目标" in markdown

    def test_render_empty_vocabulary(self, generator):
        """测试空词汇"""
        markdown = generator._render_vocabulary_markdown({})
        # 空字典应该仍然返回标题
        assert "## 核心词汇" in markdown

    def test_render_empty_exercises(self, generator):
        """测试空练习"""
        markdown = generator._render_exercises_markdown({})
        assert "## 练习题" in markdown

    def test_render_long_content_truncation(self, generator):
        """测试长内容截断"""
        long_content = "A" * 1000
        materials = {"basic": {"title": "基础", "content": long_content}}

        markdown_lines = generator._render_leveled_materials_markdown(materials)
        markdown = "\n".join(markdown_lines)

        # 应该包含截断标记
        assert "..." in markdown

    def test_minimal_content(self, generator):
        """测试最小内容"""
        content = {
            "title": "最小教案",
        }

        markdown = generator._render_to_markdown(content)

        assert "# 最小教案" in markdown
        assert "## 基本信息" in markdown


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_get_pdf_generator(self):
        """测试获取PDF生成器工厂函数"""
        generator = get_pdf_generator()

        assert generator is not None
        assert isinstance(generator, PDFDocumentGenerator)

    def test_get_pdf_generator_with_template_env(self):
        """测试带模板环境的工厂函数"""

        # 模拟模板环境
        class MockTemplateEnv:
            pass

        template_env = MockTemplateEnv()
        generator = get_pdf_generator(template_env)

        assert generator is not None
        assert isinstance(generator, PDFDocumentGenerator)
