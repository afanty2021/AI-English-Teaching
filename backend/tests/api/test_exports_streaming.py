"""
流式导出 API 测试
测试流式导出功能的基础功能、响应头、流式传输和错误处理
"""
import uuid

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_current_teacher
from app.models import LessonPlan, User, UserRole
from app.main import app


class TestStreamingExportBasic:
    """流式导出基础功能测试"""

    @pytest.mark.asyncio
    async def test_stream_export_word(self, db_session: AsyncSession, teacher_user: User):
        """测试流式导出 Word 文档"""
        # 创建教案
        lesson_plan = LessonPlan(
            teacher_id=teacher_user.id,
            title="流式导出测试教案",
            topic="Streaming Export Test",
            level="B1",
            duration=45,
            target_exam="CET4",
            status="generated",
            objectives={"language_knowledge": ["掌握流式导出概念"]},
            vocabulary={"noun": [{"word": "stream", "meaning_cn": "流"}]},
            grammar_points=[{"name": "Present Continuous", "description": "现在进行时"}],
            teaching_structure={"warm_up": {"title": "热身", "duration": 5}},
            leveled_materials=[],
            exercises={},
            ppt_outline=[{"slide_number": 1, "title": "测试"}]
        )
        db_session.add(lesson_plan)
        await db_session.commit()
        await db_session.refresh(lesson_plan)

        # 依赖注入覆盖
        async def override_get_db():
            yield db_session

        async def override_get_current_user():
            return teacher_user

        async def override_get_current_teacher():
            return teacher_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_teacher] = override_get_current_teacher

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/exports/stream?lesson_plan_id={lesson_plan.id}&format=word"
                )

                assert response.status_code == 200
                assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in response.headers["content-type"]
                assert "Content-Disposition" in response.headers
                # URL 编码的文件名
                assert "attachment" in response.headers["Content-Disposition"]
                assert "filename*=UTF-8" in response.headers["Content-Disposition"]
                assert len(response.content) > 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_stream_export_pdf(self, db_session: AsyncSession, teacher_user: User):
        """测试流式导出 PDF 文档"""
        # 创建教案
        lesson_plan = LessonPlan(
            teacher_id=teacher_user.id,
            title="PDF流式导出测试",
            topic="PDF Streaming Test",
            level="A2",
            duration=60,
            target_exam="CET6",
            status="generated",
            objectives={"language_skills": {"reading": ["提高阅读能力"]}},
            vocabulary={},
            grammar_points=[],
            teaching_structure={},
            leveled_materials=[],
            exercises={},
            ppt_outline=[]
        )
        db_session.add(lesson_plan)
        await db_session.commit()
        await db_session.refresh(lesson_plan)

        # 依赖注入覆盖
        async def override_get_db():
            yield db_session

        async def override_get_current_user():
            return teacher_user

        async def override_get_current_teacher():
            return teacher_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_teacher] = override_get_current_teacher

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/exports/stream?lesson_plan_id={lesson_plan.id}&format=pdf"
                )

                assert response.status_code == 200
                assert response.headers["content-type"] == "application/pdf"
                assert "Content-Disposition" in response.headers
                assert "attachment" in response.headers["Content-Disposition"]
                assert "filename*=UTF-8" in response.headers["Content-Disposition"]
                assert len(response.content) > 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_stream_export_pptx(self, db_session: AsyncSession, teacher_user: User):
        """测试流式导出 PPTX 文档"""
        # 创建教案
        lesson_plan = LessonPlan(
            teacher_id=teacher_user.id,
            title="PPTX流式导出测试",
            topic="PPTX Streaming Test",
            level="B2",
            duration=90,
            target_exam="IELTS",
            status="generated",
            objectives={},
            vocabulary={},
            grammar_points=[],
            teaching_structure={},
            leveled_materials=[],
            exercises={},
            ppt_outline=[
                {"slide_number": 1, "title": "标题页", "content": ["测试内容"]},
                {"slide_number": 2, "title": "内容页", "content": ["详细内容"]}
            ]
        )
        db_session.add(lesson_plan)
        await db_session.commit()
        await db_session.refresh(lesson_plan)

        # 依赖注入覆盖
        async def override_get_db():
            yield db_session

        async def override_get_current_user():
            return teacher_user

        async def override_get_current_teacher():
            return teacher_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_teacher] = override_get_current_teacher

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/exports/stream?lesson_plan_id={lesson_plan.id}&format=pptx"
                )

                assert response.status_code == 200
                assert "application/vnd.openxmlformats-officedocument.presentationml.presentation" in response.headers["content-type"]
                assert "Content-Disposition" in response.headers
                assert "attachment" in response.headers["Content-Disposition"]
                assert "filename*=UTF-8" in response.headers["Content-Disposition"]
                assert len(response.content) > 0
        finally:
            app.dependency_overrides.clear()


