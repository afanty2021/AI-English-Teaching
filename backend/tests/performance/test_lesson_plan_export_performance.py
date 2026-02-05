"""
教案导出性能测试
测试导出功能的性能和优化效果
"""
import asyncio
import time
import pytest
from typing import Dict, Any

from app.services.lesson_plan_export_service import LessonPlanExportService
from app.services.ppt_export_service import PPTExportService


class TestLessonPlanExportPerformance:
    """教案导出性能测试"""

    @pytest.fixture
    def large_lesson_plan(self) -> Dict[str, Any]:
        """创建大型教案数据用于性能测试"""
        return {
            'id': 'large-test-id',
            'title': '大型教案性能测试',
            'topic': 'Performance Test',
            'level': 'B2',
            'duration': 180,  # 3小时课程
            'target_exam': 'TOEFL',
            'status': 'generated',
            'objectives': {
                'language_knowledge': [f'知识点{i}' for i in range(50)],
                'language_skills': {
                    'listening': [f'听力技能{i}' for i in range(30)],
                    'speaking': [f'口语技能{i}' for i in range(30)],
                    'reading': [f'阅读技能{i}' for i in range(30)],
                    'writing': [f'写作技能{i}' for i in range(30)]
                },
                'learning_strategies': [f'学习策略{i}' for i in range(20)],
                'cultural_awareness': [f'文化意识{i}' for i in range(20)],
                'emotional_attitudes': [f'情感态度{i}' for i in range(20)]
            },
            'vocabulary': {
                'noun': [
                    {
                        'word': f'test_noun_{i}',
                        'phonetic': f'/test_noun_{i}/',
                        'part_of_speech': 'n.',
                        'meaning_cn': f'测试名词{i}',
                        'meaning_en': f'Test noun {i}',
                        'example_sentence': f'This is test noun {i}.',
                        'example_translation': f'这是测试名词{i}。',
                        'collocations': [f'搭配{i}', f'词语组合{i}'],
                        'synonyms': [f'同义词{i}', f'近义词{i}'],
                        'antonyms': [f'反义词{i}', f'对立词{i}'],
                        'difficulty': 'B2'
                    } for i in range(200)
                ],
                'verb': [
                    {
                        'word': f'test_verb_{i}',
                        'phonetic': f'/test_verb_{i}/',
                        'part_of_speech': 'v.',
                        'meaning_cn': f'测试动词{i}',
                        'meaning_en': f'Test verb {i}',
                        'example_sentence': f'Ve test verb {i} every day.',
                        'example_translation': f'我们每天测试动词{i}。',
                        'collocations': [f'动词搭配{i}'],
                        'synonyms': [f'动词同义词{i}'],
                        'antonyms': [f'动词反义词{i}'],
                        'difficulty': 'B2'
                    } for i in range(150)
                ]
            },
            'grammar_points': [
                {
                    'name': f'语法点{i}',
                    'description': f'这是第{i}个语法点的详细描述，包含多种用法和规则。',
                    'rule': f'第{i}个语法点的规则说明，包含各种情况和例外。',
                    'examples': [f'例句{i}-{j}' for j in range(10)],
                    'common_mistakes': [f'常见错误{i}-{j}' for j in range(5)],
                    'practice_tips': [f'练习建议{i}-{j}' for j in range(5)]
                } for i in range(30)
            ],
            'teaching_structure': {
                'warm_up': {
                    'phase': 'warm-up',
                    'title': f'热身活动{i}',
                    'duration': 15,
                    'description': f'详细的热身活动描述，包含多个环节和步骤。',
                    'activities': [f'活动{i}-{j}' for j in range(10)],
                    'teacher_actions': [f'教师活动{i}-{j}' for j in range(8)],
                    'student_actions': [f'学生活动{i}-{j}' for j in range(8)],
                    'materials': [f'教学材料{i}-{j}' for j in range(5)]
                } for i in range(10)
            },
            'leveled_materials': [
                {
                    'level': f'B{i%3}',
                    'title': f'分层材料{i}',
                    'content': f'这是第{i}个分层材料的详细内容。' * 50,  # 长内容
                    'word_count': 1000 + i * 100,
                    'vocabulary_list': [
                        {
                            'word': f'材料词汇{i}-{j}',
                            'phonetic': f'/material_vocab_{i}_{j}/',
                            'part_of_speech': 'n.',
                            'meaning_cn': f'材料词汇{i}-{j}的中文意思',
                            'example_sentence': f'Example sentence for material vocab {i}-{j}.',
                            'example_translation': f'材料词汇{i}-{j}的例句翻译。',
                            'difficulty': f'B{i%3}'
                        } for j in range(20)
                    ],
                    'comprehension_questions': [f'理解问题{i}-{j}' for j in range(10)],
                    'difficulty_notes': f'这是第{i}个材料的难度说明，包含详细的教学建议。'
                } for i in range(20)
            ],
            'exercises': {
                'multiple_choice': [
                    {
                        'id': f'mc_{i}',
                        'type': 'multiple_choice',
                        'question': f'这是第{i}道选择题的题干内容，包含详细的描述和背景信息。',
                        'options': [f'选项A-{i}', f'选项B-{i}', f'选项C-{i}', f'选项D-{i}'],
                        'correct_answer': f'选项A-{i}',
                        'explanation': f'这是第{i}道题的详细解析，包含解题思路和知识点说明。',
                        'points': 2,
                        'difficulty': 'B2'
                    } for i in range(50)
                ],
                'fill_blank': [
                    {
                        'id': f'fb_{i}',
                        'type': 'fill_blank',
                        'question': f'这是第{i}道填空题的题干，包含完整的句子和上下文信息。',
                        'options': [f'选项{i}', f'选项2{i}', f'选项3{i}'],
                        'correct_answer': f'正确答案{i}',
                        'explanation': f'第{i}道填空题的解析和说明。',
                        'points': 3,
                        'difficulty': 'B2'
                    } for i in range(30)
                ]
            },
            'ppt_outline': [
                {
                    'slide_number': i,
                    'title': f'PPT幻灯片{i}',
                    'content': [f'内容要点{j}' for j in range(15)],
                    'notes': f'这是第{i}张幻灯片的演讲者备注，包含详细的讲解提示和注意事项。' * 5,
                    'layout': 'title_content'
                } for i in range(100)  # 100张幻灯片
            ],
            'resources': {
                'audio': [f'音频资源{i}' for i in range(20)],
                'video': [f'视频资源{i}' for i in range(15)],
                'worksheets': [f'练习题单{i}' for i in range(25)],
                'digital': [f'数字资源{i}' for i in range(30)]
            },
            'teaching_notes': f'这是教学反思的详细内容。' * 20,
            'generation_time_ms': 5000,
            'created_at': '2026-02-05T10:00:00',
            'updated_at': '2026-02-05T10:00:00'
        }

    @pytest.fixture
    def sample_teacher(self) -> Dict[str, Any]:
        """示例教师数据"""
        return {
            'username': '性能测试教师',
            'email': 'performance@test.com',
            'role': 'teacher'
        }

    @pytest.mark.asyncio
    async def test_pdf_export_performance(self, large_lesson_plan, sample_teacher):
        """测试PDF导出性能"""
        service = LessonPlanExportService()

        # 测试大型教案PDF导出性能
        start_time = time.time()
        result = await service.export_as_pdf(large_lesson_plan, sample_teacher)
        end_time = time.time()

        execution_time = end_time - start_time

        # 验证结果
        assert isinstance(result, bytes)
        assert len(result) > 0

        # 性能要求：大型教案PDF导出应在30秒内完成
        print(f"\n大型教案PDF导出耗时: {execution_time:.2f}秒")
        assert execution_time < 30.0, f"PDF导出耗时过长: {execution_time:.2f}秒"

    @pytest.mark.asyncio
    async def test_markdown_export_performance(self, large_lesson_plan, sample_teacher):
        """测试Markdown导出性能"""
        service = LessonPlanExportService()

        # 测试大型教案Markdown导出性能
        start_time = time.time()
        result = await service.export_as_markdown(large_lesson_plan, sample_teacher)
        end_time = time.time()

        execution_time = end_time - start_time

        # 验证结果
        assert isinstance(result, str)
        assert len(result) > 0
        assert '# 大型教案性能测试' in result

        # 性能要求：大型教案Markdown导出应在5秒内完成
        print(f"\n大型教案Markdown导出耗时: {execution_time:.2f}秒")
        assert execution_time < 5.0, f"Markdown导出耗时过长: {execution_time:.2f}秒"

    @pytest.mark.asyncio
    async def test_ppt_export_performance(self, large_lesson_plan):
        """测试PPT导出性能"""
        service = PPTExportService()

        # 测试大型教案PPT导出性能
        start_time = time.time()
        result = await service.export_as_pptx(large_lesson_plan)
        end_time = time.time()

        execution_time = end_time - start_time

        # 验证结果
        assert isinstance(result, bytes)
        assert len(result) > 0

        # 性能要求：大型教案PPT导出应在20秒内完成
        print(f"\n大型教案PPT导出耗时: {execution_time:.2f}秒")
        assert execution_time < 20.0, f"PPT导出耗时过长: {execution_time:.2f}秒"

    @pytest.mark.asyncio
    async def test_ppt_html_export_performance(self, large_lesson_plan):
        """测试PPT HTML导出性能"""
        service = PPTExportService()

        # 测试PPT HTML导出性能
        start_time = time.time()
        result = await service.export_as_html(large_lesson_plan)
        end_time = time.time()

        execution_time = end_time - start_time

        # 验证结果
        assert isinstance(result, str)
        assert len(result) > 0
        assert '<!DOCTYPE html>' in result
        assert '大型教案性能测试' in result

        # 性能要求：PPT HTML导出应在3秒内完成
        print(f"\nPPT HTML导出耗时: {execution_time:.2f}秒")
        assert execution_time < 3.0, f"PPT HTML导出耗时过长: {execution_time:.2f}秒"

    @pytest.mark.asyncio
    async def test_concurrent_exports(self, large_lesson_plan, sample_teacher):
        """测试并发导出性能"""
        service = LessonPlanExportService()

        # 并发执行多个导出任务
        start_time = time.time()
        tasks = [
            service.export_as_pdf(large_lesson_plan, sample_teacher),
            service.export_as_markdown(large_lesson_plan, sample_teacher),
            service.export_as_pdf(large_lesson_plan, sample_teacher),
            service.export_as_markdown(large_lesson_plan, sample_teacher),
        ]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        execution_time = end_time - start_time

        # 验证结果
        assert len(results) == 4
        assert all(isinstance(result, bytes) or isinstance(result, str) for result in results)

        # 性能要求：并发导出应在60秒内完成
        print(f"\n并发导出(4个任务)总耗时: {execution_time:.2f}秒")
        assert execution_time < 60.0, f"并发导出耗时过长: {execution_time:.2f}秒"

    @pytest.mark.asyncio
    async def test_memory_usage(self, large_lesson_plan, sample_teacher):
        """测试内存使用"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        service = LessonPlanExportService()

        # 执行多次导出
        for i in range(10):
            await service.export_as_pdf(large_lesson_plan, sample_teacher)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # 内存增长应小于500MB
        print(f"\n内存使用情况:")
        print(f"初始内存: {initial_memory:.2f} MB")
        print(f"最终内存: {final_memory:.2f} MB")
        print(f"内存增长: {memory_increase:.2f} MB")

        assert memory_increase < 500, f"内存使用过高: {memory_increase:.2f} MB"

    @pytest.mark.asyncio
    async def test_small_lesson_export_performance(self, sample_teacher):
        """测试小型教案导出性能"""
        small_lesson_plan = {
            'id': 'small-test-id',
            'title': '小型教案',
            'topic': 'Small',
            'level': 'A1',
            'duration': 30,
            'status': 'generated',
            'objectives': {'language_knowledge': ['基础词汇']},
            'vocabulary': {'noun': [{'word': 'test', 'meaning_cn': '测试'}]},
            'grammar_points': [],
            'teaching_structure': {},
            'leveled_materials': [],
            'exercises': {},
            'ppt_outline': []
        }

        service = LessonPlanExportService()

        # 测试小型教案导出
        start_time = time.time()
        pdf_result = await service.export_as_pdf(small_lesson_plan, sample_teacher)
        md_result = await service.export_as_markdown(small_lesson_plan, sample_teacher)
        end_time = time.time()

        execution_time = end_time - start_time

        # 验证结果
        assert isinstance(pdf_result, bytes)
        assert isinstance(md_result, str)

        # 性能要求：小型教案导出应在2秒内完成
        print(f"\n小型教案导出耗时: {execution_time:.2f}秒")
        assert execution_time < 2.0, f"小型教案导出耗时过长: {execution_time:.2f}秒"


class TestLessonPlanExportOptimization:
    """教案导出优化测试"""

    @pytest.mark.asyncio
    async def test_template_rendering_speed(self):
        """测试模板渲染速度"""
        # 测试不同大小模板的渲染速度
        for size in ['small', 'medium', 'large']:
            lesson_plan = self._generate_lesson_plan_by_size(size)
            teacher = {'username': 'Test', 'email': 'test@test.com'}

            service = LessonPlanExportService()

            start_time = time.time()
            result = await service.export_as_markdown(lesson_plan, teacher)
            end_time = time.time()

            execution_time = end_time - start_time
            print(f"\n{size}模板渲染耗时: {execution_time:.2f}秒")

            assert execution_time < 10.0, f"{size}模板渲染耗时过长"

    def _generate_lesson_plan_by_size(self, size: str) -> Dict[str, Any]:
        """根据大小生成测试教案"""
        sizes = {
            'small': 10,
            'medium': 50,
            'large': 100
        }

        count = sizes.get(size, 10)

        return {
            'id': f'{size}-test-id',
            'title': f'{size.title()} Lesson Plan',
            'topic': f'{size} Topic',
            'level': 'B1',
            'duration': 60,
            'status': 'generated',
            'objectives': {'language_knowledge': [f'知识点{i}' for i in range(count)]},
            'vocabulary': {'noun': [{'word': f'test{i}', 'meaning_cn': f'测试{i}'} for i in range(count)]},
            'grammar_points': [{'name': f'语法{i}', 'description': f'描述{i}'} for i in range(count // 2)],
            'teaching_structure': {'warm_up': {'title': '热身', 'duration': 5}},
            'leveled_materials': [],
            'exercises': {},
            'ppt_outline': [{'slide_number': i, 'title': f'Slide {i}'} for i in range(count // 10)]
        }

    @pytest.mark.asyncio
    async def test_cache_effectiveness(self):
        """测试缓存效果"""
        lesson_plan = {
            'id': 'cache-test-id',
            'title': 'Cache Test',
            'topic': 'Cache',
            'level': 'A1',
            'duration': 45,
            'status': 'generated',
            'objectives': {},
            'vocabulary': {},
            'grammar_points': [],
            'teaching_structure': {},
            'leveled_materials': [],
            'exercises': {},
            'ppt_outline': []
        }
        teacher = {'username': 'Test', 'email': 'test@test.com'}

        service = LessonPlanExportService()

        # 第一次导出
        start_time = time.time()
        result1 = await service.export_as_markdown(lesson_plan, teacher)
        first_export_time = time.time() - start_time

        # 第二次导出（应该使用缓存）
        start_time = time.time()
        result2 = await service.export_as_markdown(lesson_plan, teacher)
        second_export_time = time.time() - start_time

        # 验证结果一致性
        assert result1 == result2

        # 第二次应该更快（缓存效果）
        print(f"\n首次导出耗时: {first_export_time:.3f}秒")
        print(f"二次导出耗时: {second_export_time:.3f}秒")
        print(f"缓存加速比: {first_export_time / second_export_time:.2f}x")

        # 缓存应该提供至少2倍加速
        assert second_export_time < first_export_time / 2, "缓存未生效"


if __name__ == "__main__":
    # 运行性能测试的示例
    pytest.main([__file__, "-v", "--tb=short"])
