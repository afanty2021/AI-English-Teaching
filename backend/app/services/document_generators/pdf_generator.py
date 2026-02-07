"""
PDF文档生成器 - AI英语教学系统

使用 markdown2 + weasyprint 将教案数据转换为 PDF 格式。
复用 PDFRendererService 和 ContentRendererService 实现教案导出。
"""

import logging
from typing import Any, Dict, List, Optional

from app.models.lesson_plan import LessonPlan
from app.services.content_renderer_service import ContentRendererService
from app.services.pdf_renderer_service import PdfRendererService

logger = logging.getLogger(__name__)


class PDFDocumentGenerator:
    """
    PDF 文档生成器

    将教案数据转换为格式化的 PDF 文档。

    功能：
    - 从 LessonPlan 模型直接生成 PDF
    - 从结构化内容生成 PDF
    - 支持章节过滤（选择性导出）
    - 完整的中文支持（通过 PDFRendererService）
    - 使用 markdown2 + weasyprint 渲染

    使用示例：
        ```python
        generator = PDFDocumentGenerator(template_env=jinja2_env)

        # 从 LessonPlan 生成
        pdf_bytes = await generator.generate_from_lesson_plan(
            lesson_plan,
            include_sections=["metadata", "objectives", "vocabulary"]
        )

        # 从结构化内容生成
        content = {"title": "教案标题", "level": "B1", ...}
        template_vars = {"teacher_name": "张老师"}
        pdf_bytes = await generator.generate(content, template_vars)
        ```
    """

    # 支持的章节列表
    SUPPORTED_SECTIONS = [
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

    def __init__(self, template_env=None):
        """
        初始化 PDF 文档生成器

        Args:
            template_env: Jinja2 模板环境（可选，传递给 PDFRendererService）
        """
        self.pdf_service = PdfRendererService(template_env=template_env)
        self.content_service = ContentRendererService(format="markdown")

    async def generate_from_lesson_plan(
        self,
        lesson_plan: LessonPlan,
        include_sections: Optional[List[str]] = None,
    ) -> bytes:
        """
        从 LessonPlan 直接生成 PDF

        Args:
            lesson_plan: 教案数据模型
            include_sections: 要包含的章节列表（None 表示全部）

        Returns:
            bytes: PDF 文档的二进制内容

        Raises:
            ValueError: 如果教案数据无效
            RuntimeError: 如果 PDF 生成失败
        """
        # 验证教案
        if not lesson_plan or not lesson_plan.title:
            raise ValueError("教案标题不能为空")

        # 验证章节列表
        if include_sections is not None:
            invalid_sections = set(include_sections) - set(self.SUPPORTED_SECTIONS)
            if invalid_sections:
                raise ValueError(
                    f"不支持的章节: {invalid_sections}. " f"支持的章节: {self.SUPPORTED_SECTIONS}"
                )

        try:
            # 使用 ContentRenderer 渲染为 Markdown
            markdown_content = self.content_service.render_lesson_plan(
                lesson_plan,
                include_sections=include_sections,
            )

            # 使用 PDFRenderer 转换为 PDF
            pdf_bytes = await self.pdf_service.render_markdown_to_pdf(
                markdown_content=markdown_content,
                title=lesson_plan.title,
                metadata={
                    "level": lesson_plan.level,
                    "topic": lesson_plan.topic,
                    "duration": lesson_plan.duration,
                },
            )

            logger.info(
                f"PDF生成成功: {lesson_plan.title} "
                f"({len(pdf_bytes)} bytes, 章节: {include_sections or '全部'})"
            )
            return pdf_bytes

        except Exception as e:
            logger.error(f"PDF生成失败: {e}")
            raise RuntimeError(f"PDF生成失败: {e}") from e

    async def generate(
        self,
        content: Dict[str, Any],
        template_vars: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        从结构化内容生成 PDF

        Args:
            content: 教案内容数据，包含以下字段：
                - title: 教案标题（必需）
                - level: CEFR等级
                - topic: 主题
                - duration: 课程时长（分钟）
                - target_exam: 目标考试（可选）
                - objectives: 教学目标（字典）
                - vocabulary: 词汇表（字典）
                - grammar_points: 语法点（列表）
                - teaching_structure: 教学流程（字典）
                - leveled_materials: 分层材料（列表）
                - exercises: 练习题（字典）
                - ppt_outline: PPT大纲（列表）
                - teaching_notes: 教学反思（可选）
            template_vars: 模板变量（可选），包含：
                - teacher_name: 教师姓名
                - school: 学校名称
                - date: 日期

        Returns:
            bytes: PDF 文档的二进制内容

        Raises:
            ValueError: 如果内容数据无效
            RuntimeError: 如果 PDF 生成失败
        """
        # 验证必要字段
        if not content.get("title"):
            raise ValueError("教案标题不能为空")

        try:
            # 渲染为 Markdown
            markdown_content = self._render_to_markdown(content, template_vars)

            # 转换为 PDF
            pdf_bytes = await self.pdf_service.render_markdown_to_pdf(
                markdown_content=markdown_content,
                title=content["title"],
                metadata=content,
            )

            logger.info(f"PDF生成成功: {content.get('title')} " f"({len(pdf_bytes)} bytes)")
            return pdf_bytes

        except Exception as e:
            logger.error(f"PDF生成失败: {e}")
            raise RuntimeError(f"PDF生成失败: {e}") from e

    def _render_to_markdown(
        self,
        content: Dict[str, Any],
        template_vars: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        将结构化内容渲染为 Markdown

        Args:
            content: 教案内容数据
            template_vars: 模板变量

        Returns:
            str: Markdown 格式的内容
        """
        lines = []

        # 标题
        lines.append(f"# {content.get('title', '教案')}")
        lines.append("")

        # 基本信息
        lines.append("## 基本信息")
        lines.append("")

        info_data = {
            "等级": content.get("level", ""),
            "主题": content.get("topic", ""),
            "时长": f"{content.get('duration', 0)} 分钟",
        }

        if content.get("target_exam"):
            info_data["目标考试"] = content["target_exam"]

        if template_vars:
            if template_vars.get("teacher_name"):
                info_data["授课教师"] = template_vars["teacher_name"]
            if template_vars.get("school"):
                info_data["学校"] = template_vars["school"]
            if template_vars.get("date"):
                info_data["日期"] = template_vars["date"]

        for key, value in info_data.items():
            lines.append(f"- **{key}**: {value}")
        lines.append("")

        # 教学目标
        objectives = content.get("objectives")
        if objectives:
            lines.extend(self._render_objectives_markdown(objectives))

        # 核心词汇
        vocabulary = content.get("vocabulary")
        if vocabulary:
            lines.extend(self._render_vocabulary_markdown(vocabulary))

        # 语法点
        grammar_points = content.get("grammar_points")
        if grammar_points:
            lines.extend(self._render_grammar_markdown(grammar_points))

        # 教学流程
        teaching_structure = content.get("teaching_structure")
        if teaching_structure:
            lines.extend(self._render_teaching_structure_markdown(teaching_structure))

        # 分层材料
        leveled_materials = content.get("leveled_materials")
        if leveled_materials:
            lines.extend(self._render_leveled_materials_markdown(leveled_materials))

        # 练习题
        exercises = content.get("exercises")
        if exercises:
            lines.extend(self._render_exercises_markdown(exercises))

        # PPT大纲
        ppt_outline = content.get("ppt_outline")
        if ppt_outline:
            lines.extend(self._render_ppt_outline_markdown(ppt_outline))

        # 教学反思
        teaching_notes = content.get("teaching_notes")
        if teaching_notes:
            lines.append("## 教学反思")
            lines.append("")
            lines.append(teaching_notes)
            lines.append("")

        return "\n".join(lines)

    def _render_objectives_markdown(self, objectives: Dict[str, Any]) -> List[str]:
        """渲染教学目标为 Markdown"""
        lines = ["## 教学目标", ""]

        if isinstance(objectives, dict):
            for category, items in objectives.items():
                if items:
                    lines.append(f"### {category}")
                    if isinstance(items, list):
                        for item in items:
                            lines.append(f"- {item}")
                    else:
                        lines.append(f"- {items}")
                    lines.append("")
        elif isinstance(objectives, str):
            lines.append(objectives)
            lines.append("")

        return lines

    def _render_vocabulary_markdown(self, vocabulary: Dict[str, Any]) -> List[str]:
        """渲染词汇为 Markdown"""
        lines = ["## 核心词汇", ""]

        if "words" in vocabulary:
            words = vocabulary["words"]
            if isinstance(words, list):
                lines.append("| 单词 | 释义 | 例句 |")
                lines.append("|------|------|------|")
                for word in words:
                    if isinstance(word, dict):
                        word_text = word.get("word", "")
                        definition = word.get("definition", word.get("meaning_cn", ""))
                        example = word.get("example", word.get("example_sentence", ""))
                        lines.append(f"| {word_text} | {definition} | {example} |")
                lines.append("")
            else:
                lines.append(f"- {words}")
                lines.append("")

        if "phrases" in vocabulary:
            phrases = vocabulary["phrases"]
            if isinstance(phrases, list):
                lines.append("### 短语")
                for phrase in phrases:
                    lines.append(f"- {phrase}")
                lines.append("")

        return lines

    def _render_grammar_markdown(self, grammar_points: Any) -> List[str]:
        """渲染语法点为 Markdown"""
        lines = ["## 语法点", ""]

        if isinstance(grammar_points, dict) and "points" in grammar_points:
            points = grammar_points["points"]
        else:
            points = grammar_points

        if isinstance(points, list):
            for point in points:
                if isinstance(point, dict):
                    name = point.get("name", "")
                    explanation = point.get("explanation", point.get("description", ""))
                    examples = point.get("examples", [])

                    if name:
                        lines.append(f"### {name}")
                    if explanation:
                        lines.append(f"{explanation}")
                    if examples:
                        lines.append("**例句：**")
                        for ex in examples[:5]:  # 最多5个例句
                            lines.append(f"- {ex}")
                    lines.append("")
                else:
                    lines.append(f"- {point}")
        elif isinstance(points, str):
            lines.append(points)

        return lines

    def _render_teaching_structure_markdown(self, structure: Dict[str, Any]) -> List[str]:
        """渲染教学流程为 Markdown"""
        lines = ["## 教学流程", ""]

        # 阶段名称映射（保留用于未来扩展）
        # phase_names = {
        #     "warm_up": "热身阶段",
        #     "presentation": "讲解阶段",
        #     "practice": "练习阶段",
        #     "production": "产出阶段",
        #     "summary": "总结阶段",
        #     "homework": "课后作业",
        # }

        if "stages" in structure:
            stages = structure["stages"]
            if isinstance(stages, list):
                for stage in stages:
                    if isinstance(stage, dict):
                        name = stage.get("name", stage.get("stage", ""))
                        duration = stage.get("duration", "")
                        activities = stage.get("activities", [])

                        lines.append(f"### {name}")
                        if duration:
                            lines.append(f"**时长**: {duration} 分钟")
                        if activities:
                            lines.append("**活动：**")
                            if isinstance(activities, list):
                                for act in activities:
                                    lines.append(f"- {act}")
                            else:
                                lines.append(f"- {activities}")
                        lines.append("")

        if "total_duration" in structure:
            lines.append(f"**总时长**: {structure['total_duration']} 分钟")
            lines.append("")

        return lines

    def _render_leveled_materials_markdown(self, materials: Any) -> List[str]:
        """渲染分层材料为 Markdown"""
        lines = ["## 分层阅读材料", ""]

        level_names = {
            "basic": "基础材料",
            "intermediate": "中等材料",
            "advanced": "进阶材料",
        }

        if isinstance(materials, dict):
            for level, content in materials.items():
                level_name = level_names.get(level, level)
                lines.append(f"### {level_name}")

                if isinstance(content, dict):
                    title = content.get("title", "")
                    text_content = content.get("content", "")

                    if title:
                        lines.append(f"**标题**: {title}")
                    if text_content:
                        # 限制长度
                        if len(text_content) > 500:
                            text_content = text_content[:500] + "..."
                        lines.append(text_content)
                elif isinstance(content, str):
                    if len(content) > 500:
                        content = content[:500] + "..."
                    lines.append(content)

                lines.append("")

        return lines

    def _render_exercises_markdown(self, exercises: Any) -> List[str]:
        """渲染练习题为 Markdown"""
        lines = ["## 练习题", ""]

        if isinstance(exercises, dict):
            if "items" in exercises:
                items = exercises["items"]
                if isinstance(items, list):
                    for i, item in enumerate(items, 1):
                        if isinstance(item, dict):
                            question = item.get("question", "")
                            options = item.get("options", [])
                            answer = item.get("answer", item.get("correct_answer", ""))
                            explanation = item.get("explanation", "")

                            lines.append(f"### {i}. {question}")

                            if options:
                                for opt in options:
                                    lines.append(f"- {opt}")

                            if answer:
                                lines.append(f"**答案**: {answer}")

                            if explanation:
                                lines.append(f"**解析**: {explanation}")

                            lines.append("")
                else:
                    lines.append(str(items))
            else:
                # 其他格式的练习题
                for key, value in exercises.items():
                    lines.append(f"### {key}")
                    lines.append(str(value))
                    lines.append("")

        return lines

    def _render_ppt_outline_markdown(self, ppt_outline: Any) -> List[str]:
        """渲染 PPT 大纲为 Markdown"""
        lines = ["## PPT大纲", ""]

        if isinstance(ppt_outline, dict) and "slides" in ppt_outline:
            slides = ppt_outline["slides"]
        else:
            slides = ppt_outline

        if isinstance(slides, list):
            for i, slide in enumerate(slides, 1):
                if isinstance(slide, dict):
                    title = slide.get("title", "")
                    bullet_points = slide.get("bullet_points", [])
                    notes = slide.get("notes", "")

                    lines.append(f"### {i}. {title}")

                    if bullet_points:
                        if isinstance(bullet_points, list):
                            for point in bullet_points:
                                lines.append(f"- {point}")
                        else:
                            lines.append(f"- {bullet_points}")

                    if notes:
                        lines.append(f"*备注: {notes}*")

                    lines.append("")

        if isinstance(ppt_outline, dict) and "total_slides" in ppt_outline:
            lines.append(f"**总页数**: {ppt_outline['total_slides']}")
            lines.append("")

        return lines


# ========== 模块级便捷函数 ==========


def get_pdf_generator(template_env=None) -> PDFDocumentGenerator:
    """
    获取 PDF 文档生成器实例

    Args:
        template_env: Jinja2 模板环境（可选）

    Returns:
        PDFDocumentGenerator: PDF 文档生成器实例
    """
    return PDFDocumentGenerator(template_env=template_env)
