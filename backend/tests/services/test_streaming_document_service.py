"""
流式文档生成服务测试 - AI英语教学系统

测试流式文档生成服务的各项功能，包括流式生成、完整性验证、内存优化和错误处理。
"""

import uuid
from io import BytesIO
from typing import List
from unittest.mock import Mock

import pytest

from app.services.streaming_document_service import StreamingDocumentService


# ========== 测试数据 ==========


@pytest.fixture
def sample_content() -> dict:
    """示例教案内容数据"""
    return {
        "title": "测试教案 - 流式生成",
        "level": "B1",
        "topic": "Grammar",
        "duration": 45,
        "target_exam": "CET4",
        "objectives": {
            "language_knowledge": ["掌握过去完成时", "理解时间状语从句"],
            "language_skills": {
                "reading": ["能够理解包含过去完成时的文章"],
                "writing": ["能够在写作中正确使用过去完成时"],
            },
        },
        "vocabulary": {
            "noun": [
                {
                    "word": "achievement",
                    "phonetic": "/əˈtʃiːvmənt/",
                    "part_of_speech": "n.",
                    "meaning_cn": "成就，成绩",
                    "example_sentence": "Her greatest achievement was winning the gold medal.",
                }
            ],
            "verb": [
                {
                    "word": "realize",
                    "phonetic": "/ˈriːəlaɪz/",
                    "part_of_speech": "v.",
                    "meaning_cn": "实现，意识到",
                    "example_sentence": "He realized his dream of becoming a pilot.",
                }
            ],
        },
        "grammar_points": [
            {
                "name": "过去完成时",
                "description": "表示在过去某个时间之前已经完成的动作",
                "rule": "had + 过去分词",
                "examples": [
                    "I had finished my homework when he came.",
                    "She had already left before I arrived.",
                ],
                "common_mistakes": ["与一般过去时混淆", "忘记使用had"],
                "practice_tips": ["多做时间轴练习", "注意上下文时间关系"],
            }
        ],
        "teaching_structure": {
            "warm_up": {
                "duration": 5,
                "description": "通过图片展示过去的成就",
                "activities": ["学生分享自己的成就", "教师引导讨论"],
            },
            "presentation": {
                "duration": 15,
                "description": "讲解过去完成时的用法",
                "activities": ["时间轴演示", "例句分析"],
                "teacher_actions": ["解释语法规则", "提供例句"],
                "student_actions": ["记笔记", "回答问题"],
            },
            "practice": {
                "duration": 15,
                "description": "练习使用过去完成时",
                "activities": ["填空练习", "句子改写"],
            },
            "production": {
                "duration": 8,
                "description": "综合运用",
                "activities": ["写作练习", "口头表达"],
            },
            "summary": {
                "duration": 2,
                "description": "总结本课重点",
                "activities": ["学生总结", "教师补充"],
            },
        },
        "leveled_materials": [
            {
                "title": "成功的定义",
                "level": "A2",
                "word_count": 150,
                "content": "成功对不同的人有不同的定义。对一些人来说，成功意味着财富和名声。"
                "但对另一些人来说，成功可能是简单的事情，比如幸福的家庭或健康的生活。",
                "vocabulary_list": [
                    {"word": "definition", "meaning_cn": "定义"},
                    {"word": "wealth", "meaning_cn": "财富"},
                    {"word": "fame", "meaning_cn": "名声"},
                ],
                "comprehension_questions": [
                    "成功对所有人都有相同的定义吗？",
                    "作者认为成功可能包括什么？",
                ],
            },
            {
                "title": "成功的路径",
                "level": "B1",
                "word_count": 250,
                "content": "实现成功需要明确的目标和坚持不懈的努力。首先，你需要知道自己想要达成什么。"
                "然后，制定详细的计划并逐步执行。遇到困难时，不要放弃，而是寻找解决方案。",
                "vocabulary_list": [
                    {"word": "achieve", "meaning_cn": "实现"},
                    {"word": "persistent", "meaning_cn": "坚持不懈的"},
                    {"word": "detailed", "meaning_cn": "详细的"},
                ],
                "comprehension_questions": [
                    "实现成功需要什么？",
                    "遇到困难时应该怎么做？",
                ],
            },
        ],
        "exercises": {
            "multiple_choice": [
                {
                    "question": "When I arrived at the station, the train _____.",
                    "options": [
                        "left",
                        "had left",
                        "has left",
                        "was leaving",
                    ],
                    "correct_answer": "B",
                    "explanation": "火车在我到达之前已经离开，所以使用过去完成时 had left。",
                },
                {
                    "question": "She _____ the book before she watched the movie.",
                    "options": [
                        "read",
                        "had read",
                        "has read",
                        "was reading",
                    ],
                    "correct_answer": "B",
                    "explanation": "读书动作发生在看电影之前，使用过去完成时。",
                },
            ],
            "fill_blank": [
                {
                    "question": "They _____ (finish) their dinner when the phone rang.",
                    "correct_answer": "had finished",
                    "explanation": "吃晚饭发生在电话响之前。",
                }
            ],
        },
        "ppt_outline": [
            {
                "slide_number": 1,
                "title": "课程导入",
                "content": ["展示成功人士图片", "讨论什么是成功"],
                "notes": "激发学生兴趣",
            },
            {
                "slide_number": 2,
                "title": "过去完成时",
                "content": ["定义", "构成", "用法"],
                "notes": "重点讲解",
            },
            {
                "slide_number": 3,
                "title": "例句分析",
                "content": ["时间轴演示", "例句解析"],
                "notes": "帮助学生理解",
            },
        ],
        "teaching_notes": "本课重点在于过去完成时的理解和应用。"
        "学生容易与一般过去时混淆，需要通过时间轴等视觉辅助工具帮助学生理解。"
        "练习环节要循序渐进，从简单到复杂。",
    }


