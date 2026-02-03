"""
教案服务测试 - AI英语教学系统
测试教案生成、查询、更新、删除功能
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import LessonPlan
from app.schemas.lesson_plan import GenerateLessonPlanRequest
from app.services.lesson_plan_service import LessonPlanService


@pytest.fixture
def lesson_plan_service():
    """创建教案服务实例"""
    return LessonPlanService()


@pytest.fixture
def sample_generate_request():
    """创建示例生成教案请求"""
    return GenerateLessonPlanRequest(
        title="英语现在完成时教学",
        topic="现在完成时",
        level="B1",
        duration=45,
        target_exam="IELTS",
        student_count=20,
        focus_areas=["grammar", "reading"],
        include_leveled_materials=True,
        leveled_levels=["A1", "B1", "C1"],
        include_exercises=True,
        exercise_count=10,
        exercise_types=["multiple_choice", "fill_blank"],
        include_ppt=True,
    )


@pytest.fixture
def sample_ai_response():
    """创建示例AI响应"""
    return {
        "objectives": {
            "language_knowledge": [
                "掌握现在完成时的构成：have/has + 过去分词",
                "理解现在完成时的用法：表示过去发生的动作对现在的影响"
            ],
            "language_skills": {
                "listening": ["能听懂含有现在完成时的对话"],
                "speaking": ["能用现在完成时描述经历"],
                "reading": ["能理解含有现在完成时的文章"],
                "writing": ["能用现在完成时写作"]
            },
            "learning_strategies": [
                "通过时间轴理解现在完成时与一般过去时的区别",
                "通过例句归纳现在完成时的用法"
            ],
            "cultural_awareness": [
                "了解中英时态表达的差异"
            ],
            "emotional_attitudes": [
                "培养学生对英语时态学习的兴趣",
                "增强学生用英语表达的自信心"
            ]
        },
        "vocabulary": {
            "noun": [
                {
                    "word": "experience",
                    "phonetic": "/ɪkˈspɪəriəns/",
                    "part_of_speech": "n.",
                    "meaning_cn": "经历，经验",
                    "meaning_en": "something that happens to you or things you have done",
                    "example_sentence": "I have a lot of teaching experience.",
                    "example_translation": "我有丰富的教学经验。",
                    "collocations": ["work experience", "life experience", "gain experience"],
                    "synonyms": ["encounter", "undergo"],
                    "antonyms": ["inexperience"],
                    "difficulty": "B1"
                }
            ],
            "verb": [
                {
                    "word": "achieve",
                    "phonetic": "/əˈtʃiːv/",
                    "part_of_speech": "v.",
                    "meaning_cn": "实现，达到",
                    "meaning_en": "to successfully complete something or get a good result",
                    "example_sentence": "She has achieved her goal.",
                    "example_translation": "她已经实现了她的目标。",
                    "collocations": ["achieve success", "achieve a goal", "achieve a target"],
                    "synonyms": ["accomplish", "attain", "reach"],
                    "antonyms": ["fail", "lose"],
                    "difficulty": "B1"
                }
            ]
        },
        "grammar_points": [
            {
                "name": "现在完成时的构成",
                "description": "现在完成时由助动词have/has加上动词的过去分词构成",
                "rule": "肯定句：主语 + have/has + 过去分词\n否定句：主语 + have/has + not + 过去分词\n疑问句：Have/Has + 主语 + 过去分词？",
                "examples": [
                    "I have finished my homework.",
                    "She has visited London twice.",
                    "They haven't seen the movie yet."
                ],
                "common_mistakes": [
                    "混淆have/has的使用：第三人称单数用has，其他人称用have",
                    "忘记使用过去分词：不能说'I have go'，应该说'I have gone'"
                ],
                "practice_tips": [
                    "多读含有现在完成时的文章",
                    "用现在完成时写日记",
                    "与同学进行对话练习"
                ]
            }
        ],
        "structure": {
            "warm_up": {
                "phase": "warm-up",
                "title": "热身活动",
                "duration": 5,
                "description": "通过问答活动激活学生背景知识",
                "activities": [
                    "教师询问：What did you do yesterday?",
                    "学生回答，然后教师引出：What have you done today?"
                ],
                "teacher_actions": [
                    "提出问题",
                  "引导学生思考",
                  "引出本课主题"
                ],
                "student_actions": [
                    "回答问题",
                  "思考过去动作与现在的关系"
                ],
                "materials": ["PPT", "黑板"]
            },
            "presentation": {
                "phase": "presentation",
                "title": "呈现新知",
                "duration": 15,
                "description": "讲解现在完成时的构成和用法",
                "activities": [
                    "展示时间轴",
                    "讲解语法规则",
                    "展示例句"
                ],
                "teacher_actions": [
                    "讲解语法点",
                  "举例说明",
                  "解答疑问"
                ],
                "student_actions": [
                    "听讲",
                  "记笔记",
                  "提问"
                ],
                "materials": ["PPT", "讲义"]
            },
            "practice": [
                {
                    "phase": "practice",
                    "title": "练习活动1",
                    "duration": 10,
                    "description": "完成句子练习",
                    "activities": [
                        "学生完成练习题",
                        "同桌互查",
                        "教师讲解"
                    ],
                    "teacher_actions": [
                        "分发练习",
                      "巡视指导",
                      "讲解答案"
                    ],
                    "student_actions": [
                        "完成练习",
                      "互相检查",
                      "订正错误"
                    ],
                    "materials": ["练习题", "答案"]
                },
                {
                    "phase": "practice",
                    "title": "练习活动2",
                    "duration": 10,
                    "description": "角色扮演",
                    "activities": [
                        "学生两人一组",
                        "用现在完成时对话",
                        "展示对话"
                    ],
                    "teacher_actions": [
                        "说明活动要求",
                      "观察学生表现",
                      "给予反馈"
                    ],
                    "student_actions": [
                        "准备对话",
                      "进行表演",
                      "互相评价"
                    ],
                    "materials": ["角色卡片", "评分表"]
                }
            ],
            "production": {
                "phase": "production",
                "title": "产出活动",
                "duration": 5,
                "description": "学生自由运用现在完成时",
                "activities": [
                    "学生分享自己的经历",
                    "其他学生提问"
                ],
                "teacher_actions": [
                    "引导活动",
                  "记录错误",
                  "总结反馈"
                ],
                "student_actions": [
                    "分享经历",
                  "互相提问",
                  "自我纠正"
                ],
                "materials": ["话题卡"]
            },
            "summary": {
                "phase": "summary",
                "title": "课堂总结",
                "duration": 3,
                "description": "总结本课重点",
                "activities": [
                    "回顾现在完成时的用法",
                    "强调常见错误",
                    "布置作业"
                ],
                "teacher_actions": [
                    "总结知识点",
                  "布置作业",
                  "解答疑问"
                ],
                "student_actions": [
                    "听总结",
                  "记录作业",
                  "提问"
                ],
                "materials": ["PPT", "黑板"]
            },
            "homework": {
                "phase": "homework",
                "title": "课后作业",
                "duration": 2,
                "description": "布置课后练习",
                "activities": [
                    "完成练习册第10-12页",
                    "用现在完成时写10个句子"
                ],
                "teacher_actions": [
                    "说明作业要求",
                  "告知提交时间"
                ],
                "student_actions": [
                    "记录作业",
                  "询问疑问"
                ],
                "materials": ["练习册"]
            }
        },
        "leveled_materials": [
            {
                "level": "A1",
                "title": "My Day",
                "content": "I get up at 7 o'clock every morning. I have breakfast with my family. Then I go to school by bus. I have lunch at school. After school, I do my homework and watch TV. I go to bed at 10 o'clock.",
                "word_count": 45,
                "vocabulary_list": [],
                "comprehension_questions": [
                    "What time does the writer get up?",
                    "How does the writer go to school?"
                ],
                "difficulty_notes": "简单句为主，词汇基础，适合初学者"
            },
            {
                "level": "B1",
                "title": "A Memorable Day",
                "content": "Last Sunday was a special day for me. I went to the zoo with my friends. We saw many animals, such as lions, tigers, and elephants. The weather was sunny and warm. We took many photos and had a great time together. In the afternoon, we ate ice cream and talked about our favorite animals.",
                "word_count": 55,
                "vocabulary_list": [],
                "comprehension_questions": [
                    "Where did the writer go last Sunday?",
                    "What animals did they see?"
                ],
                "difficulty_notes": "使用过去时态，句子结构稍复杂，有并列句"
            },
            {
                "level": "C1",
                "title": "Environmental Conservation",
                "content": "Climate change has become one of the most pressing issues of our time. Rising global temperatures, melting ice caps, and extreme weather events are clear indicators of this crisis. Governments and individuals must take immediate action to reduce carbon emissions and promote sustainable practices. Small changes in our daily lives, such as using public transportation and reducing waste, can make a significant difference.",
                "word_count": 65,
                "vocabulary_list": [],
                "comprehension_questions": [
                    "What are some indicators of climate change mentioned?",
                    "What actions can individuals take?"
                ],
                "difficulty_notes": "使用高级词汇和复杂句型，涉及抽象概念"
            }
        ],
        "exercises": {
            "multiple_choice": [
                {
                    "id": "q1",
                    "type": "multiple_choice",
                    "question": "I _____ my homework already.",
                    "options": ["have finished", "finish", "finished", "finishing"],
                    "correct_answer": "have finished",
                    "explanation": "现在完成时由have/has + 过去分词构成，表示过去发生的动作对现在的影响",
                    "points": 1,
                    "difficulty": "B1"
                },
                {
                    "id": "q2",
                    "type": "multiple_choice",
                    "question": "She _____ to London twice.",
                    "options": ["has been", "have been", "is", "was"],
                    "correct_answer": "has been",
                    "explanation": "第三人称单数用has，be的过去分词是been",
                    "points": 1,
                    "difficulty": "B1"
                }
            ],
            "fill_blank": [
                {
                    "id": "q3",
                    "type": "fill_blank",
                    "question": "They _____ (not/see) the movie yet.",
                    "options": None,
                    "correct_answer": "haven't seen",
                    "explanation": "否定形式：have not + 过去分词，see的过去分词是seen",
                    "points": 1,
                    "difficulty": "B1"
                }
            ]
        },
        "ppt_outline": [
            {
                "slide_number": 1,
                "title": "现在完成时",
                "content": [
                    "学习目标：掌握现在完成时的构成和用法",
                    "重点：have/has + 过去分词",
                    "难点：与一般过去时的区别"
                ],
                "notes": "介绍本课学习目标和重点难点",
                "layout": "title_content"
            },
            {
                "slide_number": 2,
                "title": "现在完成时的构成",
                "content": [
                    "肯定句：主语 + have/has + 过去分词",
                    "否定句：主语 + have/has + not + 过去分词",
                    "疑问句：Have/Has + 主语 + 过去分词？"
                ],
                "notes": "讲解现在完成时的基本结构",
                "layout": "title_content"
            }
        ]
    }


class TestLessonPlanService:
    """教案服务测试类"""

    @pytest.mark.asyncio
    async def test_generate_lesson_plan_success(
        self, lesson_plan_service, sample_generate_request, sample_ai_response, db_session
    ):
        """测试成功生成教案"""
        teacher_id = uuid.uuid4()

        # Mock OpenAI客户端
        with patch.object(lesson_plan_service, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client

            # Mock API响应
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = str(sample_ai_response).replace("'", '"')
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            # 生成教案
            lesson_plan = await lesson_plan_service.generate_lesson_plan(
                db=db_session,
                teacher_id=teacher_id,
                request=sample_generate_request,
            )

            # 验证结果
            assert lesson_plan is not None
            assert lesson_plan.title == sample_generate_request.title
            assert lesson_plan.topic == sample_generate_request.topic
            assert lesson_plan.level == sample_generate_request.level
            assert lesson_plan.teacher_id == teacher_id
            assert lesson_plan.status == "generated"

    @pytest.mark.asyncio
    async def test_get_lesson_plan(
        self, lesson_plan_service, db_session
    ):
        """测试获取教案详情"""
        # 创建测试教案
        lesson_plan = LessonPlan(
            teacher_id=uuid.uuid4(),
            title="测试教案",
            topic="测试主题",
            level="B1",
            duration=45,
            status="generated",
        )
        db_session.add(lesson_plan)
        await db_session.commit()
        await db_session.refresh(lesson_plan)

        # 获取教案
        result = await lesson_plan_service.get_lesson_plan(db_session, lesson_plan.id)

        assert result is not None
        assert result.id == lesson_plan.id
        assert result.title == "测试教案"

    @pytest.mark.asyncio
    async def test_update_lesson_plan(
        self, lesson_plan_service, db_session
    ):
        """测试更新教案"""
        # 创建测试教案
        lesson_plan = LessonPlan(
            teacher_id=uuid.uuid4(),
            title="测试教案",
            topic="测试主题",
            level="B1",
            duration=45,
            status="generated",
        )
        db_session.add(lesson_plan)
        await db_session.commit()
        await db_session.refresh(lesson_plan)

        # 更新教案
        updates = {
            "title": "更新后的教案",
            "status": "completed",
            "teaching_notes": "这节课效果很好，学生参与度高"
        }

        result = await lesson_plan_service.update_lesson_plan(
            db_session,
            lesson_plan.id,
            updates
        )

        assert result is not None
        assert result.title == "更新后的教案"
        assert result.status == "completed"
        assert result.teaching_notes == "这节课效果很好，学生参与度高"

    @pytest.mark.asyncio
    async def test_delete_lesson_plan(
        self, lesson_plan_service, db_session
    ):
        """测试删除教案"""
        # 创建测试教案
        lesson_plan = LessonPlan(
            teacher_id=uuid.uuid4(),
            title="测试教案",
            topic="测试主题",
            level="B1",
            duration=45,
            status="generated",
        )
        db_session.add(lesson_plan)
        await db_session.commit()

        lesson_plan_id = lesson_plan.id

        # 删除教案
        success = await lesson_plan_service.delete_lesson_plan(db_session, lesson_plan_id)

        assert success is True

        # 验证已删除
        result = await lesson_plan_service.get_lesson_plan(db_session, lesson_plan_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_lesson_plans_with_filters(
        self, lesson_plan_service, db_session
    ):
        """测试带筛选条件的教案列表"""
        teacher_id = uuid.uuid4()

        # 创建多个测试教案
        for i in range(5):
            lesson_plan = LessonPlan(
                teacher_id=teacher_id,
                title=f"测试教案{i}",
                topic="测试主题",
                level="B1" if i % 2 == 0 else "A1",
                duration=45,
                status="generated" if i % 2 == 0 else "draft",
                target_exam="IELTS" if i % 3 == 0 else None,
            )
            db_session.add(lesson_plan)

        await db_session.commit()

        # 测试按等级筛选
        plans_b1, total_b1 = await lesson_plan_service.list_lesson_plans(
            db_session,
            teacher_id=teacher_id,
            level="B1",
        )
        assert len(plans_b1) == 3
        assert total_b1 == 3

        # 测试按状态筛选
        plans_generated, total_generated = await lesson_plan_service.list_lesson_plans(
            db_session,
            teacher_id=teacher_id,
            status="generated",
        )
        assert len(plans_generated) == 3
        assert total_generated == 3

    def test_build_lesson_prompt(
        self, lesson_plan_service, sample_generate_request
    ):
        """测试构建教案提示词"""
        prompt = lesson_plan_service._build_lesson_prompt(sample_generate_request)

        assert "英语现在完成时教学" in prompt
        assert "现在完成时" in prompt
        assert "B1" in prompt
        assert "45" in prompt
        assert "IELTS" in prompt
        assert "grammar" in prompt
        assert "reading" in prompt
        assert "JSON" in prompt

    def test_build_leveled_material_prompt(self, lesson_plan_service):
        """测试构建分层材料提示词"""
        base_content = "This is a simple text about daily routines."
        prompt = lesson_plan_service._build_leveled_material_prompt(base_content, "A1")

        assert "A1" in prompt
        assert base_content in prompt
        assert "vocabulary_list" in prompt
        assert "comprehension_questions" in prompt

    def test_build_exercise_prompt(self, lesson_plan_service):
        """测试构建练习题提示词"""
        prompt = lesson_plan_service._build_exercise_prompt(
            topic="现在完成时",
            level="B1",
            exercise_type="multiple_choice",
            count=5
        )

        assert "现在完成时" in prompt
        assert "B1" in prompt
        assert "multiple_choice" in prompt
        assert "5道" in prompt

    def test_parse_lesson_plan_response(
        self, lesson_plan_service, sample_generate_request
    ):
        """测试解析教案响应"""
        import json

        # 使用示例响应
        response_text = json.dumps(sample_ai_response)

        result = lesson_plan_service._parse_lesson_plan_response(
            response_text,
            sample_generate_request
        )

        assert "objectives" in result
        assert "vocabulary" in result
        assert "grammar_points" in result
        assert "structure" in result
        assert "exercises" in result
        assert "ppt_outline" in result
