"""
内容渲染服务测试
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.services.content_renderer_service import (
    ContentRendererService,
    render_lesson_plan_to_markdown,
    render_lesson_plan_to_html,
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


class TestContentRendererService:
    """内容渲染服务测试"""

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
                    {"word": "comprehension", "definition": "理解", "example": "Reading comprehension is important."},
                    {"word": "skim", "definition": "略读", "example": "Skim the passage first."},
                ],
                "phrases": ["figure out", "in terms of"],
            },
            grammar_points={
                "points": [
                    {
                        "name": "定语从句",
                        "explanation": "用来修饰名词的从句",
                        "examples": ["The book that I read yesterday was interesting.", "This is the place where we met."],
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
                "intermediate": {"title": "中等材料", "content": "This passage discusses the importance of reading in language learning."},
                "advanced": {"title": "进阶材料", "content": "While the significance of reading comprehension cannot be overstated, it is equally crucial to develop critical thinking skills when analyzing complex texts."},
            },
            exercises={
                "type": "阅读理解",
                "items": [
                    {"question": "What is the main idea of the passage?", "options": ["A", "B", "C", "D"], "answer": "A"},
                    {"question": "According to the author, reading helps to?", "options": ["A", "B", "C", "D"], "answer": "C"},
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

    def test_init_valid_format(self):
        """测试有效格式初始化"""
        md_service = ContentRendererService(format="markdown")
        assert md_service.format == "markdown"

        html_service = ContentRendererService(format="html")
        assert html_service.format == "html"

    def test_init_invalid_format(self):
        """测试无效格式初始化"""
        with pytest.raises(ValueError):
            ContentRendererService(format="pdf")

    def test_render_metadata_markdown(self):
        """测试渲染元数据（Markdown格式）"""
        lesson_plan = MockLessonPlan()
        service = ContentRendererService(format="markdown")

        result = service._render_metadata(lesson_plan)

        assert "## 教案信息" in result
        assert "### 标题" in result
        assert "测试教案" in result
        assert "### 主题" in result
        assert "英语学习" in result
        assert "### 等级" in result
        assert "B1" in result

    def test_render_objectives_with_data(self):
        """测试渲染教学目标（有数据）"""
        lesson_plan = MockLessonPlan(
            objectives={
                "overall": "掌握阅读技巧",
                "specific": ["理解文章结构", "提高速度"],
                "outcomes": ["考试得分提升"],
            }
        )
        service = ContentRendererService(format="markdown")

        result = service._render_objectives(lesson_plan.objectives)

        assert result is not None
        assert "## 教学目标" in result
        assert "总体目标" in result or "掌握阅读技巧" in result

    def test_render_objectives_empty(self):
        """测试渲染教学目标（空数据）"""
        service = ContentRendererService(format="markdown")

        result = service._render_objectives(None)
        assert result is None

        result = service._render_objectives({})
        assert result is None

    def test_render_vocabulary(self):
        """测试渲染词汇"""
        lesson_plan = MockLessonPlan(
            vocabulary={
                "words": [
                    {"word": "test", "definition": "测试", "example": "This is a test."},
                ],
                "phrases": ["test phrase"],
            }
        )
        service = ContentRendererService(format="markdown")

        result = service._render_vocabulary(lesson_plan.vocabulary)

        assert result is not None
        assert "## 核心词汇" in result

    def test_render_grammar_points(self):
        """测试渲染语法点"""
        lesson_plan = MockLessonPlan(
            grammar_points={
                "points": [
                    {
                        "name": "时态",
                        "explanation": "描述动作发生的时间",
                        "examples": ["I eat breakfast every day.", "I ate breakfast yesterday."],
                    }
                ]
            }
        )
        service = ContentRendererService(format="markdown")

        result = service._render_grammar_points(lesson_plan.grammar_points)

        assert result is not None
        assert "## 语法点" in result

    def test_render_teaching_structure(self):
        """测试渲染教学流程"""
        lesson_plan = MockLessonPlan(
            teaching_structure={
                "stages": [
                    {"name": "导入", "duration": 5, "activities": ["提问"]},
                    {"name": "讲解", "duration": 20, "activities": ["讲解技巧"]},
                ],
                "total_duration": 25,
            }
        )
        service = ContentRendererService(format="markdown")

        result = service._render_teaching_structure(lesson_plan.teaching_structure)

        assert result is not None
        assert "## 教学流程" in result

    def test_render_leveled_materials(self):
        """测试渲染分层材料"""
        lesson_plan = MockLessonPlan(
            leveled_materials={
                "basic": {"title": "基础", "content": "Basic content."},
                "advanced": {"title": "进阶", "content": "Advanced content for skilled readers."},
            }
        )
        service = ContentRendererService(format="markdown")

        result = service._render_leveled_materials(lesson_plan.leveled_materials)

        assert result is not None
        assert "## 分层阅读材料" in result

    def test_render_exercises(self):
        """测试渲染练习"""
        lesson_plan = MockLessonPlan(
            exercises={
                "items": [
                    {"question": "What is X?", "options": ["A", "B"], "answer": "A"},
                ]
            }
        )
        service = ContentRendererService(format="markdown")

        result = service._render_exercises(lesson_plan.exercises)

        assert result is not None
        assert "## 练习题" in result

    def test_render_ppt_outline(self):
        """测试渲染PPT大纲"""
        lesson_plan = MockLessonPlan(
            ppt_outline={
                "slides": [
                    {"title": "Slide 1", "bullet_points": ["Point 1", "Point 2"]},
                ],
                "total_slides": 3,
            }
        )
        service = ContentRendererService(format="markdown")

        result = service._render_ppt_outline(lesson_plan.ppt_outline)

        assert result is not None
        assert "## PPT大纲" in result

    def test_render_resources(self):
        """测试渲染资源"""
        lesson_plan = MockLessonPlan(
            resources={
                "links": ["https://example.com"],
                "attachments": ["file.pdf"],
            }
        )
        service = ContentRendererService(format="markdown")

        result = service._render_resources(lesson_plan.resources)

        assert result is not None
        assert "## 教学资源" in result

    def test_render_teaching_notes(self):
        """测试渲染教学反思"""
        lesson_plan = MockLessonPlan(teaching_notes="Good lesson!")
        service = ContentRendererService(format="markdown")

        result = service._render_teaching_notes(lesson_plan.teaching_notes)

        assert result is not None
        assert "## 教学反思" in result
        assert "Good lesson!" in result

    def test_render_lesson_plan_complete(self):
        """测试渲染完整教案"""
        service = ContentRendererService(format="markdown")

        lesson_plan = MockLessonPlan(
            title="完整教案",
            objectives={"overall": "目标"},
            vocabulary={"words": [{"word": "test", "definition": "测试"}]},
        )

        result = service.render_lesson_plan(lesson_plan)

        assert "# 教案信息" in result
        assert "## 教学目标" in result
        assert "## 核心词汇" in result

    def test_render_lesson_plan_with_sections_filter(self):
        """测试按章节过滤渲染"""
        service = ContentRendererService(format="markdown")

        lesson_plan = MockLessonPlan(
            objectives={"overall": "目标"},
            vocabulary={"words": [{"word": "test", "definition": "测试"}]},
        )

        result = service.render_lesson_plan(
            lesson_plan, include_sections=["metadata", "vocabulary"]
        )

        assert "# 教案信息" in result
        assert "## 核心词汇" in result
        assert "## 教学目标" not in result

    def test_html_format_output(self):
        """测试HTML格式输出"""
        lesson_plan = MockLessonPlan(title="HTML测试")
        service = ContentRendererService(format="html")

        result = service.render_lesson_plan(lesson_plan)

        assert "<section" in result
        assert "<h2>" in result
        assert lesson_plan.title in result

    def test_format_datetime(self):
        """测试日期时间格式化"""
        service = ContentRendererService(format="markdown")

        # 测试 None
        result = service._format_datetime(None)
        assert result == ""

        # 测试带时区的 datetime
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = service._format_datetime(dt)
        assert "2024-01-15" in result

    def test_convenience_functions(self):
        """测试模块级便捷函数"""
        lesson_plan = MockLessonPlan(title="便捷函数测试")

        # Markdown 渲染
        md_result = render_lesson_plan_to_markdown(lesson_plan)
        assert isinstance(md_result, str)
        assert "## 教案信息" in md_result

        # HTML 渲染
        html_result = render_lesson_plan_to_html(lesson_plan)
        assert isinstance(html_result, str)
        assert "<section" in html_result


class TestContentRendererServiceEdgeCases:
    """内容渲染服务边界情况测试"""

    def test_empty_vocabulary_format(self):
        """测试空词汇格式"""
        lesson_plan = MockLessonPlan(vocabulary={})
        service = ContentRendererService(format="markdown")

        result = service._render_vocabulary(lesson_plan.vocabulary)
        assert result is None

    def test_empty_exercises(self):
        """测试空练习"""
        lesson_plan = MockLessonPlan(exercises={})
        service = ContentRendererService(format="markdown")

        result = service._render_exercises(lesson_plan.exercises)
        assert result is None

    def test_unicode_content(self):
        """测试Unicode内容"""
        lesson_plan = MockLessonPlan(
            vocabulary={
                "words": [
                    {"word": "你好", "definition": "hello", "example": "你好吗？"},
                ]
            }
        )
        service = ContentRendererService(format="markdown")

        result = service._render_vocabulary(lesson_plan.vocabulary)
        assert result is not None
        assert "你好" in result

    def test_long_content_truncation(self):
        """测试长内容截断"""
        long_content = "A" * 1000
        lesson_plan = MockLessonPlan(
            leveled_materials={
                "basic": {"title": "基础", "content": long_content}
            }
        )
        service = ContentRendererService(format="markdown")

        result = service._render_leveled_materials(lesson_plan.leveled_materials)
        assert result is not None
        # 应该包含截断标记
        assert "..." in result
