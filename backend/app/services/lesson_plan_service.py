"""
教案生成服务 - AI英语教学系统
使用ZhipuAI驱动的教案生成功能
"""
import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.models import LessonPlan, LessonPlanTemplate
from app.schemas.lesson_plan import (
    ExerciseItem,
    GenerateLessonPlanRequest,
    GrammarPoint,
    LeveledMaterial,
    LessonPlanObjectives,
    LessonPlanStructure,
    PPTSlide,
    TeachingStep,
    VocabularyItem,
)
from app.services.zhipu_service import ZhipuAIService


class LessonPlanGenerationResult(BaseModel):
    """教案生成结果"""
    objectives: Dict[str, Any]
    vocabulary: Dict[str, List[Dict]]
    grammar_points: List[Dict]
    structure: Dict[str, Any]
    leveled_materials: List[Dict]
    exercises: Dict[str, List[Dict]]
    ppt_outline: List[Dict]


class LessonPlanService:
    """
    教案生成服务类
    使用ZhipuAI GLM-4.7生成完整教案
    """

    def __init__(self):
        """初始化教案服务"""
        self.zhipu_service = ZhipuAIService()
        self.model = settings.ZHIPUAI_MODEL
        self.temperature = settings.ZHIPUAI_TEMPERATURE
        self.max_tokens = settings.ZHIPUAI_MAX_TOKENS

    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def generate_lesson_plan(
        self,
        db: AsyncSession,
        teacher_id: uuid.UUID,
        request: GenerateLessonPlanRequest,
    ) -> LessonPlan:
        """
        生成完整教案

        Args:
            db: 数据库会话
            teacher_id: 教师ID
            request: 生成教案请求

        Returns:
            LessonPlan: 生成的教案

        Raises:
            ValueError: 如果输入数据无效
            ConnectionError: 如果API调用失败
        """
        # 开始计时
        start_time = time.time()

        # 使用简化版prompt以加快生成速度
        prompt = self._build_simple_lesson_prompt(request)

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个专业的英语教学专家，拥有20年的英语教学经验。"
                    "你擅长根据教师的需求，生成实用、简洁的英语教案。"
                    "教案需要符合CEFR标准，结合目标考试特点。"
                    "请严格按照JSON格式返回，确保JSON完整有效。"
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            # 调用AI生成教案，使用长超时（10分钟）
            response_text = await self._call_zhipu_json(messages, use_long_timeout=True)

            # 解析响应
            result = self._parse_lesson_plan_response(response_text, request)

            # 创建教案记录
            lesson_plan = LessonPlan(
                teacher_id=teacher_id,
                title=request.title,
                topic=request.topic,
                level=request.level,
                duration=request.duration,
                target_exam=request.target_exam,
                status="generated",
                ai_generation_params=request.model_dump(),
                objectives=result.get("objectives", {}),
                vocabulary=result.get("vocabulary", {}),
                grammar_points=result.get("grammar_points", {}),
                teaching_structure=result.get("structure", {}),
                leveled_materials=result.get("leveled_materials", {}),
                exercises=result.get("exercises", {}),
                ppt_outline=result.get("ppt_outline", {}),
                generation_time_ms=int((time.time() - start_time) * 1000),
                last_generated_at=datetime.utcnow(),
            )

            db.add(lesson_plan)
            await db.commit()
            await db.refresh(lesson_plan)

            return lesson_plan

        except Exception as e:
            raise ConnectionError(f"教案生成失败: {str(e)}")

    async def generate_difficulty_levels(
        self,
        db: AsyncSession,
        lesson_plan_id: uuid.UUID,
        base_content: str,
        target_levels: List[str],
    ) -> List[LeveledMaterial]:
        """
        生成分层阅读材料

        Args:
            db: 数据库会话
            lesson_plan_id: 教案ID
            base_content: 基础内容
            target_levels: 目标等级列表

        Returns:
            List[LeveledMaterial]: 分层材料列表
        """
        materials = []

        for level in target_levels:
            prompt = self._build_leveled_material_prompt(base_content, level)

            messages = [
                {
                    "role": "system",
                    "content": (
                        f"你是一个专业的英语教材编写专家。"
                        f"请根据CEFR {level}等级标准，改写以下内容。"
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            try:
                response_text = await self._call_zhipu_json(messages)
                material_data = json.loads(response_text)
                materials.append(LeveledMaterial(**material_data))
            except Exception as e:
                # 如果单个等级生成失败，记录但继续
                print(f"生成{level}等级材料失败: {str(e)}")
                continue

        return materials

    async def generate_exercises(
        self,
        db: AsyncSession,
        lesson_plan_id: uuid.UUID,
        topic: str,
        level: str,
        exercise_types: List[str],
        count: int,
    ) -> Dict[str, List[ExerciseItem]]:
        """
        根据考点生成练习题

        Args:
            db: 数据库会话
            lesson_plan_id: 教案ID
            topic: 主题
            level: 等级
            exercise_types: 练习题型
            count: 每种题型的数量

        Returns:
            Dict[str, List[ExerciseItem]]: 按题型分组的练习题
        """
        exercises = {}

        for exercise_type in exercise_types:
            prompt = self._build_exercise_prompt(topic, level, exercise_type, count)

            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是一个专业的英语教学专家。"
                        "请根据主题和等级，生成高质量的练习题。"
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            try:
                response_text = await self._call_zhipu_json(messages)
                exercise_data = json.loads(response_text)
                exercises[exercise_type] = [
                    ExerciseItem(**item) for item in exercise_data.get("exercises", [])
                ]
            except Exception as e:
                print(f"生成{exercise_type}题型失败: {str(e)}")
                exercises[exercise_type] = []

        return exercises

    async def generate_ppt_outline(
        self,
        db: AsyncSession,
        lesson_plan_id: uuid.UUID,
        structure: LessonPlanStructure,
    ) -> List[PPTSlide]:
        """
        生成PPT大纲

        Args:
            db: 数据库会话
            lesson_plan_id: 教案ID
            structure: 教学流程

        Returns:
            List[PPTSlide]: PPT幻灯片列表
        """
        prompt = self._build_ppt_prompt(structure)

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个专业的教学PPT设计师。"
                    "请根据教学流程，设计清晰、美观的PPT大纲。"
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            response_text = await self._call_zhipu_json(messages)
            ppt_data = json.loads(response_text)
            return [PPTSlide(**slide) for slide in ppt_data.get("slides", [])]
        except Exception as e:
            print(f"生成PPT大纲失败: {str(e)}")
            return []

    def _build_lesson_prompt(self, request: GenerateLessonPlanRequest) -> str:
        """
        构建教案生成提示词

        Args:
            request: 生成教案请求

        Returns:
            str: 构建的提示词
        """
        prompt_parts = []

        # 基本信息
        prompt_parts.append("# 教案生成请求\n")
        prompt_parts.append(f"## 基本信息\n")
        prompt_parts.append(f"- 教案标题: {request.title}")
        prompt_parts.append(f"- 教学主题: {request.topic}")
        prompt_parts.append(f"- CEFR等级: {request.level}")
        prompt_parts.append(f"- 课程时长: {request.duration}分钟")
        if request.target_exam:
            prompt_parts.append(f"- 目标考试: {request.target_exam}")
        if request.student_count:
            prompt_parts.append(f"- 学生人数: {request.student_count}")

        # 重点关注
        if request.focus_areas:
            prompt_parts.append(f"\n## 重点关注领域\n")
            for area in request.focus_areas:
                prompt_parts.append(f"- {area}")

        # 自定义学习目标
        if request.learning_objectives:
            prompt_parts.append(f"\n## 自定义学习目标\n")
            for obj in request.learning_objectives:
                prompt_parts.append(f"- {obj}")

        # 生成要求
        prompt_parts.append(f"\n## 生成要求\n")
        prompt_parts.append(f"- 包含分层阅读材料: {'是' if request.include_leveled_materials else '否'}")
        if request.include_leveled_materials:
            prompt_parts.append(f"- 分层等级: {', '.join(request.leveled_levels)}")
        prompt_parts.append(f"- 包含练习题: {'是' if request.include_exercises else '否'}")
        if request.include_exercises:
            prompt_parts.append(f"- 练习题数量: {request.exercise_count}")
            prompt_parts.append(f"- 练习题型: {', '.join(request.exercise_types)}")
        prompt_parts.append(f"- 包含PPT大纲: {'是' if request.include_ppt else '否'}")

        # 额外要求
        if request.additional_requirements:
            prompt_parts.append(f"\n## 额外要求\n")
            prompt_parts.append(request.additional_requirements)

        # JSON格式要求
        prompt_parts.append(f"\n## 输出格式\n")
        prompt_parts.append("请严格按照以下JSON格式返回：\n")
        prompt_parts.append("```json\n")
        prompt_parts.append("{\n")
        prompt_parts.append('  "objectives": {\n')
        prompt_parts.append('    "language_knowledge": ["知识目标1", "知识目标2"],\n')
        prompt_parts.append('    "language_skills": {\n')
        prompt_parts.append('      "listening": ["听力技能1"],\n')
        prompt_parts.append('      "speaking": ["口语技能1"],\n')
        prompt_parts.append('      "reading": ["阅读技能1"],\n')
        prompt_parts.append('      "writing": ["写作技能1"]\n')
        prompt_parts.append('    },\n')
        prompt_parts.append('    "learning_strategies": ["策略1"],\n')
        prompt_parts.append('    "cultural_awareness": ["文化意识1"],\n')
        prompt_parts.append('    "emotional_attitudes": ["情感态度1"]\n')
        prompt_parts.append('  },\n')
        prompt_parts.append('  "vocabulary": {\n')
        prompt_parts.append('    "noun": [\n')
        prompt_parts.append('      {\n')
        prompt_parts.append('        "word": "单词",\n')
        prompt_parts.append('        "phonetic": "/音标/",\n')
        prompt_parts.append('        "part_of_speech": "n.",\n')
        prompt_parts.append('        "meaning_cn": "中文释义",\n')
        prompt_parts.append('        "meaning_en": "English definition",\n')
        prompt_parts.append('        "example_sentence": "例句",\n')
        prompt_parts.append('        "example_translation": "例句翻译",\n')
        prompt_parts.append('        "collocations": ["搭配1"],\n')
        prompt_parts.append('        "synonyms": ["同义词"],\n')
        prompt_parts.append('        "antonyms": ["反义词"],\n')
        prompt_parts.append('        "difficulty": "A1"\n')
        prompt_parts.append('      }\n')
        prompt_parts.append('    ]\n')
        prompt_parts.append('  },\n')
        prompt_parts.append('  "grammar_points": [\n')
        prompt_parts.append('    {\n')
        prompt_parts.append('      "name": "语法点名称",\n')
        prompt_parts.append('      "description": "描述",\n')
        prompt_parts.append('      "rule": "规则",\n')
        prompt_parts.append('      "examples": ["例句1"],\n')
        prompt_parts.append('      "common_mistakes": ["错误1"],\n')
        prompt_parts.append('      "practice_tips": ["建议1"]\n')
        prompt_parts.append('    }\n')
        prompt_parts.append('  ],\n')
        prompt_parts.append('  "structure": {\n')
        prompt_parts.append('    "warm_up": {...},\n')
        prompt_parts.append('    "presentation": {...},\n')
        prompt_parts.append('    "practice": [...],\n')
        prompt_parts.append('    "production": {...},\n')
        prompt_parts.append('    "summary": {...},\n')
        prompt_parts.append('    "homework": {...}\n')
        prompt_parts.append('  },\n')
        if request.include_leveled_materials:
            prompt_parts.append('  "leveled_materials": [\n')
            prompt_parts.append('    {\n')
            prompt_parts.append('      "level": "A1",\n')
            prompt_parts.append('      "title": "标题",\n')
            prompt_parts.append('      "content": "内容",\n')
            prompt_parts.append('      "word_count": 100,\n')
            prompt_parts.append('      "vocabulary_list": [],\n')
            prompt_parts.append('      "comprehension_questions": [],\n')
            prompt_parts.append('      "difficulty_notes": "说明"\n')
            prompt_parts.append('    }\n')
            prompt_parts.append('  ],\n')
        prompt_parts.append('  "exercises": {\n')
        prompt_parts.append('    "multiple_choice": [\n')
        prompt_parts.append('      {\n')
        prompt_parts.append('        "id": "q1",\n')
        prompt_parts.append('        "type": "multiple_choice",\n')
        prompt_parts.append('        "question": "题目",\n')
        prompt_parts.append('        "options": ["A", "B", "C", "D"],\n')
        prompt_parts.append('        "correct_answer": "A",\n')
        prompt_parts.append('        "explanation": "解析",\n')
        prompt_parts.append('        "points": 1,\n')
        prompt_parts.append('        "difficulty": "A1"\n')
        prompt_parts.append('      }\n')
        prompt_parts.append('    ]\n')
        prompt_parts.append('  },\n')
        prompt_parts.append('  "ppt_outline": [\n')
        prompt_parts.append('    {\n')
        prompt_parts.append('      "slide_number": 1,\n')
        prompt_parts.append('      "title": "幻灯片标题",\n')
        prompt_parts.append('      "content": ["内容要点"],\n')
        prompt_parts.append('      "notes": "备注",\n')
        prompt_parts.append('      "layout": "title_content"\n')
        prompt_parts.append('    }\n')
        prompt_parts.append('  ]\n')
        prompt_parts.append("}\n")
        prompt_parts.append("```\n")

        return "".join(prompt_parts)

    def _build_simple_lesson_prompt(self, request: GenerateLessonPlanRequest) -> str:
        """
        构建简化版教案生成提示词（用于快速生成）

        简化版只包含核心字段，减少生成时间和token消耗。

        Args:
            request: 生成教案请求

        Returns:
            str: 构建的提示词
        """
        prompt_parts = []

        # 基本信息
        prompt_parts.append("# 教案生成请求\n")
        prompt_parts.append(f"标题: {request.title}\n")
        prompt_parts.append(f"主题: {request.topic}\n")
        prompt_parts.append(f"等级: {request.level}\n")
        prompt_parts.append(f"时长: {request.duration}分钟\n")
        if request.target_exam:
            prompt_parts.append(f"目标考试: {request.target_exam}\n")

        # 生成要求
        if request.focus_areas:
            prompt_parts.append(f"重点关注: {', '.join(request.focus_areas)}\n")

        prompt_parts.append("\n请生成简洁实用的教案，返回JSON格式：\n")
        prompt_parts.append("```json\n")
        prompt_parts.append("{\n")
        prompt_parts.append('  "objectives": {\n')
        prompt_parts.append('    "language_knowledge": ["知识目标"],\n')
        prompt_parts.append('    "language_skills": {\n')
        prompt_parts.append('      "listening": ["听力目标"],\n')
        prompt_parts.append('      "speaking": ["口语目标"],\n')
        prompt_parts.append('      "reading": ["阅读目标"],\n')
        prompt_parts.append('      "writing": ["写作目标"]\n')
        prompt_parts.append('    },\n')
        prompt_parts.append('    "learning_strategies": ["学习策略"],\n')
        prompt_parts.append('    "cultural_awareness": ["文化意识"],\n')
        prompt_parts.append('    "emotional_attitudes": ["情感态度"]\n')
        prompt_parts.append('  },\n')
        prompt_parts.append('  "vocabulary": {\n')
        prompt_parts.append('    "noun": [\n')
        prompt_parts.append('      {\n')
        prompt_parts.append('        "word": "单词",\n')
        prompt_parts.append('        "phonetic": "/音标/",\n')
        prompt_parts.append('        "part_of_speech": "n.",\n')
        prompt_parts.append('        "meaning_cn": "中文释义",\n')
        prompt_parts.append('        "meaning_en": "英文释义",\n')
        prompt_parts.append('        "example_sentence": "例句",\n')
        prompt_parts.append('        "example_translation": "例句翻译",\n')
        prompt_parts.append('        "collocations": [],\n')
        prompt_parts.append('        "synonyms": [],\n')
        prompt_parts.append('        "antonyms": [],\n')
        prompt_parts.append('        "difficulty": "A1"\n')
        prompt_parts.append('      }\n')
        prompt_parts.append('    ]\n')
        prompt_parts.append('  },\n')
        prompt_parts.append('  "grammar_points": [\n')
        prompt_parts.append('    {\n')
        prompt_parts.append('      "name": "语法点",\n')
        prompt_parts.append('      "description": "描述",\n')
        prompt_parts.append('      "rule": "规则",\n')
        prompt_parts.append('      "examples": ["例1"],\n')
        prompt_parts.append('      "common_mistakes": [],\n')
        prompt_parts.append('      "practice_tips": []\n')
        prompt_parts.append('    }\n')
        prompt_parts.append('  ],\n')
        prompt_parts.append('  "structure": {\n')
        prompt_parts.append('    "warm_up": {\n')
        prompt_parts.append('      "phase": "warm-up",\n')
        prompt_parts.append('      "title": "热身",\n')
        prompt_parts.append('      "duration": 5,\n')
        prompt_parts.append('      "description": "说明",\n')
        prompt_parts.append('      "activities": [],\n')
        prompt_parts.append('      "teacher_actions": [],\n')
        prompt_parts.append('      "student_actions": [],\n')
        prompt_parts.append('      "materials": []\n')
        prompt_parts.append('    },\n')
        prompt_parts.append('    "presentation": {\n')
        prompt_parts.append('      "phase": "presentation",\n')
        prompt_parts.append('      "title": "讲解",\n')
        prompt_parts.append('      "duration": 15,\n')
        prompt_parts.append('      "description": "说明",\n')
        prompt_parts.append('      "activities": [],\n')
        prompt_parts.append('      "teacher_actions": [],\n')
        prompt_parts.append('      "student_actions": [],\n')
        prompt_parts.append('      "materials": []\n')
        prompt_parts.append('    },\n')
        prompt_parts.append('    "practice": [\n')
        prompt_parts.append('      {\n')
        prompt_parts.append('        "phase": "practice",\n')
        prompt_parts.append('        "title": "练习",\n')
        prompt_parts.append('        "duration": 10,\n')
        prompt_parts.append('        "description": "说明",\n')
        prompt_parts.append('        "activities": [],\n')
        prompt_parts.append('        "teacher_actions": [],\n')
        prompt_parts.append('        "student_actions": [],\n')
        prompt_parts.append('        "materials": []\n')
        prompt_parts.append('      }\n')
        prompt_parts.append('    ],\n')
        prompt_parts.append('    "production": {\n')
        prompt_parts.append('      "phase": "production",\n')
        prompt_parts.append('      "title": "产出",\n')
        prompt_parts.append('      "duration": 10,\n')
        prompt_parts.append('      "description": "说明",\n')
        prompt_parts.append('      "activities": [],\n')
        prompt_parts.append('      "teacher_actions": [],\n')
        prompt_parts.append('      "student_actions": [],\n')
        prompt_parts.append('      "materials": []\n')
        prompt_parts.append('    },\n')
        prompt_parts.append('    "summary": {\n')
        prompt_parts.append('      "phase": "summary",\n')
        prompt_parts.append('      "title": "总结",\n')
        prompt_parts.append('      "duration": 5,\n')
        prompt_parts.append('      "description": "说明",\n')
        prompt_parts.append('      "activities": [],\n')
        prompt_parts.append('      "teacher_actions": [],\n')
        prompt_parts.append('      "student_actions": [],\n')
        prompt_parts.append('      "materials": []\n')
        prompt_parts.append('    },\n')
        prompt_parts.append('    "homework": {\n')
        prompt_parts.append('      "phase": "homework",\n')
        prompt_parts.append('      "title": "作业",\n')
        prompt_parts.append('      "duration": 0,\n')
        prompt_parts.append('      "description": "说明",\n')
        prompt_parts.append('      "activities": [],\n')
        prompt_parts.append('      "teacher_actions": [],\n')
        prompt_parts.append('      "student_actions": [],\n')
        prompt_parts.append('      "materials": []\n')
        prompt_parts.append('    }\n')
        prompt_parts.append('  },\n')
        prompt_parts.append('  "leveled_materials": [],\n')
        prompt_parts.append('  "exercises": {\n')
        prompt_parts.append('    "multiple_choice": [\n')
        prompt_parts.append('      {\n')
        prompt_parts.append('        "id": "q1",\n')
        prompt_parts.append('        "type": "multiple_choice",\n')
        prompt_parts.append('        "question": "题目",\n')
        prompt_parts.append('        "options": ["A","B","C","D"],\n')
        prompt_parts.append('        "correct_answer": "A",\n')
        prompt_parts.append('        "explanation": "解析",\n')
        prompt_parts.append('        "points": 1,\n')
        prompt_parts.append('        "difficulty": "A1"\n')
        prompt_parts.append('      }\n')
        prompt_parts.append('    ]\n')
        prompt_parts.append('  },\n')
        prompt_parts.append('  "ppt_outline": [\n')
        prompt_parts.append('    {\n')
        prompt_parts.append('      "slide_number": 1,\n')
        prompt_parts.append('      "title": "封面",\n')
        prompt_parts.append('      "content": ["课程标题","教师","日期"],\n')
        prompt_parts.append('      "notes": "备注",\n')
        prompt_parts.append('      "layout": "title"\n')
        prompt_parts.append('    }\n')
        prompt_parts.append('  ]\n')
        prompt_parts.append("}\n")
        prompt_parts.append("```\n")

        return "".join(prompt_parts)

    def _build_leveled_material_prompt(self, base_content: str, target_level: str) -> str:
        """构建分层材料提示词"""
        return f"""
请根据CEFR {target_level}等级标准，改写以下内容。

要求：
1. 控制词汇难度，确保适合{target_level}水平的学生
2. 调整句子结构，{target_level}学生能理解
3. 保持主题不变，但简化或扩展内容以适应目标等级
4. 字数控制在100-200字之间
5. 提供词汇表和理解问题

原始内容：
{base_content}

请返回JSON格式：
{{
  "level": "{target_level}",
  "title": "标题",
  "content": "改写后的内容",
  "word_count": 字数,
  "vocabulary_list": [
    {{
      "word": "单词",
      "phonetic": "/音标/",
      "part_of_speech": "词性",
      "meaning_cn": "中文释义",
      "example_sentence": "例句",
      "example_translation": "翻译",
      "difficulty": "{target_level}"
    }}
  ],
  "comprehension_questions": ["问题1", "问题2"],
  "difficulty_notes": "难度说明"
}}
"""

    def _build_exercise_prompt(
        self, topic: str, level: str, exercise_type: str, count: int
    ) -> str:
        """构建练习题提示词"""
        type_descriptions = {
            "multiple_choice": "选择题",
            "fill_blank": "填空题",
            "matching": "匹配题",
            "essay": "写作题",
            "speaking": "口语题",
        }

        return f"""
请为主题"{topic}"生成{count}道{type_descriptions.get(exercise_type, exercise_type)}，难度为CEFR {level}。

要求：
1. 题目要围绕主题，考查学生对{level}级别知识的掌握
2. 题目难度适中，既不能太简单也不能太难
3. 提供详细的答案解析
4. 选择题要有4个选项，只有一个正确答案

请返回JSON格式：
{{
  "exercises": [
    {{
      "id": "q1",
      "type": "{exercise_type}",
      "question": "题目内容",
      "options": ["选项A", "选项B", "选项C", "选项D"],
      "correct_answer": "正确答案",
      "explanation": "详细解析",
      "points": 1,
      "difficulty": "{level}"
    }}
  ]
}}
"""

    def _build_ppt_prompt(self, structure: LessonPlanStructure) -> str:
        """构建PPT大纲提示词"""
        structure_desc = structure.model_dump_json(indent=2, ensure_ascii=False)

        return f"""
请根据以下教学流程，设计PPT大纲。

教学流程：
{structure_desc}

要求：
1. 每个教学环节至少对应1-2张幻灯片
2. 幻灯片内容简洁明了，突出重点
3. 包含标题、内容要点、演讲者备注
4. 设计合理的幻灯片布局类型

请返回JSON格式：
{{
  "slides": [
    {{
      "slide_number": 1,
      "title": "幻灯片标题",
      "content": ["内容要点1", "内容要点2"],
      "notes": "演讲者备注",
      "layout": "title_content"
    }}
  ]
}}
"""

    async def _call_zhipu_json(
        self,
        messages: List[Dict[str, str]],
        use_long_timeout: bool = False
    ) -> str:
        """
        调用ZhipuAI API（JSON mode）

        Args:
            messages: 对话消息
            use_long_timeout: 是否使用长超时（用于教案生成）

        Returns:
            str: AI生成的JSON响应

        Raises:
            ConnectionError: 如果API调用失败
        """
        try:
            # 教案生成使用更长的超时时间（10分钟）
            timeout = settings.ZHIPUAI_LESSON_PLAN_TIMEOUT if use_long_timeout else None

            response = await self.zhipu_service.chat_completion(
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
                timeout=timeout
            )

            # 获取响应内容
            choices = response.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content", "")
                reasoning_content = message.get("reasoning_content", "")

                # 如果 content 为空但有 reasoning_content，使用 reasoning_content
                if not content and reasoning_content:
                    return reasoning_content
                return content

            raise ConnectionError("ZhipuAI返回空响应")

        except Exception as e:
            raise ConnectionError(f"ZhipuAI API调用失败: {str(e)}")

    def _parse_lesson_plan_response(
        self, response_text: str, request: GenerateLessonPlanRequest
    ) -> Dict[str, Any]:
        """
        解析教案响应并自动填充缺失字段

        Args:
            response_text: AI响应文本
            request: 原始请求

        Returns:
            Dict[str, Any]: 解析后的教案数据
        """
        try:
            result = json.loads(response_text)

            # 兼容简化版词汇格式（key_words -> noun）
            if "vocabulary" in result and "key_words" in result["vocabulary"]:
                key_words = result["vocabulary"]["key_words"]
                # 转换为完整格式
                full_vocabs = []
                for kw in key_words:
                    full_vocabs.append({
                        "word": kw.get("word", ""),
                        "phonetic": kw.get("phonetic", ""),
                        "part_of_speech": kw.get("part_of_speech", "n."),
                        "meaning_cn": kw.get("meaning_cn", ""),
                        "meaning_en": kw.get("meaning_en", ""),
                        "example_sentence": kw.get("example_sentence", kw.get("example", f"Use {kw.get('word', '')} in a sentence.")),
                        "example_translation": kw.get("example_translation", ""),
                        "collocations": kw.get("collocations", []),
                        "synonyms": kw.get("synonyms", []),
                        "antonyms": kw.get("antonyms", []),
                        "difficulty": request.level
                    })
                result["vocabulary"] = {"noun": full_vocabs}

            # 确保词汇字段完整
            if "vocabulary" in result:
                for pos_type, vocabs in result["vocabulary"].items():
                    if isinstance(vocabs, list):
                        for vocab in vocabs:
                            if isinstance(vocab, dict):
                                word = vocab.get("word", "")
                                vocab.setdefault("part_of_speech", pos_type if pos_type != "noun" else "n.")
                                vocab.setdefault("phonetic", "")
                                vocab.setdefault("meaning_cn", vocab.get("meaning_cn", f"{word}的中文释义" if word else ""))
                                vocab.setdefault("meaning_en", "")
                                vocab.setdefault("example_sentence", f"Example with {word}.")
                                vocab.setdefault("example_translation", "")
                                vocab.setdefault("collocations", [])
                                vocab.setdefault("synonyms", [])
                                vocab.setdefault("antonyms", [])
                                vocab.setdefault("difficulty", request.level)

            # 确保语法点字段完整
            if "grammar_points" in result:
                for gp in result["grammar_points"]:
                    if isinstance(gp, dict):
                        gp.setdefault("rule", gp.get("description", ""))
                        gp.setdefault("common_mistakes", [])
                        gp.setdefault("practice_tips", [])
                        gp.setdefault("examples", gp.get("examples", []))

            # 确保结构字段完整
            if "structure" in result:
                for phase, data in result["structure"].items():
                    if isinstance(data, dict):
                        data.setdefault("phase", phase)
                        data.setdefault("title", phase.replace("_", " ").title())
                        data.setdefault("activities", [])
                        data.setdefault("teacher_actions", [])
                        data.setdefault("student_actions", [])
                        data.setdefault("materials", [])
                        if "duration" not in data:
                            data["duration"] = 5
                    elif isinstance(data, list):
                        # 如果是列表，转换每个项目
                        for item in data:
                            if isinstance(item, dict):
                                item.setdefault("phase", phase)
                                item.setdefault("title", f"{phase.title()} Activity")
                                item.setdefault("activities", [])
                                item.setdefault("teacher_actions", [])
                                item.setdefault("student_actions", [])
                                item.setdefault("materials", [])
                                item.setdefault("duration", 10)

            # 如果不包含分层材料，添加空字典
            if not request.include_leveled_materials:
                result["leveled_materials"] = []

            # 如果不包含PPT，添加空列表
            if not request.include_ppt:
                result["ppt_outline"] = []

            # 确保exercises存在且格式正确
            if "exercises" not in result:
                result["exercises"] = {}
            for ex_type, exercises in result["exercises"].items():
                if isinstance(exercises, list):
                    for idx, ex in enumerate(exercises):
                        if isinstance(ex, dict):
                            ex.setdefault("id", f"q_{ex_type}_{idx}")
                            ex.setdefault("type", ex_type)
                            ex.setdefault("options", None)
                            ex.setdefault("points", 1)
                            ex.setdefault("difficulty", request.level)

            # 确保ppt_outline是列表
            if "ppt_outline" in result and isinstance(result["ppt_outline"], dict):
                result["ppt_outline"] = []

            # 确保vocabulary至少有空的noun列表
            if "vocabulary" not in result or not result["vocabulary"]:
                result["vocabulary"] = {"noun": []}

            # 确保grammar_points是列表
            if "grammar_points" not in result:
                result["grammar_points"] = []
            elif not isinstance(result["grammar_points"], list):
                result["grammar_points"] = []

            return result
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {str(e)}\n响应内容: {response_text}")

    async def get_lesson_plan(
        self, db: AsyncSession, lesson_plan_id: uuid.UUID
    ) -> Optional[LessonPlan]:
        """
        获取教案详情

        Args:
            db: 数据库会话
            lesson_plan_id: 教案ID

        Returns:
            Optional[LessonPlan]: 教案对象或None
        """
        result = await db.execute(
            select(LessonPlan).where(LessonPlan.id == lesson_plan_id)
        )
        return result.scalar_one_or_none()

    async def list_lesson_plans(
        self,
        db: AsyncSession,
        teacher_id: uuid.UUID,
        status: Optional[str] = None,
        level: Optional[str] = None,
        target_exam: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[LessonPlan], int]:
        """
        列出教案

        Args:
            db: 数据库会话
            teacher_id: 教师ID
            status: 状态筛选
            level: 等级筛选
            target_exam: 考试类型筛选
            page: 页码
            page_size: 每页大小

        Returns:
            tuple[List[LessonPlan], int]: (教案列表, 总数)
        """
        # 构建查询
        query = select(LessonPlan).where(LessonPlan.teacher_id == teacher_id)

        # 应用筛选
        if status:
            query = query.where(LessonPlan.status == status)
        if level:
            query = query.where(LessonPlan.level == level)
        if target_exam:
            query = query.where(LessonPlan.target_exam == target_exam)

        # 排序
        query = query.order_by(LessonPlan.created_at.desc())

        # 计算总数
        count_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar()

        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        lesson_plans = result.scalars().all()

        return list(lesson_plans), total

    async def update_lesson_plan(
        self,
        db: AsyncSession,
        lesson_plan_id: uuid.UUID,
        updates: Dict[str, Any],
    ) -> Optional[LessonPlan]:
        """
        更新教案

        Args:
            db: 数据库会话
            lesson_plan_id: 教案ID
            updates: 更新内容

        Returns:
            Optional[LessonPlan]: 更新后的教案或None
        """
        lesson_plan = await self.get_lesson_plan(db, lesson_plan_id)
        if not lesson_plan:
            return None

        for key, value in updates.items():
            if hasattr(lesson_plan, key):
                setattr(lesson_plan, key, value)

        await db.commit()
        await db.refresh(lesson_plan)
        return lesson_plan

    async def delete_lesson_plan(
        self, db: AsyncSession, lesson_plan_id: uuid.UUID
    ) -> bool:
        """
        删除教案

        Args:
            db: 数据库会话
            lesson_plan_id: 教案ID

        Returns:
            bool: 是否删除成功
        """
        lesson_plan = await self.get_lesson_plan(db, lesson_plan_id)
        if not lesson_plan:
            return False

        await db.delete(lesson_plan)
        await db.commit()
        return True

    async def duplicate_lesson_plan(
        self,
        db: AsyncSession,
        lesson_plan_id: uuid.UUID,
        teacher_id: uuid.UUID,
        new_title: Optional[str] = None,
    ) -> LessonPlan:
        """
        复制教案

        Args:
            db: 数据库会话
            lesson_plan_id: 原教案ID
            teacher_id: 新教案的教师ID
            new_title: 新标题（不设置则自动生成）

        Returns:
            LessonPlan: 复制后的新教案

        Raises:
            ValueError: 如果原教案不存在
        """
        original_plan = await self.get_lesson_plan(db, lesson_plan_id)
        if not original_plan:
            raise ValueError("原教案不存在")

        # 生成新标题
        if new_title is None:
            new_title = f"{original_plan.title} (副本)"

        # 创建新教案
        new_plan = LessonPlan(
            teacher_id=teacher_id,
            title=new_title,
            topic=original_plan.topic,
            level=original_plan.level,
            duration=original_plan.duration,
            target_exam=original_plan.target_exam,
            status="draft",
            # 复制AI生成参数
            ai_generation_params=original_plan.ai_generation_params,
            # 复制教案内容
            objectives=original_plan.objectives,
            vocabulary=original_plan.vocabulary,
            grammar_points=original_plan.grammar_points,
            teaching_structure=original_plan.teaching_structure,
            leveled_materials=original_plan.leveled_materials,
            exercises=original_plan.exercises,
            ppt_outline=original_plan.ppt_outline,
            resources=original_plan.resources,
            # 不复制教学反思
            teaching_notes=None,
            # 记录来源
            forked_from=original_plan.teacher_id,
        )

        db.add(new_plan)

        # 更新原教案的分支计数
        original_plan.fork_count = (original_plan.fork_count or 0) + 1

        await db.commit()
        await db.refresh(new_plan)

        return new_plan

    async def create_from_template(
        self,
        db: AsyncSession,
        template_id: uuid.UUID,
        teacher_id: uuid.UUID,
        title: str,
        topic: str,
        level: str,
        duration: int = 45,
        target_exam: Optional[str] = None,
        additional_requirements: Optional[str] = None,
    ) -> LessonPlan:
        """
        从模板创建教案

        Args:
            db: 数据库会话
            template_id: 模板ID
            teacher_id: 教师ID
            title: 教案标题
            topic: 教学主题
            level: CEFR等级
            duration: 课程时长
            target_exam: 目标考试
            additional_requirements: 额外要求

        Returns:
            LessonPlan: 创建的教案

        Raises:
            ValueError: 如果模板不存在
        """
        from app.models import LessonPlanTemplate

        template = await db.get(LessonPlanTemplate, template_id)
        if not template:
            raise ValueError("模板不存在")

        if not template.is_active:
            raise ValueError("模板已停用")

        # 从模板结构创建教案
        template_structure = template.template_structure or {}

        new_plan = LessonPlan(
            teacher_id=teacher_id,
            title=title,
            topic=topic,
            level=level,
            duration=duration,
            target_exam=target_exam or template.target_exam,
            status="draft",
            ai_generation_params={
                "from_template": str(template_id),
                "template_name": template.name,
                "additional_requirements": additional_requirements,
            },
            # 从模板提取内容
            teaching_structure=template_structure.get("structure", {}),
            vocabulary=template_structure.get("vocabulary", {}),
            grammar_points=template_structure.get("grammar_points", {}),
            exercises=template_structure.get("exercises", {}),
            resources=template_structure.get("resources", {}),
        )

        db.add(new_plan)

        # 更新模板使用计数
        template.usage_count += 1

        await db.commit()
        await db.refresh(new_plan)

        return new_plan

    async def get_templates(
        self,
        db: AsyncSession,
        level: Optional[str] = None,
        target_exam: Optional[str] = None,
        is_system: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LessonPlanTemplate], int]:
        """
        获取教案模板列表

        Args:
            db: 数据库会话
            level: 等级筛选
            target_exam: 考试类型筛选
            is_system: 是否系统模板筛选
            page: 页码
            page_size: 每页大小

        Returns:
            tuple[list[LessonPlanTemplate], int]: (模板列表, 总数)
        """
        # 构建查询
        query = select(LessonPlanTemplate).where(
            LessonPlanTemplate.is_active == True
        )

        # 应用筛选
        if level:
            query = query.where(LessonPlanTemplate.level == level)
        if target_exam:
            query = query.where(LessonPlanTemplate.target_exam == target_exam)
        if is_system is not None:
            query = query.where(LessonPlanTemplate.is_system == is_system)

        # 计算总数
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        # 排序和分页
        query = query.order_by(
            LessonPlanTemplate.is_system.desc(),
            LessonPlanTemplate.usage_count.desc(),
            LessonPlanTemplate.created_at.desc()
        )
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        templates = result.scalars().all()

        return list(templates), total


# 创建全局单例
_lesson_plan_service: Optional[LessonPlanService] = None


def get_lesson_plan_service() -> LessonPlanService:
    """
    获取教案服务单例

    Returns:
        LessonPlanService: 教案服务实例
    """
    global _lesson_plan_service
    if _lesson_plan_service is None:
        _lesson_plan_service = LessonPlanService()
    return _lesson_plan_service
