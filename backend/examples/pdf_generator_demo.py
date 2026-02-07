"""
PDF文档生成器使用示例

演示如何使用 PDFDocumentGenerator 将教案导出为 PDF 格式。
"""
import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from app.services.document_generators.pdf_generator import PDFDocumentGenerator


class DemoLessonPlan:
    """演示用的教案对象"""

    def __init__(self):
        self.id = uuid4()
        self.title = "英语阅读理解技巧教学"
        self.topic = "阅读技巧"
        self.level = "B2"
        self.duration = 60
        self.target_exam = "CET6"
        self.created_at = datetime.now(timezone.utc)
        self.objectives = {
            "overall": "掌握英语阅读理解的基本技巧",
            "specific": ["理解文章主旨", "识别细节信息", "推断词义", "理解作者态度"],
            "outcomes": ["提高阅读速度", "增强理解准确性"],
        }
        self.vocabulary = {
            "words": [
                {
                    "word": "comprehension",
                    "definition": "理解，领悟",
                    "example": "Reading comprehension is essential for language learning.",
                },
                {
                    "word": "skim",
                    "definition": "略读，快速浏览",
                    "example": "Skim the passage to get the main idea.",
                },
                {
                    "word": "scan",
                    "definition": "扫读，寻找特定信息",
                    "example": "Scan the text for specific dates.",
                },
            ],
            "phrases": ["figure out", "in terms of", "deal with"],
        }
        self.grammar_points = {
            "points": [
                {
                    "name": "定语从句",
                    "explanation": "用来修饰名词或代词的从句，分为限制性和非限制性",
                    "examples": [
                        "The book that I read yesterday was interesting.",
                        "This is the place where we met.",
                    ],
                },
                {
                    "name": "状语从句",
                    "explanation": "修饰动词、形容词或副词的从句",
                    "examples": [
                        "When I arrived, he was having dinner.",
                        "Although it was raining, we went out.",
                    ],
                },
            ]
        }
        self.teaching_structure = {
            "stages": [
                {"name": "导入", "duration": 5, "activities": ["提问导入", "图片展示"]},
                {"name": "讲解", "duration": 20, "activities": ["技巧讲解", "例句分析"]},
                {"name": "练习", "duration": 25, "activities": ["小组讨论", "个人练习"]},
                {"name": "总结", "duration": 10, "activities": ["要点回顾"]},
            ],
            "total_duration": 60,
        }
        self.leveled_materials = {
            "basic": {
                "title": "基础阅读材料",
                "content": "Reading is an important skill in language learning. It helps you learn new words and understand grammar.",
            },
            "intermediate": {
                "title": "中等阅读材料",
                "content": "Reading comprehension is a critical skill that allows you to understand written text, extract meaning, and gain knowledge from various sources.",
            },
            "advanced": {
                "title": "进阶阅读材料",
                "content": "Advanced reading comprehension involves not only understanding the literal meaning of the text but also making inferences, recognizing implications, and critically analyzing the author's arguments and rhetorical devices.",
            },
        }
        self.exercises = {
            "type": "阅读理解",
            "items": [
                {
                    "question": "What is the main idea of the passage?",
                    "options": ["A. Reading is easy", "B. Reading is important", "C. Reading is difficult", "D. Reading is boring"],
                    "answer": "B",
                    "explanation": "文章主要讲述阅读的重要性。",
                },
                {
                    "question": "According to the passage, reading helps to?",
                    "options": ["A. Speak better", "B. Write better", "C. Learn vocabulary", "D. Listen better"],
                    "answer": "C",
                    "explanation": "文章提到阅读帮助学习新词汇。",
                },
            ],
        }
        self.ppt_outline = {
            "slides": [
                {"title": "课程导入", "bullet_points": ["阅读的重要性", "本课目标", "教学安排"]},
                {"title": "阅读技巧：略读", "bullet_points": ["定义", "适用场景", "练习方法"]},
                {"title": "阅读技巧：扫读", "bullet_points": ["定义", "适用场景", "练习方法"]},
                {"title": "课堂练习", "bullet_points": ["小组活动", "个人练习", "答案讲解"]},
                {"title": "总结与作业", "bullet_points": ["要点回顾", "课后作业"]},
            ],
            "total_slides": 5,
        }
        self.resources = {
            "links": ["https://example.com/reading-tips", "https://example.com/practice-materials"],
            "attachments": ["reading_materials.pdf", "exercises.pdf"],
            "references": ["《英语阅读教学指南》", "CET6 考试大纲"],
        }
        self.teaching_notes = "学生反应积极，对略读技巧掌握较好。建议下次增加更多扫读练习，并提供更多不同类型的文章进行练习。"


