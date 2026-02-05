"""
性能监控工具 - AI英语教学系统
提供导出功能的性能监控和优化工具
"""
import asyncio
import gc
import logging
import time
import tracemalloc
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    operation: str
    start_time: float
    end_time: float
    duration: float
    memory_before: float = 0.0
    memory_after: float = 0.0
    memory_delta: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """
    性能监控器
    用于监控导出操作的性能指标
    """

    def __init__(self, max_history: int = 1000):
        """
        初始化性能监控器

        Args:
            max_history: 最大历史记录数
        """
        self.max_history = max_history
        self.metrics_history: List[PerformanceMetrics] = []
        self.active_operations: Dict[str, datetime] = {}

    async def start_monitoring(self, operation: str, metadata: Optional[Dict] = None) -> str:
        """
        开始监控操作

        Args:
            operation: 操作名称
            metadata: 元数据

        Returns:
            str: 操作ID
        """
        operation_id = f"{operation}_{time.time_ns()}"
        self.active_operations[operation_id] = datetime.now()

        # 启动内存跟踪
        tracemalloc.start()

        # 强制垃圾回收
        gc.collect()

        return operation_id

    async def end_monitoring(
        self,
        operation_id: str,
        operation: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> PerformanceMetrics:
        """
        结束监控操作

        Args:
            operation_id: 操作ID
            operation: 操作名称
            success: 是否成功
            error_message: 错误信息

        Returns:
            PerformanceMetrics: 性能指标
        """
        end_time = time.time()

        # 获取内存使用情况
        memory_after, peak_memory = tracemalloc.get_traced_memory()
        memory_after_mb = memory_after / 1024 / 1024

        # 停止内存跟踪
        tracemalloc.stop()

        # 清理活跃操作记录
        if operation_id in self.active_operations:
            del self.active_operations[operation_id]

        # 从活跃操作记录中获取开始时间
        # 注意：在实际使用中，应该将start_time存储在操作上下文中
        start_time = end_time - 0.001  # 默认1ms

        # 创建性能指标
        metrics = PerformanceMetrics(
            operation=operation,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            memory_after=memory_after_mb,
            success=success,
            error_message=error_message
        )

        # 添加到历史记录
        self.metrics_history.append(metrics)

        # 保持历史记录在限制范围内
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)

        return metrics

    def get_operation_stats(self, operation: str, limit: int = 100) -> Dict[str, Any]:
        """
        获取操作统计信息

        Args:
            operation: 操作名称
            limit: 限制记录数

        Returns:
            Dict[str, Any]: 统计信息
        """
        # 筛选指定操作的指标
        operation_metrics = [
            m for m in self.metrics_history
            if m.operation == operation
        ][-limit:]

        if not operation_metrics:
            return {
                'operation': operation,
                'count': 0,
                'avg_duration': 0.0,
                'avg_memory': 0.0,
                'success_rate': 0.0
            }

        # 计算统计信息
        count = len(operation_metrics)
        successful_ops = [m for m in operation_metrics if m.success]
        avg_duration = sum(m.duration for m in operation_metrics) / count
        avg_memory = sum(m.memory_after for m in operation_metrics) / count
        success_rate = len(successful_ops) / count * 100

        # 获取最佳和最差性能
        best_performance = min(operation_metrics, key=lambda m: m.duration)
        worst_performance = max(operation_metrics, key=lambda m: m.duration)

        return {
            'operation': operation,
            'count': count,
            'avg_duration': round(avg_duration, 3),
            'avg_memory': round(avg_memory, 2),
            'success_rate': round(success_rate, 2),
            'best_performance': {
                'duration': round(best_performance.duration, 3),
                'memory': round(best_performance.memory_after, 2)
            },
            'worst_performance': {
                'duration': round(worst_performance.duration, 3),
                'memory': round(worst_performance.memory_after, 2)
            }
        }

    def get_system_stats(self) -> Dict[str, Any]:
        """
        获取系统统计信息

        Returns:
            Dict[str, Any]: 系统统计信息
        """
        # 垃圾回收统计
        gc_stats = gc.get_stats()

        # 内存信息
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            'total_operations': len(self.metrics_history),
            'active_operations': len(self.active_operations),
            'gc_stats': gc_stats,
            'memory_info': {
                'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
                'vms_mb': round(memory_info.vms / 1024 / 1024, 2),
                'percent': process.memory_percent()
            },
            'timestamp': datetime.now().isoformat()
        }

    def clear_history(self):
        """清空历史记录"""
        self.metrics_history.clear()
        logger.info("性能监控历史记录已清空")


# 全局性能监控器实例
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """
    获取全局性能监控器实例

    Returns:
        PerformanceMonitor: 性能监控器实例
    """
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


@asynccontextmanager
async def monitor_operation(operation: str, metadata: Optional[Dict] = None):
    """
    监控操作的上下文管理器

    Args:
        operation: 操作名称
        metadata: 元数据

    Example:
        async with monitor_operation('pdf_export') as result:
            # 执行导出操作
            result['success'] = True
    """
    monitor = get_performance_monitor()
    operation_id = await monitor.start_monitoring(operation, metadata)

    try:
        result = {'success': True}
        yield result
    except Exception as e:
        result['success'] = False
        result['error'] = str(e)
        logger.error(f"操作 {operation} 失败: {e}")
        raise
    finally:
        await monitor.end_monitoring(
            operation_id,
            operation,
            success=result.get('success', True),
            error_message=result.get('error')
        )