@pytest.fixture
def sample_template_vars() -> dict:
    """示例模板变量"""
    return {
        "teacher_name": "张老师",
        "school": "XX中学",
        "date": "2026-02-08",
    }


@pytest.fixture
def sample_lesson_plan() -> Mock:
    """示例教案模型（使用 Mock 避免关系问题）"""
    lesson_plan = Mock()
    lesson_plan.id = uuid.uuid4()
    lesson_plan.teacher_id = uuid.uuid4()
    lesson_plan.title = "测试教案 - 流式生成"
    lesson_plan.topic = "Grammar"
    lesson_plan.level = "B1"
    lesson_plan.duration = 45
    lesson_plan.target_exam = "CET4"
    lesson_plan.status = "draft"
    lesson_plan.objectives = {
        "language_knowledge": ["掌握过去完成时"],
        "language_skills": {
            "reading": ["理解包含过去完成时的文章"],
        },
    }
    lesson_plan.vocabulary = {
        "words": [
            {
                "word": "achievement",
                "meaning_cn": "成就",
                "example": "Her greatest achievement.",
            }
        ]
    }
    lesson_plan.grammar_points = {
        "points": [
            {
                "name": "过去完成时",
                "explanation": "过去某个时间之前已完成的动作",
                "examples": ["I had finished."],
            }
        ]
    }
    lesson_plan.teaching_structure = {
        "stages": [
            {
                "name": "热身阶段",
                "duration": "5分钟",
                "activities": ["图片展示"],
            }
        ]
    }
    lesson_plan.leveled_materials = [
        {
            "basic": {
                "title": "基础材料",
                "content": "这是一篇基础阅读材料。",
            }
        }
    ]
    lesson_plan.exercises = {
        "items": [
            {
                "question": "测试问题？",
                "answer": "A",
            }
        ]
    }
    lesson_plan.ppt_outline = {
        "slides": [
            {
                "title": "第一页",
                "bullet_points": ["要点1", "要点2"],
            }
        ]
    }
    lesson_plan.teaching_notes = "测试教学反思"
    # 添加 resources 字段（字典类型）
    lesson_plan.resources = {}
    return lesson_plan


# ========== 流式生成测试 ==========


