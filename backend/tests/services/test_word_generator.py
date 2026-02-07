"""
Word文档生成器单元测试

测试 WordDocumentGenerator 类的各项功能。
"""
import pytest

from app.services.document_generators.word_generator import WordDocumentGenerator


class TestWordDocumentGenerator:
    """WordDocumentGenerator 测试类"""

    @pytest.fixture
    def generator(self):
        """创建生成器实例"""
        return WordDocumentGenerator()

    @pytest.fixture
    def basic_content(self):
        """基本教案内容"""
        return {
            "title": "过去完成时教学",
            "level": "B1",
            "topic": "Grammar",
            "duration": 45,
            "target_exam": "CET4",
        }

    @pytest.fixture
    def full_content(self):
        """完整教案内容"""
        return {
            "title": "过去完成时教学",
            "level": "B1",
            "topic": "Grammar",
            "duration": 45,
            "target_exam": "CET4",
            "objectives": {
                "language_knowledge": ["掌握过去完成时的构成", "理解过去完成时的用法"],
                "language_skills": {
                    "listening": ["能听懂包含过去完成的对话"],
                    "reading": ["能理解包含过去完成的文章"],
                },
            },
            "vocabulary": {
                "noun": [
                    {
                        "word": "experience",
                        "phonetic": "/ɪkˈspɪəriəns/",
                        "part_of_speech": "n.",
                        "meaning_cn": "经验，经历",
                        "example_sentence": "I have experience in teaching.",
                    }
                ],
                "verb": [
                    {
                        "word": "realize",
                        "phonetic": "/ˈriːəlaɪz/",
                        "part_of_speech": "v.",
                        "meaning_cn": "意识到",
                        "example_sentence": "She realized her mistake.",
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
                        "She had left before I arrived.",
                    ],
                    "common_mistakes": ["与一般过去时混淆", "忘记使用had"],
                    "practice_tips": ["多造句练习", "阅读时注意标记"],
                }
            ],
            "teaching_structure": {
                "warm_up": {
                    "duration": 5,
                    "description": "通过图片导入过去完成时的概念",
                    "activities": ["展示时间线", "提问引导"],
                    "teacher_actions": ["展示PPT", "提问学生"],
                    "student_actions": ["观看图片", "回答问题"],
                },
                "presentation": {
                    "duration": 15,
                    "description": "讲解过去完成时的构成和用法",
                    "activities": ["讲解规则", "举例说明"],
                    "teacher_actions": ["板书规则", "举例"],
                    "student_actions": ["记笔记", "跟读例句"],
                },
            },
            "leveled_materials": [
                {
                    "title": "The Journey",
                    "level": "B1",
                    "word_count": 200,
                    "content": "Last year, John had traveled to many countries before he returned home.",
                    "vocabulary_list": [
                        {"word": "journey", "meaning_cn": "旅程"},
                        {"word": "return", "meaning_cn": "返回"},
                    ],
                    "comprehension_questions": [
                        "Where had John traveled?",
                        "When did he return home?",
                    ],
                }
            ],
            "exercises": {
                "multiple_choice": [
                    {
                        "question": "By the time I arrived, he ____.",
                        "options": ["had left", "left", "has left", "leaves"],
                        "correct_answer": "A",
                        "explanation": "因为'到达'是过去的时间，'离开'发生在到达之前，所以用过去完成时。",
                    },
                    {
                        "question": "She ____ the book before she watched the movie.",
                        "options": ["had read", "read", "has read", "reads"],
                        "correct_answer": "A",
                        "explanation": "看书发生在看电影之前，用过去完成时。",
                    },
                ],
                "fill_blank": [
                    {
                        "question": "I ____ (finish) my homework before dinner.",
                        "correct_answer": "had finished",
                        "explanation": "完成作业发生在晚饭前，用过去完成时。",
                    }
                ],
            },
            "ppt_outline": [
                {
                    "slide_number": 1,
                    "title": "过去完成时",
                    "content": ["定义", "构成", "用法"],
                    "notes": "第一页幻灯片，介绍主题",
                },
                {
                    "slide_number": 2,
                    "title": "构成规则",
                    "content": ["had + 过去分词", "肯定句、否定句、疑问句"],
                    "notes": "详细讲解构成规则",
                },
            ],
            "teaching_notes": "本节课学生掌握情况良好，需要加强练习。",
        }

    @pytest.fixture
    def template_vars(self):
        """模板变量"""
        return {
            "teacher_name": "张老师",
            "school": "XX中学",
            "date": "2026-02-07",
        }

    def test_generator_initialization(self, generator):
        """测试生成器初始化"""
        assert generator is not None
        assert generator.doc is None

    def test_generate_basic_document(self, generator, basic_content, template_vars):
        """测试生成基本文档"""
        result = generator.generate(basic_content, template_vars)

        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        # Word 文档应该以 PK 开头（ZIP 格式）
        assert result[:2] == b"PK"

    def test_generate_full_document(self, generator, full_content, template_vars):
        """测试生成完整文档"""
        result = generator.generate(full_content, template_vars)

        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:2] == b"PK"

    def test_generate_with_empty_objectives(self, generator, basic_content, template_vars):
        """测试空教学目标"""
        content = basic_content.copy()
        content["objectives"] = {}

        result = generator.generate(content, template_vars)
        assert result is not None
        assert isinstance(result, bytes)

    def test_generate_with_empty_vocabulary(self, generator, basic_content, template_vars):
        """测试空词汇表"""
        content = basic_content.copy()
        content["vocabulary"] = {}

        result = generator.generate(content, template_vars)
        assert result is not None
        assert isinstance(result, bytes)

    def test_generate_with_minimal_content(self, generator):
        """测试最小内容（只有标题）"""
        content = {"title": "测试教案"}
        template_vars = {"teacher_name": "老师"}

        result = generator.generate(content, template_vars)
        assert result is not None
        assert isinstance(result, bytes)

    def test_generate_with_missing_title_raises_error(self, generator, template_vars):
        """测试缺少标题时抛出异常"""
        content = {
            "level": "B1",
            "topic": "Grammar",
        }

        with pytest.raises(Exception, match="Word文档生成失败"):
            generator.generate(content, template_vars)

    def test_objectives_rendering_with_dict(self, generator, basic_content, template_vars):
        """测试字典格式的教学目标渲染"""
        content = basic_content.copy()
        content["objectives"] = {
            "language_knowledge": ["目标1", "目标2"],
        }

        result = generator.generate(content, template_vars)
        assert result is not None

    def test_objectives_rendering_with_list(self, generator, basic_content, template_vars):
        """测试列表格式的教学目标渲染"""
        content = basic_content.copy()
        content["objectives"] = {
            "language_knowledge": ["目标1", "目标2"],
        }

        result = generator.generate(content, template_vars)
        assert result is not None

    def test_vocabulary_table_rendering(self, generator, full_content, template_vars):
        """测试词汇表格渲染"""
        result = generator.generate(full_content, template_vars)
        assert result is not None

    def test_grammar_points_rendering(self, generator, full_content, template_vars):
        """测试语法点渲染"""
        result = generator.generate(full_content, template_vars)
        assert result is not None

    def test_teaching_structure_rendering(self, generator, full_content, template_vars):
        """测试教学流程渲染"""
        result = generator.generate(full_content, template_vars)
        assert result is not None

    def test_leveled_materials_rendering(self, generator, full_content, template_vars):
        """测试分层材料渲染"""
        result = generator.generate(full_content, template_vars)
        assert result is not None

    def test_exercises_rendering(self, generator, full_content, template_vars):
        """测试练习题渲染"""
        result = generator.generate(full_content, template_vars)
        assert result is not None

    def test_ppt_outline_rendering(self, generator, full_content, template_vars):
        """测试PPT大纲渲染"""
        result = generator.generate(full_content, template_vars)
        assert result is not None

    def test_teaching_notes_rendering(self, generator, full_content, template_vars):
        """测试教学反思渲染"""
        result = generator.generate(full_content, template_vars)
        assert result is not None

    def test_chinese_character_support(self, generator, basic_content, template_vars):
        """测试中文字符支持"""
        content = basic_content.copy()
        content["title"] = "中文教案标题测试"

        result = generator.generate(content, template_vars)
        assert result is not None

    def test_multiple_vocabulary_types(self, generator, basic_content, template_vars):
        """测试多种词性的词汇"""
        content = basic_content.copy()
        content["vocabulary"] = {
            "noun": [
                {
                    "word": "book",
                    "phonetic": "/bʊk/",
                    "part_of_speech": "n.",
                    "meaning_cn": "书",
                    "example_sentence": "This is a book.",
                }
            ],
            "verb": [
                {
                    "word": "read",
                    "phonetic": "/riːd/",
                    "part_of_speech": "v.",
                    "meaning_cn": "阅读",
                    "example_sentence": "I read books.",
                }
            ],
            "adj": [
                {
                    "word": "good",
                    "phonetic": "/ɡʊd/",
                    "part_of_speech": "adj.",
                    "meaning_cn": "好的",
                    "example_sentence": "It is good.",
                }
            ],
        }

        result = generator.generate(content, template_vars)
        assert result is not None

    def test_multiple_exercise_types(self, generator, basic_content, template_vars):
        """测试多种题型"""
        content = basic_content.copy()
        content["exercises"] = {
            "multiple_choice": [
                {
                    "question": "测试选择题",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "explanation": "解析",
                }
            ],
            "fill_blank": [
                {
                    "question": "测试填空题",
                    "correct_answer": "answer",
                    "explanation": "解析",
                }
            ],
            "essay": [
                {
                    "question": "测试写作题",
                    "correct_answer": "参考答案",
                    "explanation": "评分标准",
                }
            ],
        }

        result = generator.generate(content, template_vars)
        assert result is not None

    def test_document_size_is_reasonable(self, generator, full_content, template_vars):
        """测试文档大小合理"""
        result = generator.generate(full_content, template_vars)

        # 完整教案的 Word 文档大小应该在 10KB - 500KB 之间
        assert 10 * 1024 < len(result) < 500 * 1024

    def test_generate_without_optional_fields(self, generator, basic_content, template_vars):
        """测试不包含可选字段的内容"""
        content = {
            "title": "基本教案",
            "level": "A1",
            "topic": "Basic",
            "duration": 30,
        }

        result = generator.generate(content, template_vars)
        assert result is not None
        assert isinstance(result, bytes)

    def test_generate_with_long_text(self, generator, basic_content, template_vars):
        """测试包含长文本的内容"""
        content = basic_content.copy()
        long_text = "这是一个很长的文本。" * 100
        content["teaching_notes"] = long_text

        result = generator.generate(content, template_vars)
        assert result is not None
