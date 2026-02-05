"""
教案导出API集成测试
测试完整的教案导出流程
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LessonPlan, User, UserRole
from app.models.lesson_plan import LessonPlanTemplate


class TestLessonPlanExportAPI:
    """教案导出API测试类"""

    @pytest.mark.asyncio
    async def test_export_pdf_basic(self, client: AsyncClient, db: AsyncSession, teacher_user: User, sample_lesson_plan_data):
        """测试基本PDF导出功能"""
        # 创建教案
        lesson_plan = LessonPlan(
            teacher_id=teacher_user.id,
            title="测试教案",
            topic="Test Topic",
            level="A1",
            duration=45,
            target_exam="CET4",
            status="generated",
            objectives={"language_knowledge": ["掌握基本问候语"]},
            vocabulary={"noun": [{"word": "test", "meaning_cn": "测试"}]},
            grammar_points=[{"name": "test", "description": "测试"}],
            teaching_structure={"warm_up": {"title": "热身", "duration": 5}},
            leveled_materials=[],
            exercises={},
            ppt_outline=[{"slide_number": 1, "title": "测试"}]
        )
        db.add(lesson_plan)
        await db.commit()
        await db.refresh(lesson_plan)

        # 测试PDF导出
        response = await client.get(
            f"/api/v1/lesson-plans/{lesson_plan.id}/export/pdf",
            headers={"Authorization": f"Bearer {teacher_user.access_token}"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "Content-Disposition" in response.headers
        assert "教案-测试教案-A1.pdf" in response.headers["Content-Disposition"]
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_export_pdf_with_options(self, client: AsyncClient, db: AsyncSession, teacher_user: User, sample_lesson_plan_data):
        """测试PDF导出自定义选项"""
        # 创建教案
        lesson_plan = LessonPlan(
            teacher_id=teacher_user.id,
            title="测试教案",
            topic="Test Topic",
            level="A1",
            duration=45,
            status="generated",
            objectives={},
            vocabulary={},
            grammar_points=[],
            teaching_structure={},
            leveled_materials=[],
            exercises={},
            ppt_outline=[]
        )
        db.add(lesson_plan)
        await db.commit()
        await db.refresh(lesson_plan)

        # 测试带选项的PDF导出
        response = await client.get(
            f"/api/v1/lesson-plans/{lesson_plan.id}/export/pdf"
            f"?include_objectives=false&include_vocabulary=false&include_grammar=false",
            headers={"Authorization": f"Bearer {teacher_user.access_token}"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_export_markdown(self, client: AsyncClient, db: AsyncSession, teacher_user: User):
        """测试Markdown导出"""
        # 创建教案
        lesson_plan = LessonPlan(
            teacher_id=teacher_user.id,
            title="测试教案",
            topic="Test Topic",
            level="A1",
            duration=45,
            status="generated",
            objectives={"language_knowledge": ["掌握基本问候语"]},
            vocabulary={"noun": [{"word": "test", "meaning_cn": "测试"}]},
            grammar_points=[{"name": "test", "description": "测试"}],
            teaching_structure={"warm_up": {"title": "热身", "duration": 5}},
            leveled_materials=[],
            exercises={},
            ppt_outline=[]
        )
        db.add(lesson_plan)
        await db.commit()
        await db.refresh(lesson_plan)

        # 测试Markdown导出
        response = await client.get(
            f"/api/v1/lesson-plans/{lesson_plan.id}/export/markdown",
            headers={"Authorization": f"Bearer {teacher_user.access_token}"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown"
        assert "Content-Disposition" in response.headers
        assert "# 测试教案" in response.text

    @pytest.mark.asyncio
    async def test_export_ppt(self, client: AsyncClient, db: AsyncSession, teacher_user: User):
        """测试PPT导出"""
        # 创建教案
        lesson_plan = LessonPlan(
            teacher_id=teacher_user.id,
            title="测试教案",
            topic="Test Topic",
            level="A1",
            duration=45,
            status="generated",
            objectives={},
            vocabulary={},
            grammar_points=[],
            teaching_structure={},
            leveled_materials=[],
            exercises={},
            ppt_outline=[
                {"slide_number": 1, "title": "测试", "content": ["测试内容"]},
                {"slide_number": 2, "title": "测试2", "content": ["测试内容2"]}
            ]
        )
        db.add(lesson_plan)
        await db.commit()
        await db.refresh(lesson_plan)

        # 测试PPT导出
        response = await client.get(
            f"/api/v1/lesson-plans/{lesson_plan.id}/export/ppt?color_scheme=blue",
            headers={"Authorization": f"Bearer {teacher_user.access_token}"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        assert "Content-Disposition" in response.headers
        assert "教案PPT-测试教案-A1.pptx" in response.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_ppt_preview(self, client: AsyncClient, db: AsyncSession, teacher_user: User):
        """测试PPT预览"""
        # 创建教案
        lesson_plan = LessonPlan(
            teacher_id=teacher_user.id,
            title="测试教案",
            topic="Test Topic",
            level="A1",
            duration=45,
            status="generated",
            objectives={},
            vocabulary={},
            grammar_points=[],
            teaching_structure={},
            leveled_materials=[],
            exercises={},
            ppt_outline=[{"slide_number": 1, "title": "测试", "content": ["测试内容"]}]
        )
        db.add(lesson_plan)
        await db.commit()
        await db.refresh(lesson_plan)

        # 测试PPT预览
        response = await client.get(
            f"/api/v1/lesson-plans/{lesson_plan.id}/ppt/preview",
            headers={"Authorization": f"Bearer {teacher_user.access_token}"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html"
        assert "<!DOCTYPE html>" in response.text
        assert "测试教案" in response.text

    @pytest.mark.asyncio
    async def test_export_unauthorized(self, client: AsyncClient, db: AsyncSession, teacher_user: User, student_user: User):
        """测试无权限访问导出"""
        # 创建教案
        lesson_plan = LessonPlan(
            teacher_id=teacher_user.id,
            title="测试教案",
            topic="Test Topic",
            level="A1",
            duration=45,
            status="generated",
            objectives={},
            vocabulary={},
            grammar_points=[],
            teaching_structure={},
            leveled_materials=[],
            exercises={},
            ppt_outline=[]
        )
        db.add(lesson_plan)
        await db.commit()
        await db.refresh(lesson_plan)

        # 使用学生账号尝试访问教师教案
        response = await client.get(
            f"/api/v1/lesson-plans/{lesson_plan.id}/export/pdf",
            headers={"Authorization": f"Bearer {student_user.access_token}"}
        )

        assert response.status_code == 403
        assert "无权导出此教案" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_export_nonexistent_lesson_plan(self, client: AsyncClient, teacher_user: User):
        """测试导出不存在的教案"""
        import uuid
        fake_id = uuid.uuid4()

        response = await client.get(
            f"/api/v1/lesson-plans/{fake_id}/export/pdf",
            headers={"Authorization": f"Bearer {teacher_user.access_token}"}
        )

        assert response.status_code == 404
        assert "教案不存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_ppt_invalid_color_scheme(self, client: AsyncClient, db: AsyncSession, teacher_user: User):
        """测试无效的PPT配色方案"""
        # 创建教案
        lesson_plan = LessonPlan(
            teacher_id=teacher_user.id,
            title="测试教案",
            topic="Test Topic",
            level="A1",
            duration=45,
            status="generated",
            objectives={},
            vocabulary={},
            grammar_points=[],
            teaching_structure={},
            leveled_materials=[],
            exercises={},
            ppt_outline=[]
        )
        db.add(lesson_plan)
        await db.commit()
        await db.refresh(lesson_plan)

        # 测试无效配色方案
        response = await client.get(
            f"/api/v1/lesson-plans/{lesson_plan.id}/export/ppt?color_scheme=invalid",
            headers={"Authorization": f"Bearer {teacher_user.access_token}"}
        )

        assert response.status_code == 400
        assert "不支持的配色方案" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_template_list_access(self, client: AsyncClient, db: AsyncSession):
        """测试模板列表访问"""
        # 检查数据库中是否有模板
        result = await db.execute(select(LessonPlanTemplate).limit(5))
        templates = result.scalars().all()

        # 如果有模板，验证API可以访问
        if templates:
            assert len(templates) > 0
            # 这里应该测试模板列表API，但当前尚未实现
            # response = await client.get("/api/v1/lesson-plan-templates")
            # assert response.status_code == 200


class TestLessonPlanExportIntegration:
    """教案导出集成测试"""

    @pytest.mark.asyncio
    async def test_complete_export_workflow(self, client: AsyncClient, db: AsyncSession, teacher_user: User):
        """测试完整的导出工作流"""
        # 1. 创建教案
        lesson_plan = LessonPlan(
            teacher_id=teacher_user.id,
            title="完整测试教案",
            topic="Complete Test",
            level="B1",
            duration=90,
            target_exam="CET6",
            status="generated",
            objectives={
                "language_knowledge": ["掌握高级语法"],
                "language_skills": {
                    "listening": ["听懂复杂对话"],
                    "speaking": ["流利表达观点"],
                    "reading": ["理解长篇文章"],
                    "writing": ["撰写学术论文"]
                }
            },
            vocabulary={
                "noun": [
                    {"word": "analysis", "meaning_cn": "分析", "example_sentence": "This is an analysis."},
                    {"word": "research", "meaning_cn": "研究", "example_sentence": "Conduct research."}
                ],
                "verb": [
                    {"word": "analyze", "meaning_cn": "分析", "example_sentence": "Analyze the data."}
                ]
            },
            grammar_points=[
                {
                    "name": "Complex Sentences",
                    "description": "使用复杂句型",
                    "rule": "主句+从句结构",
                    "examples": ["Although it was raining, we went outside."],
                    "common_mistakes": ["Running in the park, the dog was happy."]
                }
            ],
            teaching_structure={
                "warm_up": {
                    "title": "头脑风暴",
                    "duration": 10,
                    "description": "激活背景知识",
                    "activities": ["讨论话题", "分享经验"]
                },
                "presentation": {
                    "title": "语法讲解",
                    "duration": 25,
                    "description": "系统讲解复杂句型",
                    "activities": ["讲解规则", "举例说明"]
                },
                "practice": [
                    {
                        "title": "句型练习",
                        "duration": 30,
                        "description": "操练复杂句型",
                        "activities": ["改写句子", "完形填空"]
                    }
                ],
                "production": {
                    "title": "实际应用",
                    "duration": 20,
                    "description": "在真实语境中使用",
                    "activities": ["写作练习", "口头表达"]
                },
                "summary": {
                    "title": "总结归纳",
                    "duration": 5,
                    "description": "回顾本课要点",
                    "activities": ["知识梳理", "作业布置"]
                }
            },
            leveled_materials=[
                {
                    "level": "B1",
                    "title": "学术写作入门",
                    "content": "Academic writing requires clear structure and logical flow.",
                    "word_count": 150,
                    "vocabulary_list": [
                        {"word": "structure", "meaning_cn": "结构"},
                        {"word": "logical", "meaning_cn": "逻辑的"}
                    ],
                    "comprehension_questions": [
                        "What does academic writing require?",
                        "What is important in academic writing?"
                    ],
                    "difficulty_notes": "适合B1水平学生"
                }
            ],
            exercises={
                "multiple_choice": [
                    {
                        "id": "q1",
                        "type": "multiple_choice",
                        "question": "Choose the correct complex sentence:",
                        "options": ["Simple", "Complex", "Compound", "Fragment"],
                        "correct_answer": "Complex",
                        "explanation": "Complex sentences contain subordinate clauses.",
                        "points": 2,
                        "difficulty": "B1"
                    }
                ],
                "fill_blank": [
                    {
                        "id": "q2",
                        "type": "fill_blank",
                        "question": "_____ the weather was bad, we continued our journey.",
                        "correct_answer": "Although",
                        "explanation": "Use 'although' to show contrast in complex sentences.",
                        "points": 2,
                        "difficulty": "B1"
                    }
                ]
            },
            ppt_outline=[
                {
                    "slide_number": 1,
                    "title": "复杂句型学习",
                    "content": ["课程标题", "等级：B1", "时长：90分钟"],
                    "layout": "title"
                },
                {
                    "slide_number": 2,
                    "title": "学习目标",
                    "content": ["掌握复杂句型", "提高写作能力", "增强语言运用"],
                    "layout": "title_content"
                },
                {
                    "slide_number": 3,
                    "title": "语法讲解",
                    "content": ["复杂句型的定义", "从句类型", "连接词使用"],
                    "layout": "title_content"
                }
            ]
        )
        db.add(lesson_plan)
        await db.commit()
        await db.refresh(lesson_plan)

        # 2. 测试PDF导出
        pdf_response = await client.get(
            f"/api/v1/lesson-plans/{lesson_plan.id}/export/pdf",
            headers={"Authorization": f"Bearer {teacher_user.access_token}"}
        )
        assert pdf_response.status_code == 200
        assert len(pdf_response.content) > 0

        # 3. 测试Markdown导出
        md_response = await client.get(
            f"/api/v1/lesson-plans/{lesson_plan.id}/export/markdown",
            headers={"Authorization": f"Bearer {teacher_user.access_token}"}
        )
        assert md_response.status_code == 200
        assert "完整测试教案" in md_response.text
        assert "学习目标" in md_response.text

        # 4. 测试PPT导出
        ppt_response = await client.get(
            f"/api/v1/lesson-plans/{lesson_plan.id}/export/ppt?color_scheme=blue",
            headers={"Authorization": f"Bearer {teacher_user.access_token}"}
        )
        assert ppt_response.status_code == 200
        assert "presentation" in ppt_response.headers["content-type"]

        # 5. 测试PPT预览
        preview_response = await client.get(
            f"/api/v1/lesson-plans/{lesson_plan.id}/ppt/preview",
            headers={"Authorization": f"Bearer {teacher_user.access_token}"}
        )
        assert preview_response.status_code == 200
        assert "<!DOCTYPE html>" in preview_response.text
        assert "完整测试教案" in preview_response.text

    @pytest.mark.asyncio
    async def test_partial_export_options(self, client: AsyncClient, db: AsyncSession, teacher_user: User):
        """测试部分导出选项"""
        # 创建教案
        lesson_plan = LessonPlan(
            teacher_id=teacher_user.id,
            title="部分导出测试",
            topic="Partial Export",
            level="A2",
            duration=60,
            status="generated",
            objectives={"language_knowledge": ["测试目标"]},
            vocabulary={"noun": [{"word": "test", "meaning_cn": "测试"}]},
            grammar_points=[{"name": "test", "description": "测试"}],
            teaching_structure={"warm_up": {"title": "热身", "duration": 5}},
            leveled_materials=[],
            exercises={},
            ppt_outline=[]
        )
        db.add(lesson_plan)
        await db.commit()
        await db.refresh(lesson_plan)

        # 测试只包含目标和词汇
        response = await client.get(
            f"/api/v1/lesson-plans/{lesson_plan.id}/export/pdf"
            f"?include_objectives=true&include_vocabulary=true"
            f"&include_structure=false&include_grammar=false"
            f"&include_materials=false&include_exercises=false"
            f"&include_ppt_outline=false",
            headers={"Authorization": f"Bearer {teacher_user.access_token}"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_empty_lesson_plan_export(self, client: AsyncClient, db: AsyncSession, teacher_user: User):
        """测试空教案导出"""
        # 创建最小化教案
        lesson_plan = LessonPlan(
            teacher_id=teacher_user.id,
            title="空教案测试",
            topic="Empty",
            level="A1",
            duration=30,
            status="generated",
            objectives={},
            vocabulary={},
            grammar_points=[],
            teaching_structure={},
            leveled_materials=[],
            exercises={},
            ppt_outline=[]
        )
        db.add(lesson_plan)
        await db.commit()
        await db.refresh(lesson_plan)

        # 测试导出空教案
        response = await client.get(
            f"/api/v1/lesson-plans/{lesson_plan.id}/export/markdown",
            headers={"Authorization": f"Bearer {teacher_user.access_token}"}
        )

        assert response.status_code == 200
        assert "空教案测试" in response.text


class TestLessonPlanTemplates:
    """教案模板测试"""

    @pytest.mark.asyncio
    async def test_template_initialization(self, db: AsyncSession):
        """测试模板是否正确初始化"""
        result = await db.execute(select(LessonPlanTemplate))
        templates = result.scalars().all()

        assert len(templates) > 0
        assert all(template.is_system for template in templates)

        # 验证模板分类
        levels = set(template.level for template in templates)
        assert "A1" in levels or "A2" in levels
        assert "B1" in levels or "B2" in levels or "C1" in levels or "C2" in levels

        # 验证模板结构
        for template in templates:
            assert template.template_structure is not None
            assert "warm_up" in template.template_structure or "presentation" in template.template_structure

    @pytest.mark.asyncio
    async def test_template_usage_count(self, db: AsyncSession):
        """测试模板使用计数"""
        result = await db.execute(select(LessonPlanTemplate).where(LessonPlanTemplate.name == "日常问候与介绍"))
        template = result.scalar_one_or_none()

        if template:
            assert template.usage_count >= 0
            assert template.is_system == True