async def demo_generate_from_lesson_plan():
    """演示从 LessonPlan 对象生成 PDF"""
    print("=== 演示1: 从 LessonPlan 对象生成完整 PDF ===\n")

    generator = PDFDocumentGenerator()
    lesson_plan = DemoLessonPlan()

    # 生成完整 PDF
    pdf_bytes = await generator.generate_from_lesson_plan(lesson_plan)

    # 保存到文件
    output_path = "demo_lesson_plan_full.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"✅ 完整 PDF 已生成: {output_path}")
    print(f"   文件大小: {len(pdf_bytes)} 字节\n")


async def demo_generate_with_sections_filter():
    """演示生成部分章节的 PDF"""
    print("=== 演示2: 生成部分章节 PDF ===\n")

    generator = PDFDocumentGenerator()
    lesson_plan = DemoLessonPlan()

    # 只生成基本信息、教学目标和词汇
    pdf_bytes = await generator.generate_from_lesson_plan(
        lesson_plan,
        include_sections=["metadata", "objectives", "vocabulary"],
    )

    # 保存到文件
    output_path = "demo_lesson_plan_partial.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"✅ 部分 PDF 已生成: {output_path}")
    print(f"   包含章节: metadata, objectives, vocabulary")
    print(f"   文件大小: {len(pdf_bytes)} 字节\n")


async def demo_generate_from_dict():
    """演示从字典数据生成 PDF"""
    print("=== 演示3: 从字典数据生成 PDF ===\n")

    generator = PDFDocumentGenerator()

    content = {
        "title": "英语口语教学教案",
        "level": "B1",
        "topic": "日常对话",
        "duration": 45,
        "target_exam": "CET4",
        "objectives": {
            "overall": "掌握日常英语对话技巧",
            "specific": ["学会问候", "学会自我介绍", "学会表达观点"],
        },
        "vocabulary": {
            "words": [
                {"word": "conversation", "definition": "对话", "example": "Let's have a conversation."},
                {"word": "opinion", "definition": "观点", "example": "What's your opinion?"},
            ]
        },
        "teaching_structure": {
            "stages": [
                {"name": "热身", "duration": 5, "activities": ["自由对话"]},
                {"name": "讲解", "duration": 15, "activities": ["句型讲解"]},
                {"name": "练习", "duration": 20, "activities": ["角色扮演"]},
                {"name": "总结", "duration": 5, "activities": ["回顾要点"]},
            ],
            "total_duration": 45,
        },
    }

    template_vars = {
        "teacher_name": "李老师",
        "school": "XX中学",
        "date": "2026-02-07",
    }

    pdf_bytes = await generator.generate(content, template_vars)

    # 保存到文件
    output_path = "demo_lesson_plan_dict.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"✅ 字典 PDF 已生成: {output_path}")
    print(f"   模板变量: {template_vars}")
    print(f"   文件大小: {len(pdf_bytes)} 字节\n")


async def demo_markdown_preview():
    """演示预览 Markdown 内容"""
    print("=== 演示4: 预览 Markdown 内容 ===\n")

    generator = PDFDocumentGenerator()

    content = {
        "title": "简单教案",
        "level": "A2",
        "topic": "基础语法",
        "duration": 30,
        "objectives": {"overall": "掌握基本时态"},
        "vocabulary": {"words": [{"word": "be", "definition": "是", "example": "I am happy."}]},
    }

    markdown = generator._render_to_markdown(content)

    print("Markdown 内容预览:")
    print("-" * 50)
    print(markdown)
    print("-" * 50)
    print()


async def main():
    """运行所有演示"""
    print("\n" + "=" * 60)
    print("PDF 文档生成器演示")
    print("=" * 60 + "\n")

    await demo_generate_from_lesson_plan()
    await demo_generate_with_sections_filter()
    await demo_generate_from_dict()
    await demo_markdown_preview()

    print("=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