class TestStreamingGeneration:
    """流式生成测试类"""

    @pytest.mark.asyncio
    async def test_stream_generate_word(self, sample_content, sample_template_vars):
        """测试 Word 文档流式生成"""
        service = StreamingDocumentService()
        chunks: List[bytes] = []

        async for chunk in service.stream_generate_word(
            sample_content, sample_template_vars, chunk_size=4096
        ):
            chunks.append(chunk)
            assert isinstance(chunk, bytes)
            assert len(chunk) > 0

        # 验证至少有一个数据块
        assert len(chunks) > 0

        # 验证总大小
        total_size = sum(len(c) for c in chunks)
        assert total_size > 0

        # 验证可以合并成完整文档
        full_doc = b"".join(chunks)
        assert len(full_doc) == total_size
        # Word 文档应该有正确的文件头
        assert full_doc.startswith(b"PK\x03\x04")  # ZIP 格式（DOCX 是 ZIP）

    @pytest.mark.asyncio
    async def test_stream_generate_pdf(self, sample_lesson_plan):
        """测试 PDF 文档流式生成"""
        service = StreamingDocumentService()
        chunks: List[bytes] = []

        async for chunk in service.stream_generate_pdf(
            sample_lesson_plan, chunk_size=4096
        ):
            chunks.append(chunk)
            assert isinstance(chunk, bytes)
            assert len(chunk) > 0

        # 验证至少有一个数据块
        assert len(chunks) > 0

        # 验证总大小
        total_size = sum(len(c) for c in chunks)
        assert total_size > 0

        # 验证可以合并成完整文档
        full_doc = b"".join(chunks)
        assert len(full_doc) == total_size
        # PDF 文档应该有正确的文件头
        assert full_doc.startswith(b"%PDF-")

    @pytest.mark.asyncio
    async def test_stream_generate_pptx(self, sample_content, sample_template_vars):
        """测试 PPTX 文档流式生成"""
        service = StreamingDocumentService()
        chunks: List[bytes] = []

        async for chunk in service.stream_generate_pptx(
            sample_content, sample_template_vars, chunk_size=4096
        ):
            chunks.append(chunk)
            assert isinstance(chunk, bytes)
            assert len(chunk) > 0

        # 验证至少有一个数据块
        assert len(chunks) > 0

        # 验证总大小
        total_size = sum(len(c) for c in chunks)
        assert total_size > 0

        # 验证可以合并成完整文档
        full_doc = b"".join(chunks)
        assert len(full_doc) == total_size
        # PPTX 文档应该有正确的文件头
        assert full_doc.startswith(b"PK\x03\x04")  # ZIP 格式（PPTX 是 ZIP）

    @pytest.mark.asyncio
    async def test_chunk_size_validation(self, sample_content, sample_template_vars):
        """测试数据块大小验证"""
        service = StreamingDocumentService()

        # 测试不同的块大小
        chunk_sizes = [1024, 4096, 8192, 16384]

        for chunk_size in chunk_sizes:
            chunks = []
            async for chunk in service.stream_generate_word(
                sample_content, sample_template_vars, chunk_size=chunk_size
            ):
                chunks.append(chunk)

            # 除了最后一个块，其他块应该接近指定大小
            for i, c in enumerate(chunks[:-1]):
                # 允许一定的误差（由于对齐等因素）
                assert len(c) <= chunk_size

    @pytest.mark.asyncio
    async def test_invalid_chunk_size_too_small(self, sample_content, sample_template_vars):
        """测试过小的块大小"""
        service = StreamingDocumentService()

        # 在开始迭代之前就会抛出异常（被包装为 Exception）
        generator = service.stream_generate_word(
            sample_content, sample_template_vars, chunk_size=512
        )

        with pytest.raises(Exception, match="Word文档流式生成失败.*块大小不能小于"):
            await generator.__anext__()

    @pytest.mark.asyncio
    async def test_invalid_chunk_size_too_large(self, sample_content, sample_template_vars):
        """测试过大的块大小"""
        service = StreamingDocumentService()

        # 在开始迭代之前就会抛出异常（被包装为 Exception）
        generator = service.stream_generate_word(
            sample_content, sample_template_vars, chunk_size=2 * 1024 * 1024
        )

        with pytest.raises(Exception, match="Word文档流式生成失败.*块大小不能大于"):
            await generator.__anext__()


# ========== 完整性测试 ==========