class TestStreamingExportErrors:
    """流式导出错误处理测试"""

    @pytest.mark.asyncio
    async def test_lesson_plan_not_found(self, db_session: AsyncSession, teacher_user: User):
        """测试教案不存在返回 404"""
        fake_id = uuid.uuid4()

        # 依赖注入覆盖
        async def override_get_db():
            yield db_session

        async def override_get_current_user():
            return teacher_user

        async def override_get_current_teacher():
            return teacher_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_teacher] = override_get_current_teacher

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/exports/stream?lesson_plan_id={fake_id}&format=pdf"
                )

                assert response.status_code == 404
                assert "教案不存在" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_unsupported_format(self, db_session: AsyncSession, teacher_user: User):
        """测试格式不支持返回 400"""
        # 创建教案
        lesson_plan = LessonPlan(
            teacher_id=teacher_user.id,
            title="格式测试",
            topic="Format Test",
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
        db_session.add(lesson_plan)
        await db_session.commit()
        await db_session.refresh(lesson_plan)

        # 依赖注入覆盖
        async def override_get_db():
            yield db_session

        async def override_get_current_user():
            return teacher_user

        async def override_get_current_teacher():
            return teacher_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_teacher] = override_get_current_teacher

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # 测试不支持的格式
                response = await client.post(
                    f"/api/v1/exports/stream?lesson_plan_id={lesson_plan.id}&format=unsupported"
                )

                assert response.status_code == 400
                assert "不支持的导出格式" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_cross_user_access_denied(self, db_session: AsyncSession, teacher_user: User, another_teacher_user: User):
        """测试跨用户访问被拒绝"""
        # teacher_user 创建教案
        lesson_plan = LessonPlan(
            teacher_id=teacher_user.id,
            title="跨用户测试",
            topic="Cross User Test",
            level="B2",
            duration=60,
            status="generated",
            objectives={},
            vocabulary={},
            grammar_points=[],
            teaching_structure={},
            leveled_materials=[],
            exercises={},
            ppt_outline=[]
        )
        db_session.add(lesson_plan)
        await db_session.commit()
        await db_session.refresh(lesson_plan)

        # 依赖注入覆盖 - 使用另一个教师用户
        async def override_get_db():
            yield db_session

        async def override_get_current_user():
            return another_teacher_user

        async def override_get_current_teacher():
            return another_teacher_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_teacher] = override_get_current_teacher

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # another_teacher_user 尝试访问 teacher_user 的教案
                response = await client.post(
                    f"/api/v1/exports/stream?lesson_plan_id={lesson_plan.id}&format=pdf"
                )

                assert response.status_code == 403
                assert "无权导出此教案" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


class TestExportFormatsEndpoint:
    """导出格式列表端点测试"""

    @pytest.mark.asyncio
    async def test_list_export_formats(self, db_session: AsyncSession, teacher_user: User):
        """测试获取支持的导出格式列表"""
        # 依赖注入覆盖
        async def override_get_current_user():
            return teacher_user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/exports/formats")

                assert response.status_code == 200
                data = response.json()
                assert "formats" in data

                formats = data["formats"]
                assert len(formats) == 3

                # 验证格式信息
                format_values = [f["value"] for f in formats]
                assert "word" in format_values
                assert "pdf" in format_values
                assert "pptx" in format_values

                # 验证每个格式有完整的元数据
                for format_info in formats:
                    assert "value" in format_info
                    assert "label" in format_info
                    assert "extension" in format_info
                    assert "media_type" in format_info
        finally:
            app.dependency_overrides.clear()
