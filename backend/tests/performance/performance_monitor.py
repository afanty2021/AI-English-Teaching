"""
性能监控工具

提供数据库连接池监控、API响应时间统计、内存使用分析等功能。
"""
import asyncio
import psutil
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from collections import deque

import asyncpg
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import settings


@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatabasePoolStats:
    """数据库连接池统计"""
    pool_size: int
    checked_in: int
    checked_out: int
    overflow: int
    checked_out_duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class PerformanceMonitor:
    """
    性能监控器

    用于监控API响应时间、数据库连接池状态、内存使用等指标。
    """

    def __init__(self):
        self.metrics: deque = deque(maxlen=1000)
        self.response_times: Dict[str, deque] = {}
        self.start_time = time.time()

    def record_metric(self, name: str, value: float, unit: str = "ms", **metadata):
        """记录性能指标"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            metadata=metadata
        )
        self.metrics.append(metric)

    def record_response_time(self, endpoint: str, response_time_ms: float):
        """记录API响应时间"""
        if endpoint not in self.response_times:
            self.response_times[endpoint] = deque(maxlen=100)
        self.response_times[endpoint].append(response_time_ms)

    def get_percentile(self, endpoint: str, percentile: float = 0.95) -> Optional[float]:
        """获取响应时间的百分位数"""
        if endpoint not in self.response_times:
            return None
        times = list(self.response_times[endpoint])
        if not times:
            return None
        times.sort()
        index = int(len(times) * percentile)
        return times[min(index, len(times) - 1)]

    def get_average_response_time(self, endpoint: str) -> Optional[float]:
        """获取平均响应时间"""
        if endpoint not in self.response_times:
            return None
        times = list(self.response_times[endpoint])
        if not times:
            return None
        return sum(times) / len(times)

    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        process = psutil.Process()
        mem_info = process.memory_info()
        return {
            "rss_mb": mem_info.rss / 1024 / 1024,  # 常驻内存集
            "vms_mb": mem_info.vms / 1024 / 1024,  # 虚拟内存大小
            "percent": process.memory_percent(),  # 内存使用百分比
        }

    def get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        process = psutil.Process()
        return process.cpu_percent(interval=0.1)

    def get_uptime(self) -> timedelta:
        """获取运行时长"""
        return timedelta(seconds=int(time.time() - self.start_time))

    def get_stats_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        stats = {
            "uptime_seconds": self.get_uptime().total_seconds(),
            "memory_usage": self.get_memory_usage(),
            "cpu_usage": self.get_cpu_usage(),
            "endpoints": {}
        }

        for endpoint in self.response_times:
            times = list(self.response_times[endpoint])
            if times:
                stats["endpoints"][endpoint] = {
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "count": len(times),
                    "p95": self.get_percentile(endpoint, 0.95),
                    "p99": self.get_percentile(endpoint, 0.99)
                }

        return stats


class DatabaseConnectionMonitor:
    """
    数据库连接监控器

    监控SQLAlchemy连接池的状态和性能。
    """

    def __init__(self, engine: Engine):
        self.engine = engine
        self.stats: List[DatabasePoolStats] = []
        self._setup_listeners()

    def _setup_listeners(self):
        """设置SQLAlchemy事件监听器"""

        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """连接创建时"""
            pass

        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """从连接池获取连接时"""
            pass

        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """归还连接到连接池时"""
            pass

    def get_pool_status(self) -> DatabasePoolStats:
        """获取连接池状态"""
        pool = self.engine.pool
        return DatabasePoolStats(
            pool_size=pool.size(),
            checked_in=pool.checkedin(),
            checked_out=pool.checkedout(),
            overflow=pool.overflow(),
            checked_out_duration_ms=0  # 需要额外跟踪
        )

    async def get_async_pool_status(self, engine: AsyncEngine) -> Dict[str, Any]:
        """获取异步连接池状态"""
        pool = engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "max_overflow": pool._max_overflow
        }

    async def test_connection_performance(self, iterations: int = 100) -> Dict[str, float]:
        """测试数据库连接性能"""
        results = {
            "connect_times": [],
            "query_times": [],
            "total_times": []
        }

        for _ in range(iterations):
            start = time.time()

            # 测试连接
            conn_start = time.time()
            conn = await asyncpg.connect(settings.DATABASE_URL)
            results["connect_times"].append((time.time() - conn_start) * 1000)

            # 测试简单查询
            query_start = time.time()
            await conn.fetchval("SELECT 1")
            results["query_times"].append((time.time() - query_start) * 1000)

            await conn.close()
            results["total_times"].append((time.time() - start) * 1000)

        return {
            "avg_connect_ms": sum(results["connect_times"]) / len(results["connect_times"]),
            "avg_query_ms": sum(results["query_times"]) / len(results["query_times"]),
            "avg_total_ms": sum(results["total_times"]) / len(results["total_times"]),
            "min_connect_ms": min(results["connect_times"]),
            "max_connect_ms": max(results["connect_times"])
        }


class ResponseTimeMiddleware:
    """
    响应时间中间件

    用于记录FastAPI端点的响应时间。
    """

    def __init__(self, app, monitor: PerformanceMonitor):
        self.app = app
        self.monitor = monitor
        self._setup_middleware()

    def _setup_middleware(self):
        """设置中间件"""

        @self.app.middleware("http")
        async def add_response_time_middleware(request, call_next):
            """添加响应时间记录"""
            start_time = time.time()

            response = await call_next(request)

            # 计算响应时间
            process_time = (time.time() - start_time) * 1000
            endpoint = f"{request.method} {request.url.path}"

            # 记录到监控器
            self.monitor.record_response_time(endpoint, process_time)

            # 添加响应头
            response.headers["X-Process-Time"] = str(process_time)

            return response


def format_performance_report(stats: Dict[str, Any]) -> str:
    """格式化性能报告"""
    lines = [
        "=" * 80,
        "Performance Report",
        "=" * 80,
        f"Generated: {datetime.utcnow().isoformat()}",
        "",
        "## System Resources",
        "-" * 40,
        f"Uptime: {timedelta(seconds=int(stats['uptime_seconds']))}",
        "",
        "Memory Usage:",
        f"  RSS: {stats['memory_usage']['rss_mb']:.2f} MB",
        f"  VMS: {stats['memory_usage']['vms_mb']:.2f} MB",
        f"  Percent: {stats['memory_usage']['percent']:.2f}%",
        "",
        f"CPU Usage: {stats['cpu_usage']:.2f}%",
        "",
        "## API Response Times",
        "-" * 40,
    ]

    for endpoint, metrics in stats.get("endpoints", {}).items():
        lines.extend([
            f"{endpoint}:",
            f"  Avg: {metrics['avg']:.2f} ms",
            f"  Min: {metrics['min']:.2f} ms",
            f"  Max: {metrics['max']:.2f} ms",
            f"  P95: {metrics['p95']:.2f} ms",
            f"  P99: {metrics['p99']:.2f} ms",
            f"  Requests: {metrics['count']}",
            ""
        ])

    lines.append("=" * 80)
    return "\n".join(lines)


@asynccontextmanager
async def performance_timer(monitor: PerformanceMonitor, name: str):
    """
    性能计时上下文管理器

    用法:
        async with performance_timer(monitor, "operation_name"):
            # 执行操作
            pass
    """
    start = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start) * 1000
        monitor.record_metric(name, duration_ms, "ms")
