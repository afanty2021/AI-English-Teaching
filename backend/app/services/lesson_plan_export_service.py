"""
教案导出服务 - AI英语教学系统
基于现有的PDF渲染服务，提供教案导出功能
包含性能优化：缓存、内存管理、并发优化
"""
import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union, Tuple
from functools import lru_cache
from weakref import WeakValueDictionary

from jinja2 import Environment, Template

from app.services.pdf_renderer_service import PdfRendererService
from app.utils.pdf_helpers import get_pdf_css, check_font_availability

logger = logging.getLogger(__name__)


class LessonPlanExportService:
    """
    教案导出服务类（性能优化版）

    提供以下功能：
    1. 教案导出为PDF格式
    2. 教案导出为Markdown格式
    3. PPT大纲导出为结构化数据
    4. 创建PPT幻灯片数据

    性能优化特性：
    - 内存缓存：缓存导出的结果
    - 并发优化：支持异步并发导出
    - 内存监控：实时监控内存使用
    - 资源清理：自动清理过期缓存
    """

    # 缓存存储（使用普通字典，避免字符串弱引用问题）
    _cache: Dict[str, Union[bytes, str]] = {}
    _cache_timestamps: Dict[str, float] = {}
    _cache_lock = asyncio.Lock()

    # 缓存配置
    CACHE_TTL = 3600  # 缓存1小时
    MAX_CACHE_SIZE = 100  # 最大缓存100条记录

    # 内存监控
    _memory_usage_history: List[float] = []
    _memory_alert_threshold = 500  # MB

    def __init__(self, template_env: Optional[Environment] = None):
        """
        初始化教案导出服务

        Args:
            template_env: Jinja2模板环境，如果为None则使用默认环境
        """
        self.pdf_renderer = PdfRendererService(template_env)
        self.template_env = template_env or Environment(
            loader=None,  # 将使用字符串模板
            autoescape=True
        )

        # 启动后台清理任务
        asyncio.create_task(self._cleanup_expired_cache())

    def _generate_cache_key(self, lesson_plan: Dict, teacher: Dict,
                           options: Optional[Dict] = None, export_type: str = 'pdf') -> str:
        """
        生成缓存键

        Args:
            lesson_plan: 教案数据
            teacher: 教师信息
            options: 导出选项
            export_type: 导出类型

        Returns:
            str: 缓存键
        """
        # 使用教案ID、标题和关键信息生成哈希
        cache_data = {
            'lesson_id': lesson_plan.get('id', ''),
            'lesson_title': lesson_plan.get('title', ''),
            'teacher_id': teacher.get('id', ''),
            'options': options or {},
            'export_type': export_type,
            'version': '1.0'  # 版本号，用于缓存失效
        }

        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()

    async def _get_cached_result(self, cache_key: str) -> Optional[Union[bytes, str]]:
        """获取缓存结果"""
        async with self._cache_lock:
            if cache_key in self._cache:
                # 检查缓存是否过期
                timestamp = self._cache_timestamps.get(cache_key, 0)
                if time.time() - timestamp < self.CACHE_TTL:
                    logger.debug(f"缓存命中: {cache_key}")
                    return self._cache[cache_key]
                else:
                    # 缓存过期，删除
                    del self._cache[cache_key]
                    del self._cache_timestamps[cache_key]
        return None

    async def _store_cached_result(self, cache_key: str, result: Union[bytes, str]):
        """存储缓存结果"""
        async with self._cache_lock:
            # 检查缓存大小
            if len(self._cache) >= self.MAX_CACHE_SIZE:
                # 删除最旧的缓存
                oldest_key = min(self._cache_timestamps.keys(),
                               key=lambda k: self._cache_timestamps[k])
                if oldest_key in self._cache:
                    del self._cache[oldest_key]
                del self._cache_timestamps[oldest_key]
                logger.debug(f"缓存已满，删除最旧记录: {oldest_key}")

            # 存储新结果
            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = time.time()
            logger.debug(f"缓存已更新: {cache_key}")

    async def _cleanup_expired_cache(self):
        """后台清理过期缓存"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次
                current_time = time.time()
                expired_keys = []

                async with self._cache_lock:
                    for key, timestamp in self._cache_timestamps.items():
                        if current_time - timestamp >= self.CACHE_TTL:
                            expired_keys.append(key)

                for key in expired_keys:
                    if key in self._cache:
                        del self._cache[key]
                    if key in self._cache_timestamps:
                        del self._cache_timestamps[key]

                if expired_keys:
                    logger.debug(f"清理了 {len(expired_keys)} 个过期缓存")

            except Exception as e:
                logger.error(f"缓存清理任务出错: {e}")

    def _monitor_memory_usage(self):
        """监控内存使用"""
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024

            self._memory_usage_history.append(memory_mb)

            # 保持历史记录在合理范围
            if len(self._memory_usage_history) > 100:
                self._memory_usage_history.pop(0)

            # 检查内存使用是否过高
            if memory_mb > self._memory_alert_threshold:
                logger.warning(f"内存使用过高: {memory_mb:.2f} MB")

            return memory_mb
        except ImportError:
            logger.warning("psutil未安装，无法监控内存使用")
            return 0
        except Exception as e:
            logger.error(f"内存监控出错: {e}")
            return 0

    async def export_as_pdf(
        self,
        lesson_plan: Dict[str, Any],
        teacher: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> bytes:
        """
        导出教案为PDF格式（性能优化版）

        Args:
            lesson_plan: 教案数据
            teacher: 教师信息
            options: 导出选项
                - include_objectives: 是否包含教学目标 (默认: True)
                - include_structure: 是否包含教学流程 (默认: True)
                - include_vocabulary: 是否包含词汇表 (默认: True)
                - include_grammar: 是否包含语法点 (默认: True)
                - include_materials: 是否包含分层材料 (默认: True)
                - include_exercises: 是否包含练习题 (默认: True)
                - include_ppt_outline: 是否包含PPT大纲 (默认: True)
            use_cache: 是否使用缓存 (默认: True)

        Returns:
            bytes: PDF文件内容

        Raises:
            ValueError: 如果教案数据无效
            Exception: 如果PDF渲染失败
        """
        try:
            # 验证必要字段
            if not lesson_plan.get('title'):
                raise ValueError("教案标题不能为空")

            # 设置默认选项
            default_options = {
                'include_objectives': True,
                'include_structure': True,
                'include_vocabulary': True,
                'include_grammar': True,
                'include_materials': True,
                'include_exercises': True,
                'include_ppt_outline': True,
            }
            if options:
                default_options.update(options)
            options = default_options

            # 生成缓存键
            cache_key = self._generate_cache_key(lesson_plan, teacher, options, 'pdf')

            # 尝试从缓存获取结果
            if use_cache:
                cached_result = await self._get_cached_result(cache_key)
                if cached_result:
                    logger.info(f"教案PDF导出成功（缓存）: {lesson_plan['title']}")
                    return cached_result

            # 监控内存使用
            memory_before = self._monitor_memory_usage()
            start_time = time.time()

            # 生成Markdown内容（使用异步）
            markdown_content = await asyncio.get_event_loop().run_in_executor(
                None, self._render_lesson_plan_markdown, lesson_plan, teacher, options
            )

            # 获取PDF样式
            pdf_css = get_pdf_css()

            # 渲染为PDF（异步操作）
            pdf_bytes = await self.pdf_renderer.render_markdown_to_pdf(
                markdown_content=markdown_content,
                css_content=pdf_css,
                title=lesson_plan.get('title', '教案')
            )

            # 存储到缓存
            if use_cache:
                await self._store_cached_result(cache_key, pdf_bytes)

            # 监控内存使用变化
            memory_after = self._monitor_memory_usage()
            execution_time = time.time() - start_time

            logger.info(
                f"教案PDF导出成功: {lesson_plan['title']} "
                f"(耗时: {execution_time:.2f}s, 内存: {memory_before:.1f}MB -> {memory_after:.1f}MB)"
            )
            return pdf_bytes

        except Exception as e:
            logger.error(f"教案PDF导出失败: {str(e)}")
            raise Exception(f"PDF导出失败: {str(e)}")

    async def export_as_markdown(
        self,
        lesson_plan: Dict[str, Any],
        teacher: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> str:
        """
        导出教案为Markdown格式（性能优化版）

        Args:
            lesson_plan: 教案数据
            teacher: 教师信息
            options: 导出选项（与PDF导出相同）
            use_cache: 是否使用缓存 (默认: True)

        Returns:
            str: Markdown格式的教案内容
        """
        try:
            # 验证必要字段
            if not lesson_plan.get('title'):
                raise ValueError("教案标题不能为空")

            # 设置默认选项
            default_options = {
                'include_objectives': True,
                'include_structure': True,
                'include_vocabulary': True,
                'include_grammar': True,
                'include_materials': True,
                'include_exercises': True,
                'include_ppt_outline': True,
            }
            if options:
                default_options.update(options)
            options = default_options

            # 生成缓存键
            cache_key = self._generate_cache_key(lesson_plan, teacher, options, 'markdown')

            # 尝试从缓存获取结果
            if use_cache:
                cached_result = await self._get_cached_result(cache_key)
                if cached_result:
                    logger.info(f"教案Markdown导出成功（缓存）: {lesson_plan['title']}")
                    return cached_result

            # 监控内存使用
            memory_before = self._monitor_memory_usage()
            start_time = time.time()

            # 生成Markdown内容（使用异步）
            markdown_content = await asyncio.get_event_loop().run_in_executor(
                None, self._render_lesson_plan_markdown, lesson_plan, teacher, options
            )

            # 存储到缓存
            if use_cache:
                await self._store_cached_result(cache_key, markdown_content)

            # 监控内存使用变化
            memory_after = self._monitor_memory_usage()
            execution_time = time.time() - start_time

            logger.info(
                f"教案Markdown导出成功: {lesson_plan['title']} "
                f"(耗时: {execution_time:.2f}s, 内存: {memory_before:.1f}MB -> {memory_after:.1f}MB)"
            )
            return markdown_content

        except Exception as e:
            logger.error(f"教案Markdown导出失败: {str(e)}")
            raise Exception(f"Markdown导出失败: {str(e)}")

    async def export_ppt_outline(
        self,
        lesson_plan: Dict[str, Any],
        format_type: str = 'json'
    ) -> Union[Dict[str, Any], str]:
        """
        导出PPT大纲为结构化数据

        Args:
            lesson_plan: 教案数据
            format_type: 输出格式 ('json' | 'markdown')

        Returns:
            Union[Dict, str]: 结构化的PPT大纲数据
        """
        try:
            ppt_outline = lesson_plan.get('ppt_outline', [])

            if not ppt_outline:
                logger.warning(f"教案 '{lesson_plan.get('title')}' 没有PPT大纲")
                return [] if format_type == 'json' else "# PPT大纲\n\n暂无内容"

            if format_type == 'json':
                return ppt_outline
            elif format_type == 'markdown':
                return self._render_ppt_outline_markdown(ppt_outline)
            else:
                raise ValueError(f"不支持的格式类型: {format_type}")

        except Exception as e:
            logger.error(f"PPT大纲导出失败: {str(e)}")
            raise Exception(f"PPT大纲导出失败: {str(e)}")

    def create_presentation_slides(
        self,
        lesson_plan: Dict[str, Any],
        ppt_outline: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        创建PPT幻灯片数据

        Args:
            lesson_plan: 教案数据
            ppt_outline: PPT大纲数据，如果为None则从教案中获取

        Returns:
            List[Dict]: 幻灯片数据列表
        """
        try:
            if ppt_outline is None:
                ppt_outline = lesson_plan.get('ppt_outline', [])

            if not ppt_outline:
                # 如果没有PPT大纲，生成基本的幻灯片结构
                ppt_outline = self._generate_basic_ppt_outline(lesson_plan)

            # 转换为标准幻灯片格式
            slides = []
            for idx, slide_data in enumerate(ppt_outline, 1):
                slide = {
                    'slide_number': slide_data.get('slide_number', idx),
                    'title': slide_data.get('title', f'幻灯片 {idx}'),
                    'content': slide_data.get('content', []),
                    'notes': slide_data.get('notes', ''),
                    'layout': slide_data.get('layout', 'title_content'),
                    'background_color': '#ffffff',
                    'text_color': '#333333',
                }
                slides.append(slide)

            logger.info(f"创建PPT幻灯片成功: {len(slides)}张幻灯片")
            return slides

        except Exception as e:
            logger.error(f"创建PPT幻灯片失败: {str(e)}")
            raise Exception(f"PPT幻灯片创建失败: {str(e)}")

    def _render_lesson_plan_markdown(
        self,
        lesson_plan: Dict[str, Any],
        teacher: Dict[str, Any],
        options: Dict[str, bool]
    ) -> str:
        """
        渲染教案为Markdown格式

        Args:
            lesson_plan: 教案数据
            teacher: 教师信息
            options: 导出选项

        Returns:
            str: Markdown格式的教案内容
        """
        # 构建Markdown内容
        md_parts = []

        # 封面信息
        md_parts.append(f"# {lesson_plan.get('title', '教案')}")
        md_parts.append("")
        md_parts.append("---")
        md_parts.append("")

        # 基本信息表格
        md_parts.append("## 基本信息")
        md_parts.append("")
        md_parts.append("| 项目 | 内容 |")
        md_parts.append("|------|------|")
        md_parts.append(f"| 教案标题 | {lesson_plan.get('title', '')} |")
        md_parts.append(f"| 教师 | {teacher.get('username', '')} |")
        md_parts.append(f"| 等级 | {lesson_plan.get('level', '')} |")
        md_parts.append(f"| 时长 | {lesson_plan.get('duration', 0)}分钟 |")
        md_parts.append(f"| 主题 | {lesson_plan.get('topic', '')} |")
        if lesson_plan.get('target_exam'):
            md_parts.append(f"| 目标考试 | {lesson_plan.get('target_exam')} |")
        md_parts.append(f"| 生成时间 | {lesson_plan.get('created_at', '')} |")
        md_parts.append("")

        # 教学目标
        if options.get('include_objectives', True):
            md_parts.append(self._render_objectives_section(lesson_plan.get('objectives', {})))

        # 教学流程
        if options.get('include_structure', True):
            md_parts.append(self._render_structure_section(lesson_plan.get('teaching_structure', {})))

        # 核心词汇
        if options.get('include_vocabulary', True):
            md_parts.append(self._render_vocabulary_section(lesson_plan.get('vocabulary', {})))

        # 语法点
        if options.get('include_grammar', True):
            md_parts.append(self._render_grammar_section(lesson_plan.get('grammar_points', [])))

        # 分层阅读材料
        if options.get('include_materials', True):
            md_parts.append(self._render_materials_section(lesson_plan.get('leveled_materials', [])))

        # 练习题
        if options.get('include_exercises', True):
            md_parts.append(self._render_exercises_section(lesson_plan.get('exercises', {})))

        # PPT大纲
        if options.get('include_ppt_outline', True):
            md_parts.append(self._render_ppt_outline_section(lesson_plan.get('ppt_outline', [])))

        return "\n".join(md_parts)

    def _render_objectives_section(self, objectives: Dict[str, Any]) -> str:
        """渲染教学目标部分"""
        if not objectives:
            return ""

        parts = ["## 教学目标", ""]

        for category, items in objectives.items():
            if not items:
                continue

            # 类别标题
            category_name = {
                'language_knowledge': '语言知识',
                'language_skills': '语言技能',
                'learning_strategies': '学习策略',
                'cultural_awareness': '文化意识',
                'emotional_attitudes': '情感态度'
            }.get(category, category)

            parts.append(f"### {category_name}")
            parts.append("")

            if isinstance(items, dict):
                # 处理嵌套结构（如 language_skills）
                for skill, skill_items in items.items():
                    if skill_items:
                        skill_name = {
                            'listening': '听力',
                            'speaking': '口语',
                            'reading': '阅读',
                            'writing': '写作'
                        }.get(skill, skill)
                        parts.append(f"**{skill_name}**")
                        for item in skill_items:
                            parts.append(f"- {item}")
                        parts.append("")
            elif isinstance(items, list):
                # 处理列表结构
                for item in items:
                    parts.append(f"- {item}")
                parts.append("")

        return "\n".join(parts)

    def _render_structure_section(self, structure: Dict[str, Any]) -> str:
        """渲染教学流程部分"""
        if not structure:
            return ""

        parts = ["## 教学流程", ""]

        phase_names = {
            'warm_up': '热身',
            'presentation': '讲解',
            'practice': '练习',
            'production': '产出',
            'summary': '总结',
            'homework': '作业'
        }

        for phase, data in structure.items():
            if not data:
                continue

            phase_name = phase_names.get(phase, phase)
            parts.append(f"### {phase_name}")
            parts.append("")

            if isinstance(data, dict):
                parts.append(f"**时长**: {data.get('duration', 0)}分钟")
                parts.append("")
                parts.append(f"**描述**: {data.get('description', '')}")
                parts.append("")

                if data.get('activities'):
                    parts.append("**活动**")
                    for activity in data['activities']:
                        parts.append(f"- {activity}")
                    parts.append("")

                if data.get('teacher_actions'):
                    parts.append("**教师活动**")
                    for action in data['teacher_actions']:
                        parts.append(f"- {action}")
                    parts.append("")

                if data.get('student_actions'):
                    parts.append("**学生活动**")
                    for action in data['student_actions']:
                        parts.append(f"- {action}")
                    parts.append("")

                if data.get('materials'):
                    parts.append("**所需材料**")
                    for material in data['materials']:
                        parts.append(f"- {material}")
                    parts.append("")
            elif isinstance(data, list):
                # 处理列表结构（如 practice 可能有多个活动）
                for activity in data:
                    if isinstance(activity, dict):
                        parts.append(f"**{activity.get('title', '活动')}** ({activity.get('duration', 0)}分钟)")
                        parts.append(f"描述: {activity.get('description', '')}")
                        parts.append("")

        return "\n".join(parts)

    def _render_vocabulary_section(self, vocabulary: Dict[str, Any]) -> str:
        """渲染词汇表部分"""
        if not vocabulary:
            return ""

        parts = ["## 核心词汇", ""]

        # 处理不同词性的词汇
        for pos_type, words in vocabulary.items():
            if not words:
                continue

            pos_name = {
                'noun': '名词',
                'verb': '动词',
                'adj': '形容词',
                'adv': '副词',
                'prep': '介词'
            }.get(pos_type, pos_type)

            parts.append(f"### {pos_name}")
            parts.append("")

            # 词汇表格
            parts.append("| 单词 | 音标 | 词性 | 中文释义 | 例句 |")
            parts.append("|------|------|------|----------|------|")

            for word_data in words:
                word = word_data.get('word', '')
                phonetic = word_data.get('phonetic', '')
                pos = word_data.get('part_of_speech', '')
                meaning_cn = word_data.get('meaning_cn', '')
                example = word_data.get('example_sentence', '')

                parts.append(f"| {word} | {phonetic} | {pos} | {meaning_cn} | {example} |")

            parts.append("")

        return "\n".join(parts)

    def _render_grammar_section(self, grammar_points: List[Dict[str, Any]]) -> str:
        """渲染语法点部分"""
        if not grammar_points:
            return ""

        parts = ["## 语法点", ""]

        for gp in grammar_points:
            parts.append(f"### {gp.get('name', '')}")
            parts.append("")
            parts.append(f"**描述**: {gp.get('description', '')}")
            parts.append("")
            parts.append(f"**规则**: {gp.get('rule', '')}")
            parts.append("")

            if gp.get('examples'):
                parts.append("**例句**")
                for example in gp['examples']:
                    parts.append(f"- {example}")
                parts.append("")

            if gp.get('common_mistakes'):
                parts.append("**常见错误**")
                for mistake in gp['common_mistakes']:
                    parts.append(f"- {mistake}")
                parts.append("")

            if gp.get('practice_tips'):
                parts.append("**练习建议**")
                for tip in gp['practice_tips']:
                    parts.append(f"- {tip}")
                parts.append("")

        return "\n".join(parts)

    def _render_materials_section(self, materials: List[Dict[str, Any]]) -> str:
        """渲染分层材料部分"""
        if not materials:
            return ""

        parts = ["## 分层阅读材料", ""]

        for material in materials:
            parts.append(f"### {material.get('title', '')} (CEFR {material.get('level', '')})")
            parts.append("")
            parts.append(f"**等级**: {material.get('level', '')}")
            parts.append(f"**字数**: {material.get('word_count', 0)}字")
            parts.append("")
            parts.append(f"**内容**")
            parts.append("")
            parts.append(material.get('content', ''))
            parts.append("")

            if material.get('vocabulary_list'):
                parts.append("**重点词汇**")
                for vocab in material['vocabulary_list']:
                    parts.append(f"- {vocab.get('word', '')}: {vocab.get('meaning_cn', '')}")
                parts.append("")

            if material.get('comprehension_questions'):
                parts.append("**理解问题**")
                for question in material['comprehension_questions']:
                    parts.append(f"- {question}")
                parts.append("")

        return "\n".join(parts)

    def _render_exercises_section(self, exercises: Dict[str, Any]) -> str:
        """渲染练习题部分"""
        if not exercises:
            return ""

        parts = ["## 练习题", ""]

        type_names = {
            'multiple_choice': '选择题',
            'fill_blank': '填空题',
            'matching': '匹配题',
            'essay': '写作题',
            'speaking': '口语题'
        }

        for ex_type, exercise_list in exercises.items():
            if not exercise_list:
                continue

            type_name = type_names.get(ex_type, ex_type)
            parts.append(f"### {type_name}")
            parts.append("")

            for idx, exercise in enumerate(exercise_list, 1):
                parts.append(f"**{idx}. {exercise.get('question', '')}**")
                parts.append("")

                if exercise.get('options'):
                    options = ['A', 'B', 'C', 'D']
                    for opt, option_text in zip(options, exercise['options']):
                        parts.append(f"{opt}. {option_text}")
                    parts.append("")

                parts.append(f"**答案**: {exercise.get('correct_answer', '')}")
                parts.append("")
                parts.append(f"**解析**: {exercise.get('explanation', '')}")
                parts.append("")

        return "\n".join(parts)

    def _render_ppt_outline_section(self, ppt_outline: List[Dict[str, Any]]) -> str:
        """渲染PPT大纲部分"""
        if not ppt_outline:
            return ""

        parts = ["## PPT大纲", ""]
        parts.append("| 幻灯片 | 标题 | 内容要点 |")
        parts.append("|---------|------|----------|")

        for slide in ppt_outline:
            slide_num = slide.get('slide_number', '')
            title = slide.get('title', '')
            content = ', '.join(slide.get('content', []))
            parts.append(f"| {slide_num} | {title} | {content} |")

        parts.append("")

        return "\n".join(parts)

    def _render_ppt_outline_markdown(self, ppt_outline: List[Dict[str, Any]]) -> str:
        """渲染PPT大纲为Markdown格式"""
        if not ppt_outline:
            return "# PPT大纲\n\n暂无内容"

        parts = ["# PPT大纲", ""]

        for slide in ppt_outline:
            parts.append(f"## 幻灯片 {slide.get('slide_number', '')}: {slide.get('title', '')}")
            parts.append("")

            if slide.get('content'):
                parts.append("**内容要点**")
                for content in slide['content']:
                    parts.append(f"- {content}")
                parts.append("")

            if slide.get('notes'):
                parts.append(f"**演讲者备注**: {slide['notes']}")
                parts.append("")

        return "\n".join(parts)

    def _generate_basic_ppt_outline(self, lesson_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成基本的PPT大纲（如果没有提供）"""
        outline = []

        # 封面
        outline.append({
            'slide_number': 1,
            'title': lesson_plan.get('title', '教案'),
            'content': [
                f"等级: {lesson_plan.get('level', '')}",
                f"主题: {lesson_plan.get('topic', '')}",
                f"时长: {lesson_plan.get('duration', 0)}分钟"
            ],
            'layout': 'title'
        })

        # 教学目标
        outline.append({
            'slide_number': 2,
            'title': '教学目标',
            'content': ['语言知识', '语言技能', '学习策略', '文化意识'],
            'layout': 'title_content'
        })

        # 教学流程
        structure = lesson_plan.get('teaching_structure', {})
        for phase, data in structure.items():
            if not data:
                continue

            outline.append({
                'slide_number': len(outline) + 1,
                'title': f"{phase.title()} - {data.get('title', '')}",
                'content': data.get('activities', []),
                'layout': 'title_content'
            })

        # 总结
        outline.append({
            'slide_number': len(outline) + 1,
            'title': '课程总结',
            'content': ['重点回顾', '学生反馈', '下次预告'],
            'layout': 'title_content'
        })

        return outline

    async def export_multiple_formats(
        self,
        lesson_plan: Dict[str, Any],
        teacher: Dict[str, Any],
        formats: List[str] = ['pdf', 'markdown'],
        options: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        concurrent: bool = True
    ) -> Dict[str, Union[bytes, str]]:
        """
        并发导出多种格式（性能优化版）

        Args:
            lesson_plan: 教案数据
            teacher: 教师信息
            formats: 需要导出的格式列表 ['pdf', 'markdown', 'ppt']
            options: 导出选项
            use_cache: 是否使用缓存
            concurrent: 是否并发执行

        Returns:
            Dict[str, Union[bytes, str]]: 各格式的导出结果
        """
        try:
            start_time = time.time()
            logger.info(f"开始并发导出: {lesson_plan['title']}, 格式: {formats}")

            if concurrent:
                # 并发执行
                tasks = []
                for format_type in formats:
                    if format_type == 'pdf':
                        tasks.append(
                            asyncio.create_task(
                                self.export_as_pdf(lesson_plan, teacher, options, use_cache)
                            )
                        )
                    elif format_type == 'markdown':
                        tasks.append(
                            asyncio.create_task(
                                self.export_as_markdown(lesson_plan, teacher, options, use_cache)
                            )
                        )
                    # 可以添加其他格式的导出

                # 等待所有任务完成
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # 处理结果
                export_results = {}
                for i, format_type in enumerate(formats):
                    result = results[i]
                    if isinstance(result, Exception):
                        logger.error(f"导出 {format_type} 失败: {result}")
                        export_results[format_type] = None
                    else:
                        export_results[format_type] = result

            else:
                # 串行执行
                export_results = {}
                for format_type in formats:
                    if format_type == 'pdf':
                        result = await self.export_as_pdf(lesson_plan, teacher, options, use_cache)
                    elif format_type == 'markdown':
                        result = await self.export_as_markdown(lesson_plan, teacher, options, use_cache)
                    else:
                        result = None
                    export_results[format_type] = result

            execution_time = time.time() - start_time
            successful_formats = [f for f, r in export_results.items() if r is not None]
            logger.info(
                f"并发导出完成: {lesson_plan['title']} "
                f"(耗时: {execution_time:.2f}s, 成功: {successful_formats})"
            )

            return export_results

        except Exception as e:
            logger.error(f"并发导出失败: {str(e)}")
            raise Exception(f"并发导出失败: {str(e)}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        import asyncio
        try:
            # 创建一个新的事件循环来获取锁
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            cache_size = len(self._cache)
            total_cache = len(self._cache_timestamps)
            loop.close()

            # 计算缓存使用率
            cache_usage_rate = (cache_size / self.MAX_CACHE_SIZE) * 100

            return {
                'cache_size': cache_size,
                'max_cache_size': self.MAX_CACHE_SIZE,
                'cache_usage_rate': round(cache_usage_rate, 2),
                'cache_ttl': self.CACHE_TTL,
                'total_cached': total_cache
            }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {
                'cache_size': 0,
                'max_cache_size': self.MAX_CACHE_SIZE,
                'cache_usage_rate': 0,
                'cache_ttl': self.CACHE_TTL,
                'total_cached': 0
            }

    async def clear_cache(self):
        """清空缓存"""
        async with self._cache_lock:
            self._cache.clear()
            self._cache_timestamps.clear()
            logger.info("缓存已清空")

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标

        Returns:
            Dict[str, Any]: 性能指标
        """
        memory_usage = self._monitor_memory_usage()
        cache_stats = self.get_cache_stats()

        return {
            'memory_usage_mb': round(memory_usage, 2),
            'memory_alert_threshold': self._memory_alert_threshold,
            'memory_history_count': len(self._memory_usage_history),
            'cache_stats': cache_stats,
            'active_exports': len(asyncio.all_tasks())  # 当前活跃任务数
        }


# 创建全局单例
_lesson_plan_export_service: Optional[LessonPlanExportService] = None


def get_lesson_plan_export_service() -> LessonPlanExportService:
    """
    获取教案导出服务单例

    Returns:
        LessonPlanExportService: 教案导出服务实例
    """
    global _lesson_plan_export_service
    if _lesson_plan_export_service is None:
        _lesson_plan_export_service = LessonPlanExportService()
    return _lesson_plan_export_service
