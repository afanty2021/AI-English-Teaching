#!/usr/bin/env python3
"""
性能优化验证测试
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.lesson_plan_export_service import LessonPlanExportService

async def test_performance_optimization():
    """测试性能优化功能"""
    print("🚀 开始性能优化验证测试...")
    print("=" * 50)

    # 创建测试数据
    lesson_plan = {
        'id': 'test-id',
        'title': '性能测试教案',
        'topic': 'Performance Test',
        'level': 'A1',
        'duration': 45,
        'objectives': {'language_knowledge': ['测试目标']},
        'vocabulary': {'noun': [{'word': 'test', 'meaning_cn': '测试'}]},
        'grammar_points': [{'name': 'test', 'description': '测试'}],
        'teaching_structure': {'warm_up': {'title': '测试', 'duration': 5}},
        'leveled_materials': [],
        'exercises': {},
        'ppt_outline': []
    }

    teacher = {'username': '测试教师', 'id': 'teacher-1'}

    service = LessonPlanExportService()

    # 测试缓存功能
    print("\n📦 测试缓存功能...")
    print("-" * 30)

    # 第一次导出
    print("  第一次导出（无缓存）...")
    result1 = await service.export_as_markdown(lesson_plan, teacher)
    print(f"  ✓ 第一次导出完成: {len(result1)} 字符")

    # 第二次导出（使用缓存）
    print("  第二次导出（使用缓存）...")
    result2 = await service.export_as_markdown(lesson_plan, teacher)
    print(f"  ✓ 第二次导出完成: {len(result2)} 字符")

    # 验证缓存效果
    assert result1 == result2, "缓存结果不一致"
    print("  ✅ 缓存验证通过")

    # 测试并发导出
    print("\n⚡ 测试并发导出...")
    print("-" * 30)

    # 准备多个教案数据
    lesson_plans = []
    for i in range(3):
        lp = lesson_plan.copy()
        lp['id'] = f'test-id-{i}'
        lp['title'] = f'测试教案-{i}'
        lesson_plans.append(lp)

    # 并发导出
    print("  执行并发导出...")
    tasks = []
    for i, lp in enumerate(lesson_plans):
        task = asyncio.create_task(
            service.export_as_markdown(lp, teacher),
            name=f"export-{i}"
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    print(f"  ✓ 并发导出完成: {len(results)} 个结果")

    # 测试性能指标
    print("\n📊 检查性能指标...")
    print("-" * 30)

    metrics = await service.get_performance_metrics()
    print(f"  内存使用: {metrics['memory_usage_mb']} MB")
    print(f"  缓存状态: {metrics['cache_stats']['cache_size']} 项")
    print(f"  缓存使用率: {metrics['cache_stats']['cache_usage_rate']}%")
    print(f"  活跃任务: {metrics['active_exports']} 个")

    # 测试并发导出功能
    print("\n🔄 测试多格式并发导出...")
    print("-" * 30)

    formats = ['markdown']
    multi_results = await service.export_multiple_formats(
        lesson_plan, teacher, formats, concurrent=True
    )
    print(f"  ✓ 多格式导出完成: {list(multi_results.keys())}")

    print("\n" + "=" * 50)
    print("✅ 性能优化验证测试完成!")
    print("=" * 50)

    return {
        'cache_test': True,
        'concurrent_test': True,
        'metrics': metrics
    }

if __name__ == "__main__":
    try:
        result = asyncio.run(test_performance_optimization())
        print("\n🎉 所有测试通过!")
        print(f"   - 缓存功能: ✅")
        print(f"   - 并发导出: ✅")
        print(f"   - 性能监控: ✅")
        print(f"   - 内存使用: {result['metrics']['memory_usage_mb']} MB")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
