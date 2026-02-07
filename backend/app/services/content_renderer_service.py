"""
内容渲染服务 - AI英语教学系统
将教案数据渲染为结构化输出，支持多种导出格式
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.models.lesson_plan import LessonPlan

logger = logging.getLogger(__name__)


class ContentRendererService:
    """
    内容渲染服务

    将 LessonPlan 数据转换为可用于导出的结构化内容。
    支持 Markdown 和 HTML 格式输出。

    核心功能：
    1. 渲染教案基本信息
    2. 渲染教学目标
    3. 渲染核心词汇
    4. 渲染语法点
    5. 渲染教学流程
    6. 渲染分层阅读材料
    7. 渲染练习题
    8. 渲染 PPT 大纲
    9. 渲染教学反思
    """

    def __init__(self, format: str = "markdown"):
        """
        初始化内容渲染服务

        Args:
            format: 输出格式 ("markdown" | "html")
        """
        self.format = format.lower()
        if self.format not in ("markdown", "html"):
            raise ValueError(f"Unsupported format: {format}. Supported: markdown, html")

    def render_lesson_plan(
        self,
        lesson_plan: LessonPlan,
        include_sections: Optional[List[str]] = None,
    ) -> str:
        """
        渲染完整教案

        Args:
            lesson_plan: 教案数据模型
            include_sections: 要包含的章节列表（None 表示全部）

        Returns:
            str: 渲染后的内容
        """
        sections = []

        # 默认包含所有章节
        if include_sections is None:
            include_sections = [
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

        # 按顺序渲染各章节
        for section in include_sections:
            if section == "metadata":
                sections.append(self._render_metadata(lesson_plan))
            elif section == "objectives":
                content = self._render_objectives(lesson_plan.objectives)
                if content:
                    sections.append(content)
            elif section == "vocabulary":
                content = self._render_vocabulary(lesson_plan.vocabulary)
                if content:
                    sections.append(content)
            elif section == "grammar":
                content = self._render_grammar_points(lesson_plan.grammar_points)
                if content:
                    sections.append(content)
            elif section == "teaching_structure":
                content = self._render_teaching_structure(lesson_plan.teaching_structure)
                if content:
                    sections.append(content)
            elif section == "leveled_materials":
                content = self._render_leveled_materials(lesson_plan.leveled_materials)
                if content:
                    sections.append(content)
            elif section == "exercises":
                content = self._render_exercises(lesson_plan.exercises)
                if content:
                    sections.append(content)
            elif section == "ppt_outline":
                content = self._render_ppt_outline(lesson_plan.ppt_outline)
                if content:
                    sections.append(content)
            elif section == "resources":
                content = self._render_resources(lesson_plan.resources)
                if content:
                    sections.append(content)
            elif section == "teaching_notes":
                content = self._render_teaching_notes(lesson_plan.teaching_notes)
                if content:
                    sections.append(content)

        return self._join_sections(sections)

    def _render_metadata(self, lesson_plan: LessonPlan) -> str:
        """渲染教案元数据"""
        data = {
            "标题": lesson_plan.title,
            "主题": lesson_plan.topic,
            "等级": lesson_plan.level,
            "时长": f"{lesson_plan.duration} 分钟",
            "目标考试": lesson_plan.target_exam or "无",
            "创建时间": self._format_datetime(lesson_plan.created_at),
        }
        return self._render_section("教案信息", data)

    def _render_objectives(self, objectives: Optional[Dict[str, Any]]) -> Optional[str]:
        """渲染教学目标"""
        if not objectives:
            return None

        data = {}

        # 提取各层级目标
        if "overall" in objectives:
            data["总体目标"] = objectives["overall"]
        if "specific" in objectives:
            if isinstance(objectives["specific"], list):
                data["具体目标"] = objectives["specific"]
            else:
                data["具体目标"] = [objectives["specific"]]
        if "outcomes" in objectives:
            if isinstance(objectives["outcomes"], list):
                data["学习成果"] = objectives["outcomes"]
            else:
                data["学习成果"] = [objectives["outcomes"]]

        return self._render_section("教学目标", data) if data else None

    def _render_vocabulary(self, vocabulary: Optional[Dict[str, Any]]) -> Optional[str]:
        """渲染核心词汇"""
        if not vocabulary:
            return None

        data = {}

        if "words" in vocabulary:
            words_data = vocabulary["words"]
            if isinstance(words_data, list):
                # 格式: [{"word": "xxx", "definition": "xxx", "example": "xxx"}, ...]
                formatted_words = []
                for item in words_data:
                    if isinstance(item, dict):
                        word_entry = item.get("word", "")
                        if "definition" in item:
                            word_entry += f" - {item['definition']}"
                        if "example" in item and item["example"]:
                            word_entry += f"\n  例句: {item['example']}"
                        formatted_words.append(word_entry)
                    else:
                        formatted_words.append(str(item))
                data["核心词汇"] = formatted_words
            else:
                data["核心词汇"] = [str(words_data)]

        if "phrases" in vocabulary:
            phrases = vocabulary["phrases"]
            if isinstance(phrases, list):
                data["短语"] = [str(p) for p in phrases]
            else:
                data["短语"] = [str(phrases)]

        return self._render_section("核心词汇", data) if data else None

    def _render_grammar_points(
        self, grammar_points: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """渲染语法点"""
        if not grammar_points:
            return None

        data = {}

        if "points" in grammar_points:
            points = grammar_points["points"]
            if isinstance(points, list):
                formatted_points = []
                for point in points:
                    if isinstance(point, dict):
                        entry = point.get("name", "")
                        if "explanation" in point:
                            entry += f"\n  说明: {point['explanation']}"
                        if "examples" in point and isinstance(point["examples"], list):
                            entry += "\n  例句:"
                            for ex in point["examples"][:3]:  # 最多3个例句
                                entry += f"\n    - {ex}"
                        formatted_points.append(entry)
                    else:
                        formatted_points.append(str(point))
                data["语法点"] = formatted_points
            else:
                data["语法点"] = [str(points)]

        return self._render_section("语法点", data) if data else None

    def _render_teaching_structure(
        self, teaching_structure: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """渲染教学流程"""
        if not teaching_structure:
            return None

        data = {}

        if "stages" in teaching_structure:
            stages = teaching_structure["stages"]
            if isinstance(stages, list):
                formatted_stages = []
                for stage in stages:
                    if isinstance(stage, dict):
                        entry = stage.get("name", stage.get("stage", ""))
                        if "duration" in stage:
                            entry += f" ({stage['duration']}分钟)"
                        if "activities" in stage:
                            activities = stage["activities"]
                            if isinstance(activities, list):
                                entry += "\n  活动:"
                                for act in activities:
                                    entry += f"\n    - {act}"
                            else:
                                entry += f"\n  活动: {activities}"
                        formatted_stages.append(entry)
                    else:
                        formatted_stages.append(str(stage))
                data["教学流程"] = formatted_stages
            else:
                data["教学流程"] = [str(stages)]

        if "total_duration" in teaching_structure:
            data["总时长"] = f"{teaching_structure['total_duration']}分钟"

        return self._render_section("教学流程", data) if data else None

    def _render_leveled_materials(
        self, leveled_materials: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """渲染分层阅读材料"""
        if not leveled_materials:
            return None

        data = {}

        # 处理不同难度的材料
        levels = ["basic", "intermediate", "advanced"]
        level_names = {"basic": "基础材料", "intermediate": "中等材料", "advanced": "进阶材料"}

        for level in levels:
            if level in leveled_materials:
                material = leveled_materials[level]
                if isinstance(material, dict):
                    title = material.get("title", level_names.get(level, level))
                    content = material.get("content", "")
                    if content:
                        data[title] = content[:500] + "..." if len(content) > 500 else content
                elif isinstance(material, str):
                    data[level_names.get(level, level)] = material[:500] + "..." if len(material) > 500 else material

        return self._render_section("分层阅读材料", data) if data else None

    def _render_exercises(self, exercises: Optional[Dict[str, Any]]) -> Optional[str]:
        """渲染练习题"""
        if not exercises:
            return None

        data = {}

        if "items" in exercises:
            items = exercises["items"]
            if isinstance(items, list):
                formatted_items = []
                for i, item in enumerate(items, 1):
                    if isinstance(item, dict):
                        entry = f"{i}. {item.get('question', '')}"
                        if "options" in item and isinstance(item["options"], list):
                            for opt in item["options"]:
                                entry += f"\n   {opt}"
                        if "answer" in item:
                            entry += f"\n   答案: {item['answer']}"
                        formatted_items.append(entry)
                    else:
                        formatted_items.append(f"{i}. {item}")
                data["练习题"] = formatted_items
            else:
                data["练习题"] = [str(items)]

        if "type" in exercises:
            data["题型"] = exercises["type"]

        return self._render_section("练习题", data) if data else None

    def _render_ppt_outline(
        self, ppt_outline: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """渲染 PPT 大纲"""
        if not ppt_outline:
            return None

        data = {}

        if "slides" in ppt_outline:
            slides = ppt_outline["slides"]
            if isinstance(slides, list):
                formatted_slides = []
                for i, slide in enumerate(slides, 1):
                    if isinstance(slide, dict):
                        entry = f"第{i}页: {slide.get('title', '')}"
                        if "bullet_points" in slide:
                            bullets = slide["bullet_points"]
                            if isinstance(bullets, list):
                                for bullet in bullets[:5]:  # 最多5个要点
                                    entry += f"\n  - {bullet}"
                            else:
                                entry += f"\n  - {bullets}"
                        formatted_slides.append(entry)
                    else:
                        formatted_slides.append(f"第{i}页: {slide}")
                data["PPT大纲"] = formatted_slides
            else:
                data["PPT大纲"] = [str(slides)]

        if "total_slides" in ppt_outline:
            data["总页数"] = str(ppt_outline["total_slides"])

        return self._render_section("PPT大纲", data) if data else None

    def _render_resources(self, resources: Optional[Dict[str, Any]]) -> Optional[str]:
        """渲染资源列表"""
        if not resources:
            return None

        data = {}

        if "links" in resources:
            links = resources["links"]
            if isinstance(links, list):
                data["相关链接"] = [str(link) for link in links]
            else:
                data["相关链接"] = [str(links)]

        if "attachments" in resources:
            attachments = resources["attachments"]
            if isinstance(attachments, list):
                data["附件"] = [str(att) for att in attachments]
            else:
                data["附件"] = [str(attachments)]

        if "references" in resources:
            refs = resources["references"]
            if isinstance(refs, list):
                data["参考资料"] = [str(ref) for ref in refs]
            else:
                data["参考资料"] = [str(refs)]

        return self._render_section("教学资源", data) if data else None

    def _render_teaching_notes(self, teaching_notes: Optional[str]) -> Optional[str]:
        """渲染教学反思"""
        if not teaching_notes:
            return None

        return self._render_section("教学反思", {"反思内容": teaching_notes})

    def _render_section(self, title: str, content: Dict[str, Any]) -> str:
        """
        渲染单个章节

        Args:
            title: 章节标题
            content: 字典格式的内容

        Returns:
            str: 渲染后的章节内容
        """
        if self.format == "markdown":
            return self._render_section_markdown(title, content)
        else:
            return self._render_section_html(title, content)

    def _render_section_markdown(self, title: str, content: Dict[str, Any]) -> str:
        """Markdown 格式渲染"""
        lines = [f"## {title}", ""]

        for key, value in content.items():
            if isinstance(value, list):
                lines.append(f"### {key}")
                for item in value:
                    if "\n" in item:
                        # 多行内容
                        for line in item.split("\n"):
                            lines.append(f"  {line}")
                    else:
                        lines.append(f"- {item}")
                lines.append("")
            else:
                lines.append(f"### {key}")
                lines.append(str(value))
                lines.append("")

        return "\n".join(lines)

    def _render_section_html(self, title: str, content: Dict[str, Any]) -> str:
        """HTML 格式渲染"""
        lines = [f'<section class="section">', f'<h2>{title}</h2>']

        for key, value in content.items():
            lines.append(f"<h3>{key}</h3>")
            if isinstance(value, list):
                lines.append("<ul>")
                for item in value:
                    if "\n" in item:
                        # 多行内容需要处理
                        clean_item = item.replace("\n", "<br/>")
                        lines.append(f"<li>{clean_item}</li>")
                    else:
                        lines.append(f"<li>{item}</li>")
                lines.append("</ul>")
            else:
                lines.append(f"<p>{value}</p>")

        lines.append("</section>")
        return "\n".join(lines)

    def _join_sections(self, sections: List[str]) -> str:
        """合并多个章节"""
        if self.format == "markdown":
            return "\n\n".join(sections)
        else:
            return "\n".join(sections)

    def _format_datetime(self, dt: Optional[datetime]) -> str:
        """格式化日期时间"""
        if dt is None:
            return ""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

    def render_to_html(self, markdown_content: str) -> str:
        """
        将 Markdown 内容转换为 HTML（用于 HTML 格式输出）

        Args:
            markdown_content: Markdown 格式的内容

        Returns:
            str: HTML 格式的内容
        """
        # 简单的 Markdown 转 HTML 转换
        html = markdown_content

        # 标题
        html = html.replace("\n## ", "</section>\n<section><h2>")
        html = html.replace("\n### ", "</p>\n<p><strong>")

        # 列表
        html = html.replace("\n- ", "</li>\n<li>")
        html = html.replace("<ul>", "<ul>\n<li>").replace("</ul>", "</li>\n</ul>")

        # 换行
        html = html.replace("\n\n", "</p>\n<p>")
        html = html.replace("\n", "<br/>")

        return f'<div class="content">\n<p>{html}</p>\n</div>'


# ========== 模块级便捷函数 ==========

def render_lesson_plan_to_markdown(
    lesson_plan: LessonPlan,
    include_sections: Optional[List[str]] = None,
) -> str:
    """
    渲染教案为 Markdown 格式

    Args:
        lesson_plan: 教案数据模型
        include_sections: 要包含的章节列表

    Returns:
        str: Markdown 格式的内容
    """
    renderer = ContentRendererService(format="markdown")
    return renderer.render_lesson_plan(lesson_plan, include_sections)


def render_lesson_plan_to_html(
    lesson_plan: LessonPlan,
    include_sections: Optional[List[str]] = None,
) -> str:
    """
    渲染教案为 HTML 格式

    Args:
        lesson_plan: 教案数据模型
        include_sections: 要包含的章节列表

    Returns:
        str: HTML 格式的内容
    """
    renderer = ContentRendererService(format="html")
    return renderer.render_lesson_plan(lesson_plan, include_sections)
