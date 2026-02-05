"""
教案导出服务单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.services.lesson_plan_export_service import (
    LessonPlanExportService,
    get_lesson_plan_export_service
)


class TestLessonPlanExportService:
    """教案导出服务测试类"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return LessonPlanExportService()

    @pytest.fixture
    def sample_lesson_plan(self):
        """示例教案数据"""
        return {
            'id': 'test-id-123',
            'title': '日常问候与介绍',
            'topic': 'Greetings and Introductions',
            'level': 'A1',
            'duration': 45,
            'target_exam': 'CET4',
            'status': 'generated',
            'objectives': {
                'language_knowledge': ['掌握基本问候语', '了解自我介绍的方式'],
                'language_skills': {
                    'listening': ['听懂简单的问候语'],
                    'speaking': ['能够进行简单的自我介绍'],
                    'reading': ['阅读简单的对话'],
                    'writing': ['写出简单的自我介绍']
                },
                'learning_strategies': ['通过对话练习提高口语'],
                'cultural_awareness': ['了解英语国家的问候文化'],
                'emotional_attitudes': ['培养学习英语的兴趣']
            },
            'vocabulary': {
                'noun': [
                    {
                        'word': 'hello',
                        'phonetic': '/həˈloʊ/',
                        'part_of_speech': 'n.',
                        'meaning_cn': '你好',
                        'meaning_en': 'A greeting',
                        'example_sentence': 'Hello, how are you?',
                        'example_translation': '你好，你怎么样？',
                        'collocations': ['say hello', 'hello everyone'],
                        'synonyms': ['hi'],
                        'antonyms': ['goodbye'],
                        'difficulty': 'A1'
                    },
                    {
                        'word': 'name',
                        'phonetic': '/neɪm/',
                        'part_of_speech': 'n.',
                        'meaning_cn': '名字',
                        'meaning_en': 'The word by which a person is known',
                        'example_sentence': 'My name is John.',
                        'example_translation': '我的名字是约翰。',
                        'collocations': ['first name', 'last name'],
                        'synonyms': [],
                        'antonyms': [],
                        'difficulty': 'A1'
                    }
                ],
                'verb': [
                    {
                        'word': 'meet',
                        'phonetic': '/miːt/',
                        'part_of_speech': 'v.',
                        'meaning_cn': '遇见',
                        'meaning_en': 'To come into the presence of someone',
                        'example_sentence': 'Nice to meet you.',
                        'example_translation': '很高兴见到你。',
                        'collocations': ['meet someone', 'meet for the first time'],
                        'synonyms': [],
                        'antonyms': [],
                        'difficulty': 'A1'
                    }
                ]
            },
            'grammar_points': [
                {
                    'name': '一般现在时',
                    'description': '描述经常性或习惯性的动作',
                    'rule': '主语+动词原形/第三人称单数+s',
                    'examples': ['I am a student.', 'She goes to school every day.'],
                    'common_mistakes': ['I am not going every day.'],
                    'practice_tips': ['注意第三人称单数的变化']
                }
            ],
            'teaching_structure': {
                'warm_up': {
                    'phase': 'warm-up',
                    'title': '热身活动',
                    'duration': 5,
                    'description': '通过歌曲或游戏引起学生兴趣',
                    'activities': ['播放问候歌', '师生互动'],
                    'teacher_actions': ['播放歌曲', '引导学生'],
                    'student_actions': ['跟唱', '参与互动'],
                    'materials': ['音频文件', '投影设备']
                },
                'presentation': {
                    'phase': 'presentation',
                    'title': '新知识呈现',
                    'duration': 15,
                    'description': '介绍问候语和自我介绍的表达方式',
                    'activities': ['展示对话', '解释语法'],
                    'teacher_actions': ['演示对话', '讲解语法点'],
                    'student_actions': ['观察', '记笔记'],
                    'materials': ['对话文本', 'PPT']
                },
                'practice': [
                    {
                        'phase': 'practice',
                        'title': '课堂练习',
                        'duration': 15,
                        'description': '学生分组练习对话',
                        'activities': ['角色扮演', '小组练习'],
                        'teacher_actions': ['巡视指导', '纠正错误'],
                        'student_actions': ['练习对话', '相互纠正'],
                        'materials': ['练习材料']
                    }
                ],
                'production': {
                    'phase': 'production',
                    'title': '知识运用',
                    'duration': 8,
                    'description': '学生展示所学内容',
                    'activities': ['对话展示', '自我介绍'],
                    'teacher_actions': ['点评', '鼓励'],
                    'student_actions': ['展示', '评价'],
                    'materials': []
                },
                'summary': {
                    'phase': 'summary',
                    'title': '课堂总结',
                    'duration': 2,
                    'description': '总结本课重点',
                    'activities': ['回顾知识点', '布置作业'],
                    'teacher_actions': ['总结', '布置作业'],
                    'student_actions': ['回顾', '记录作业'],
                    'materials': ['作业单']
                }
            },
            'leveled_materials': [
                {
                    'level': 'A1',
                    'title': '简单的问候',
                    'content': 'Hello! My name is Tom. Nice to meet you. How are you? I am fine, thank you.',
                    'word_count': 20,
                    'vocabulary_list': [
                        {
                            'word': 'hello',
                            'phonetic': '/həˈloʊ/',
                            'part_of_speech': 'n.',
                            'meaning_cn': '你好',
                            'example_sentence': 'Hello, everyone.',
                            'example_translation': '大家好。',
                            'difficulty': 'A1'
                        }
                    ],
                    'comprehension_questions': [
                        'What is the speaker\'s name?',
                        'How does the speaker greet others?'
                    ],
                    'difficulty_notes': '使用最基础的词汇和句型'
                }
            ],
            'exercises': {
                'multiple_choice': [
                    {
                        'id': 'q1',
                        'type': 'multiple_choice',
                        'question': 'What is the correct greeting?',
                        'options': ['Good night', 'Goodbye', 'Hello', 'Thank you'],
                        'correct_answer': 'Hello',
                        'explanation': 'Hello是最常用的问候语',
                        'points': 1,
                        'difficulty': 'A1'
                    },
                    {
                        'id': 'q2',
                        'type': 'multiple_choice',
                        'question': 'How do you ask someone\'s name politely?',
                        'options': ['What is you?', 'What are you?', 'What is your name?', 'Who name?'],
                        'correct_answer': 'What is your name?',
                        'explanation': 'What is your name?是最礼貌的询问方式',
                        'points': 1,
                        'difficulty': 'A1'
                    }
                ],
                'fill_blank': [
                    {
                        'id': 'q3',
                        'type': 'fill_blank',
                        'question': '____ to meet you.',
                        'options': ['Nice', 'Good', 'Hello', 'Thanks'],
                        'correct_answer': 'Nice',
                        'explanation': 'Nice to meet you是固定搭配',
                        'points': 1,
                        'difficulty': 'A1'
                    }
                ]
            },
            'ppt_outline': [
                {
                    'slide_number': 1,
                    'title': '日常问候与介绍',
                    'content': [
                        '课程标题：日常问候与介绍',
                        '教师：AI英语教学系统',
                        '等级：A1',
                        '时长：45分钟'
                    ],
                    'layout': 'title'
                },
                {
                    'slide_number': 2,
                    'title': '教学目标',
                    'content': [
                        '掌握基本问候语',
                        '能够进行自我介绍',
                        '了解英语国家的问候文化'
                    ],
                    'layout': 'title_content'
                },
                {
                    'slide_number': 3,
                    'title': '热身活动',
                    'content': [
                        '播放问候歌',
                        '师生互动',
                        '引起学习兴趣'
                    ],
                    'layout': 'title_content'
                }
            ],
            'resources': {
                'audio': ['问候歌曲音频', '对话录音'],
                'video': ['教学视频'],
                'worksheets': ['练习题单', '词汇表'],
                'digital': ['PPT课件', '互动软件']
            },
            'teaching_notes': '本课重点是让学生掌握基本的问候用语和自我介绍方式。可以通过歌曲、游戏等活动增加课堂趣味性。',
            'generation_time_ms': 3500,
            'created_at': '2026-02-05T10:00:00',
            'updated_at': '2026-02-05T10:00:00'
        }

    @pytest.fixture
    def sample_teacher(self):
        """示例教师数据"""
        return {
            'username': '张老师',
            'email': 'zhang@school.edu.cn',
            'role': 'teacher'
        }

    @pytest.mark.asyncio
    async def test_export_as_pdf_basic(self, service, sample_lesson_plan, sample_teacher):
        """测试PDF导出基本功能"""
        # 测试默认选项
        result = await service.export_as_pdf(sample_lesson_plan, sample_teacher)

        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_export_as_pdf_with_options(self, service, sample_lesson_plan, sample_teacher):
        """测试PDF导出自定义选项"""
        options = {
            'include_objectives': True,
            'include_structure': True,
            'include_vocabulary': True,
            'include_grammar': True,
            'include_materials': True,
            'include_exercises': True,
            'include_ppt_outline': True,
        }

        result = await service.export_as_pdf(sample_lesson_plan, sample_teacher, options)

        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_export_as_pdf_minimal(self, service, sample_lesson_plan, sample_teacher):
        """测试最小选项PDF导出"""
        options = {
            'include_objectives': False,
            'include_structure': False,
            'include_vocabulary': False,
            'include_grammar': False,
            'include_materials': False,
            'include_exercises': False,
            'include_ppt_outline': False,
        }

        result = await service.export_as_pdf(sample_lesson_plan, sample_teacher, options)

        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_export_as_markdown_basic(self, service, sample_lesson_plan, sample_teacher):
        """测试Markdown导出基本功能"""
        result = await service.export_as_markdown(sample_lesson_plan, sample_teacher)

        assert isinstance(result, str)
        assert len(result) > 0
        assert '# 日常问候与介绍' in result
        assert '基本信息' in result
        assert '教学目标' in result

    @pytest.mark.asyncio
    async def test_export_as_markdown_minimal(self, service, sample_lesson_plan, sample_teacher):
        """测试最小选项Markdown导出"""
        options = {
            'include_objectives': False,
            'include_structure': False,
            'include_vocabulary': False,
            'include_grammar': False,
            'include_materials': False,
            'include_exercises': False,
            'include_ppt_outline': False,
        }

        result = await service.export_as_markdown(sample_lesson_plan, sample_teacher, options)

        assert isinstance(result, str)
        assert len(result) > 0
        assert '# 日常问候与介绍' in result
        assert '基本信息' in result
        # 确保没有包含被禁用部分
        assert '教学目标' not in result

    @pytest.mark.asyncio
    async def test_export_ppt_outline_json(self, service, sample_lesson_plan):
        """测试PPT大纲JSON导出"""
        result = await service.export_ppt_outline(sample_lesson_plan, format_type='json')

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]['title'] == '日常问候与介绍'
        assert result[0]['slide_number'] == 1

    @pytest.mark.asyncio
    async def test_export_ppt_outline_markdown(self, service, sample_lesson_plan):
        """测试PPT大纲Markdown导出"""
        result = await service.export_ppt_outline(sample_lesson_plan, format_type='markdown')

        assert isinstance(result, str)
        assert len(result) > 0
        assert '# PPT大纲' in result
        assert '日常问候与介绍' in result

    @pytest.mark.asyncio
    async def test_export_ppt_outline_empty(self, service):
        """测试空PPT大纲导出"""
        lesson_plan = {'title': 'Test', 'ppt_outline': []}

        result_json = await service.export_ppt_outline(lesson_plan, format_type='json')
        result_md = await service.export_ppt_outline(lesson_plan, format_type='markdown')

        assert result_json == []
        assert '暂无内容' in result_md

    def test_create_presentation_slides_basic(self, service, sample_lesson_plan):
        """测试创建演示幻灯片"""
        slides = service.create_presentation_slides(sample_lesson_plan)

        assert isinstance(slides, list)
        assert len(slides) == 3
        assert slides[0]['title'] == '日常问候与介绍'
        assert slides[0]['slide_number'] == 1
        assert 'content' in slides[0]
        assert 'layout' in slides[0]

    def test_create_presentation_slides_custom_outline(self, service, sample_lesson_plan):
        """测试使用自定义大纲创建幻灯片"""
        custom_outline = [
            {
                'slide_number': 1,
                'title': 'Custom Slide',
                'content': ['Custom content'],
                'notes': 'Custom notes',
                'layout': 'title_content'
            }
        ]

        slides = service.create_presentation_slides(sample_lesson_plan, custom_outline)

        assert len(slides) == 1
        assert slides[0]['title'] == 'Custom Slide'

    def test_create_presentation_slides_no_outline(self, service):
        """测试没有PPT大纲时生成基本大纲"""
        lesson_plan = {
            'title': 'Test Lesson',
            'topic': 'Test Topic',
            'level': 'A1',
            'duration': 45,
            'teaching_structure': {
                'warm_up': {'title': 'Warm up', 'activities': []},
                'presentation': {'title': 'Presentation', 'activities': []}
            }
        }

        slides = service.create_presentation_slides(lesson_plan)

        assert len(slides) > 0
        assert slides[0]['title'] == 'Test Lesson'

    @pytest.mark.asyncio
    async def test_export_as_pdf_invalid_lesson_plan(self, service, sample_teacher):
        """测试无效教案数据"""
        invalid_lesson_plan = {'title': ''}  # 缺少必要字段

        with pytest.raises(ValueError, match="教案标题不能为空"):
            await service.export_as_pdf(invalid_lesson_plan, sample_teacher)

    @pytest.mark.asyncio
    async def test_export_as_markdown_invalid_lesson_plan(self, service, sample_teacher):
        """测试无效教案Markdown导出"""
        invalid_lesson_plan = {'title': ''}

        with pytest.raises(ValueError, match="教案标题不能为空"):
            await service.export_as_markdown(invalid_lesson_plan, sample_teacher)

    def test_service_singleton(self):
        """测试服务单例模式"""
        service1 = get_lesson_plan_export_service()
        service2 = get_lesson_plan_export_service()

        assert service1 is service2

    @pytest.mark.asyncio
    async def test_markdown_content_structure(self, service, sample_lesson_plan, sample_teacher):
        """测试Markdown内容的结构完整性"""
        result = await service.export_as_markdown(sample_lesson_plan, sample_teacher)

        # 检查基本结构
        assert '# 日常问候与介绍' in result
        assert '基本信息' in result
        assert '教学目标' in result
        assert '教学流程' in result
        assert '核心词汇' in result
        assert '语法点' in result
        assert '练习题' in result
        assert 'PPT大纲' in result

        # 检查表格格式
        assert '| 单词 | 音标 | 词性 |' in result
        assert '| hello | /həˈloʊ/ | n. |' in result

        # 检查列表格式
        assert '## 教学目标' in result
        assert '### Language Knowledge' in result or '### 语言知识' in result

    @pytest.mark.asyncio
    async def test_vocabulary_rendering(self, service, sample_lesson_plan, sample_teacher):
        """测试词汇表渲染"""
        result = await service.export_as_markdown(sample_lesson_plan, sample_teacher)

        # 检查词汇表渲染
        assert '## 核心词汇' in result
        assert '### Noun' in result or '### 名词' in result
        assert '| hello | /həˈloʊ/ | n. | 你好 |' in result
        assert '| name | /neɪm/ | n. | 名字 |' in result

    @pytest.mark.asyncio
    async def test_grammar_rendering(self, service, sample_lesson_plan, sample_teacher):
        """测试语法点渲染"""
        result = await service.export_as_markdown(sample_lesson_plan, sample_teacher)

        # 检查语法点渲染
        assert '## 语法点' in result
        assert '### 一般现在时' in result
        assert '**描述**: 描述经常性或习惯性的动作' in result
        assert '**规则**: 主语+动词原形/第三人称单数+s' in result
        assert '**例句**' in result

    @pytest.mark.asyncio
    async def test_structure_rendering(self, service, sample_lesson_plan, sample_teacher):
        """测试教学流程渲染"""
        result = await service.export_as_markdown(sample_lesson_plan, sample_teacher)

        # 检查教学流程渲染
        assert '## 教学流程' in result
        assert '### Warm Up' in result or '### 热身' in result
        assert '**时长**: 5分钟' in result
        assert '**活动**' in result
        assert '- 播放问候歌' in result

    @pytest.mark.asyncio
    async def test_ppt_outline_section(self, service, sample_lesson_plan, sample_teacher):
        """测试PPT大纲部分渲染"""
        result = await service.export_as_markdown(sample_lesson_plan, sample_teacher)

        # 检查PPT大纲渲染
        assert '## PPT大纲' in result
        assert '| 幻灯片 | 标题 | 内容要点 |' in result
        assert '| 1 | 日常问候与介绍 |' in result
        assert '| 2 | 教学目标 |' in result


class TestLessonPlanExportServiceIntegration:
    """教案导出服务集成测试"""

    @pytest.mark.asyncio
    async def test_full_export_workflow(self):
        """测试完整导出工作流"""
        # 这个测试需要完整的数据库和文件IO，实际环境中运行
        pass

    @pytest.mark.asyncio
    async def test_pdf_with_special_characters(self):
        """测试包含特殊字符的PDF导出"""
        # 测试中文字符、特殊符号等
        pass

    @pytest.mark.asyncio
    async def test_large_lesson_plan_export(self):
        """测试大型教案导出性能"""
        # 创建大型教案数据进行性能测试
        pass