class TestDocumentIntegrity:
    """文档完整性测试类"""

    @pytest.mark.asyncio
    async def test_streamed_vs_complete_word(self, sample_content, sample_template_vars):
        """测试流式生成的 Word 文档与完整文档一致"""
        from app.services.document_generators.word_generator import WordDocumentGenerator

        service = StreamingDocumentService()
        generator = WordDocumentGenerator()

        # 获取流式生成的文档
        streamed_chunks = []
        async for chunk in service.stream_generate_word(
            sample_content, sample_template_vars
        ):
            streamed_chunks.append(chunk)
        streamed_doc = b"".join(streamed_chunks)

        # 获取完整生成的文档
        complete_doc = generator.generate(sample_content, sample_template_vars)

        # 验证两者完全一致
        assert len(streamed_doc) == len(complete_doc)
        assert streamed_doc == complete_doc

    @pytest.mark.asyncio
    async def test_streamed_vs_complete_pdf(self, sample_lesson_plan):
        """测试流式生成的 PDF 文档与完整文档一致"""
        from app.services.document_generators.pdf_generator import PDFDocumentGenerator

        service = StreamingDocumentService()
        generator = PDFDocumentGenerator()

        # 获取流式生成的文档
        streamed_chunks = []
        async for chunk in service.stream_generate_pdf(sample_lesson_plan):
            streamed_chunks.append(chunk)
        streamed_doc = b"".join(streamed_chunks)

        # 获取完整生成的文档
        complete_doc = await generator.generate_from_lesson_plan(sample_lesson_plan)

        # 验证两者完全一致
        assert len(streamed_doc) == len(complete_doc)
        assert streamed_doc == complete_doc

    @pytest.mark.asyncio
    async def test_streamed_vs_complete_pptx(self, sample_content, sample_template_vars):
        """测试流式生成的 PPTX 文档与完整文档一致"""
        from app.services.document_generators.pptx_generator import PPTXDocumentGenerator

        service = StreamingDocumentService()
        generator = PPTXDocumentGenerator()

        # 获取流式生成的文档
        streamed_chunks = []
        async for chunk in service.stream_generate_pptx(
            sample_content, sample_template_vars
        ):
            streamed_chunks.append(chunk)
        streamed_doc = b"".join(streamed_chunks)

        # 获取完整生成的文档
        complete_doc = generator.generate(sample_content, sample_template_vars)

        # 验证两者完全一致
        assert len(streamed_doc) == len(complete_doc)
        assert streamed_doc == complete_doc

    @pytest.mark.asyncio
    async def test_document_can_be_opened_word(self, sample_content, sample_template_vars):
        """测试流式生成的 Word 文档可以正常打开"""
        import zipfile

        service = StreamingDocumentService()

        chunks = []
        async for chunk in service.stream_generate_word(
            sample_content, sample_template_vars
        ):
            chunks.append(chunk)

        doc_bytes = b"".join(chunks)

        # 验证这是一个有效的 ZIP 文件（DOCX 是 ZIP 格式）
        with zipfile.ZipFile(BytesIO(doc_bytes), "r") as zip_file:
            # 验证包含必要的文件
            assert "[Content_Types].xml" in zip_file.namelist()
            assert "word/document.xml" in zip_file.namelist()

    @pytest.mark.asyncio
    async def test_document_file_size_correct(self, sample_content, sample_template_vars):
        """测试文档文件大小正确"""
        service = StreamingDocumentService()

        chunks = []
        total_streamed = 0
        async for chunk in service.stream_generate_word(
            sample_content, sample_template_vars
        ):
            chunks.append(chunk)
            total_streamed += len(chunk)

        full_doc = b"".join(chunks)

        # 验证流式传输的总大小与文档大小一致
        assert total_streamed == len(full_doc)


# ========== 内存测试 ==========


