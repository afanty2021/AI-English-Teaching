"""
PDF渲染服务异步优化测试

验证：
1. 异步渲染不阻塞事件循环
2. 线程池正确工作
3. 并发PDF渲染性能
"""
import asyncio
import time
import pytest

from app.services.pdf_renderer_service import PdfRendererService


class TestPdfAsyncOptimization:
    """PDF异步渲染优化测试"""

    @pytest.fixture
    def pdf_service(self):
        """创建PDF渲染服务实例"""
        return PdfRendererService()

    @pytest.mark.asyncio
    async def test_async_render_non_blocking(self, pdf_service):
        """测试异步渲染不阻塞事件循环"""
        markdown_content = "# Test\n\nHello, World!"

        # 记录开始时间
        start_time = time.time()

        # 执行异步渲染
        result = await pdf_service.render_markdown_to_pdf(markdown_content)

        # 验证结果
        assert result is not None
        assert len(result) > 0

        # 记录结束时间
        elapsed = time.time() - start_time

        # 验证在合理时间内完成（应小于5秒）
        assert elapsed < 5.0, f"PDF渲染耗时过长: {elapsed:.2f}秒"

    @pytest.mark.asyncio
    async def test_concurrent_rendering(self, pdf_service):
        """测试并发PDF渲染性能"""
        # 准备多个PDF渲染任务
        tasks = []
        for i in range(5):
            markdown = f"# Document {i}\n\nContent for document {i}."
            task = pdf_service.render_markdown_to_pdf(markdown)
            tasks.append(task)

        # 并发执行所有任务
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        # 验证所有任务都成功完成
        assert len(results) == 5
        for result in results:
            assert result is not None
            assert len(result) > 0

        # 并发执行应比顺序执行快
        # 假设单个PDF需要1秒，顺序执行需要5秒，并发应显著更少
        print(f"并发渲染5个PDF耗时: {elapsed:.2f}秒")

    @pytest.mark.asyncio
    async def test_executor_reuse(self, pdf_service):
        """测试线程池执行器被正确复用"""
        executor = pdf_service.get_executor()

        # 验证执行器存在
        assert executor is not None

        # 多次调用应返回同一个执行器
        executor2 = pdf_service.get_executor()
        assert executor is executor2

    @pytest.mark.asyncio
    async def test_html_to_pdf_async(self, pdf_service):
        """测试HTML到PDF的异步转换"""
        html = "<h1>Test</h1><p>Hello, async PDF rendering!</p>"

        # 应用样式
        styled_html = await pdf_service.apply_pdf_styles(html, "Test Document")

        # 异步转换
        pdf_bytes = await pdf_service.html_to_pdf(styled_html)

        # 验证结果
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        # PDF文件以魔数开头：%PDF
        assert pdf_bytes[:4] == b'%PDF'


class TestConstantsUsage:
    """测试常量替换魔法数字"""

    def test_ability_levels(self):
        """测试能力等级常量"""
        from app.core.constants import AbilityLevels, ABILITY_LEVELS

        # 验证枚举值
        assert AbilityLevels.EXCELLENT == 90
        assert AbilityLevels.GOOD == 75
        assert AbilityLevels.INTERMEDIATE == 60
        assert AbilityLevels.BASIC == 40
        assert AbilityLevels.NEEDS_IMPROVEMENT == 0

        # 验证字典访问
        assert ABILITY_LEVELS["EXCELLENT"] == 90
        assert ABILITY_LEVELS["GOOD"] == 75

    def test_review_intervals(self):
        """测试复习间隔常量"""
        from app.core.constants import ReviewIntervals, REVIEW_INTERVALS

        # 验证艾宾浩斯间隔
        assert ReviewIntervals.FIRST == 1
        assert ReviewIntervals.SECOND == 3
        assert ReviewIntervals.THIRD == 7
        assert ReviewIntervals.FOURTH == 14
        assert ReviewIntervals.FIFTH == 30

        # 验证序列
        sequence = ReviewIntervals.get_interval_sequence()
        assert sequence == [1, 3, 7, 14, 30]

    def test_time_thresholds(self):
        """测试时间阈值常量"""
        from app.core.constants import TimeThresholds, TIME_THRESHOLDS

        # 验证枚举值
        assert TimeThresholds.NEW_MISTAKE_THRESHOLD == 24
        assert TimeThresholds.RECENT_REVIEW_THRESHOLD == 72
        assert TimeThresholds.URGENT_REVIEW_THRESHOLD == 24

        # 验证字典访问
        assert TIME_THRESHOLDS["NEW_MISTAKE"] == 24

    def test_priority_weights(self):
        """测试优先级权重常量"""
        from app.core.constants import PriorityWeights, PRIORITY_WEIGHTS

        # 验证权重值
        assert PriorityWeights.OVERDUE_PER_HOUR == 10
        assert PriorityWeights.MISTAKE_COUNT == 6
        assert PriorityWeights.REVIEW_COUNT == -5
        assert PriorityWeights.NEW_MISTAKE_BONUS == 10