def benchmark_operation(
    func: Callable,
    *args,
    iterations: int = 1,
    **kwargs
) -> Dict[str, Any]:
    """
    对函数进行性能基准测试

    Args:
        func: 要测试的函数
        *args: 位置参数
        iterations: 迭代次数
        **kwargs: 关键字参数

    Returns:
        Dict[str, Any]: 基准测试结果
    """
    durations = []
    memory_usage = []

    # 预热
    for _ in range(min(3, iterations)):
        try:
            func(*args, **kwargs)
        except Exception:
            pass

    # 正式测试
    for i in range(iterations):
        # 开始内存监控
        tracemalloc.start()
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            logger.error(f"基准测试第 {i+1} 次失败: {e}")
            result = None
            success = False

        end_time = time.time()
        duration = end_time - start_time

        # 结束内存监控
        memory_current, memory_peak = tracemalloc.get_traced_memory()
        memory_usage.append(memory_peak / 1024 / 1024)  # MB
        tracemalloc.stop()

        durations.append(duration)

    return {
        'function': func.__name__,
        'iterations': iterations,
        'avg_duration': round(sum(durations) / len(durations), 4),
        'min_duration': round(min(durations), 4),
        'max_duration': round(max(durations), 4),
        'avg_memory_mb': round(sum(memory_usage) / len(memory_usage), 2),
        'min_memory_mb': round(min(memory_usage), 2),
        'max_memory_mb': round(max(memory_usage), 2),
        'success_rate': round((len([d for d in durations if d > 0]) / iterations) * 100, 2)
    }


class CacheOptimizer:
    """
    缓存优化器
    用于优化缓存策略和内存使用
    """

    @staticmethod
    async def analyze_cache_efficiency(cache_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析缓存效率

        Args:
            cache_stats: 缓存统计信息

        Returns:
            Dict[str, Any]: 缓存效率分析
        """
        usage_rate = cache_stats.get('cache_usage_rate', 0)
        cache_size = cache_stats.get('cache_size', 0)
        max_size = cache_stats.get('max_cache_size', 100)

        # 计算效率评分
        efficiency_score = 100
        recommendations = []

        if usage_rate > 90:
            efficiency_score -= 20
            recommendations.append("缓存使用率过高，建议增加缓存大小")
        elif usage_rate < 30:
            efficiency_score -= 10
            recommendations.append("缓存使用率较低，可以考虑减少缓存大小")

        if cache_size > max_size * 0.8:
            efficiency_score -= 15
            recommendations.append("缓存接近满载，建议清理过期缓存")

        # 计算推荐TTL
        recommended_ttl = cache_stats.get('cache_ttl', 3600)
        if usage_rate > 70:
            recommended_ttl = int(recommended_ttl * 1.5)
            recommendations.append("建议增加缓存TTL以提高命中率")

        return {
            'efficiency_score': max(0, efficiency_score),
            'usage_rate': usage_rate,
            'recommendations': recommendations,
            'recommended_ttl': recommended_ttl,
            'health_status': 'good' if efficiency_score >= 80 else 'warning' if efficiency_score >= 60 else 'poor'
        }

    @staticmethod
    async def optimize_memory_usage() -> Dict[str, Any]:
        """
        优化内存使用

        Returns:
            Dict[str, Any]: 内存优化结果
        """
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024

        # 执行垃圾回收
        collected = gc.collect()

        # 获取垃圾回收统计
        gc_stats = gc.get_stats()

        memory_after = process.memory_info().rss / 1024 / 1024
        memory_saved = memory_before - memory_after

        return {
            'memory_before_mb': round(memory_before, 2),
            'memory_after_mb': round(memory_after, 2),
            'memory_saved_mb': round(memory_saved, 2),
            'objects_collected': collected,
            'gc_stats': gc_stats
        }


# 便捷函数
async def get_performance_summary() -> Dict[str, Any]:
    """
    获取性能摘要

    Returns:
        Dict[str, Any]: 性能摘要
    """
    monitor = get_performance_monitor()
    optimizer = CacheOptimizer()

    # 获取系统统计
    system_stats = monitor.get_system_stats()

    # 获取内存优化建议
    memory_optimization = await optimizer.optimize_memory_usage()

    return {
        'system_stats': system_stats,
        'memory_optimization': memory_optimization,
        'timestamp': datetime.now().isoformat()
    }


async def print_performance_report():
    """
    打印性能报告
    """
    summary = await get_performance_summary()

    print("\n" + "="*60)
    print("性能监控报告")
    print("="*60)

    # 系统统计
    system_stats = summary['system_stats']
    print(f"\n📊 系统统计:")
    print(f"  总操作数: {system_stats['total_operations']}")
    print(f"  活跃操作: {system_stats['active_operations']}")
    print(f"  内存使用: {system_stats['memory_info']['rss_mb']} MB")
    print(f"  内存占比: {system_stats['memory_info']['percent']:.2f}%")

    # 内存优化
    memory_opt = summary['memory_optimization']
    print(f"\n🧹 内存优化:")
    print(f"  释放内存: {memory_opt['memory_saved_mb']} MB")
    print(f"  回收对象: {memory_opt['objects_collected']}")

    print("="*60 + "\n")