class TestMemoryOptimization:
    """内存优化测试类"""

    @pytest.mark.asyncio
    async def test_large_document_streaming(self, sample_content, sample_template_vars):
        """测试大文档流式处理不会溢出"""
        # 创建一个较大的内容
        large_content = sample_content.copy()
        large_content["teaching_notes"] = "这是一个很长的教学反思。" * 1000

        service = StreamingDocumentService()

        chunks = []
        async for chunk in service.stream_generate_word(
            large_content, sample_template_vars, chunk_size=1024
        ):
            chunks.append(chunk)
            # 验证每个块的大小
            assert len(chunk) <= 1024

        # 验证文档生成成功
        assert len(chunks) > 0
        full_doc = b"".join(chunks)
        assert len(full_doc) > 0

    @pytest.mark.asyncio
    async def test_memory_usage_stable(self, sample_content, sample_template_vars):
        """测试内存使用稳定"""
        import tracemalloc

        service = StreamingDocumentService()

        # 开始追踪内存
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        # 流式生成文档
        chunks = []
        async for chunk in service.stream_generate_word(
            sample_content, sample_template_vars, chunk_size=2048
        ):
            chunks.append(chunk)

        snapshot2 = tracemalloc.take_snapshot()

        # 停止追踪
        tracemalloc.stop()

        # 验证内存增长在合理范围内（不超过 10MB）
        top_stats = snapshot2.compare_to(snapshot1, "lineno")
        total_increase = sum(stat.size_diff for stat in top_stats)

        # 10MB = 10 * 1024 * 1024 bytes
        assert total_increase < 10 * 1024 * 1024


# ========== 错误处理测试 ==========


class TestErrorHandling:
    """错误处理测试类"""

    @pytest.mark.asyncio
    async def test_missing_title(self, sample_template_vars):
        """测试缺少标题时的错误处理"""
        service = StreamingDocumentService()
        invalid_content = {"level": "B1"}  # 缺少 title

        # 在开始迭代之前就会抛出异常（被包装为 Exception）
        generator = service.stream_generate_word(
            invalid_content, sample_template_vars
        )

        with pytest.raises(Exception, match="Word文档流式生成失败.*教案标题不能为空"):
            await generator.__anext__()

    @pytest.mark.asyncio
    async def test_empty_lesson_plan(self):
        """测试空教案时的错误处理"""
        service = StreamingDocumentService()
        lesson_plan = Mock()  # 空 Mock
        lesson_plan.title = None  # 没有标题
        lesson_plan.resources = {}  # 添加 resources 字典

        # 在开始迭代之前就会抛出异常（被包装为 Exception）
        generator = service.stream_generate_pdf(lesson_plan)

        with pytest.raises(Exception, match="PDF文档流式生成失败.*教案标题不能为空"):
            await generator.__anext__()

    @pytest.mark.asyncio
    async def test_progress_callback_word(self, sample_content, sample_template_vars):
        """测试 Word 生成进度回调"""
        service = StreamingDocumentService()
        progress_values = []

        def callback(percent: int):
            progress_values.append(percent)

        async for _ in service.stream_generate_word(
            sample_content, sample_template_vars, progress_callback=callback
        ):
            pass

        # 验证进度回调被调用
        assert len(progress_values) > 0
        # 验证进度从 0 开始到 100 结束
        assert progress_values[0] == 0
        assert progress_values[-1] == 100

    @pytest.mark.asyncio
    async def test_progress_callback_pdf(self, sample_lesson_plan):
        """测试 PDF 生成进度回调"""
        service = StreamingDocumentService()
        progress_values = []

        def callback(percent: int):
            progress_values.append(percent)

        async for _ in service.stream_generate_pdf(
            sample_lesson_plan, progress_callback=callback
        ):
            pass

        # 验证进度回调被调用
        assert len(progress_values) > 0
        # 验证进度包含开始和结束
        assert 0 in progress_values or 10 in progress_values  # 开始
        assert 100 in progress_values  # 结束

    @pytest.mark.asyncio
    async def test_interrupt_mid_stream(self, sample_content, sample_template_vars):
        """测试中断流式传输的处理"""
        service = StreamingDocumentService()
        chunk_count = 0
        max_chunks = 2  # 只读取前两个块

        async for chunk in service.stream_generate_word(
            sample_content, sample_template_vars
        ):
            chunk_count += 1
            if chunk_count >= max_chunks:
                break

        # 验证只读取了指定数量的块
        assert chunk_count == max_chunks


# ========== 模块级便捷函数测试 ==========


class TestConvenienceFunctions:
    """便捷函数测试类"""

    def test_get_streaming_document_service(self):
        """测试获取流式文档生成服务实例"""
        from app.services.streaming_document_service import get_streaming_document_service

        service = get_streaming_document_service()
        assert isinstance(service, StreamingDocumentService)

        # 验证每次调用返回新实例
        service2 = get_streaming_document_service()
        assert service is not service2
