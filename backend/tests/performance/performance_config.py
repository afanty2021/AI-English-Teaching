"""
性能测试配置

定义性能阈值、测试参数等配置。
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class PerformanceThresholds:
    """性能阈值配置"""

    # API响应时间阈值（毫秒）
    API_P50_RESPONSE_TIME: float = 200  # 50%请求应在200ms内完成
    API_P95_RESPONSE_TIME: float = 500  # 95%请求应在500ms内完成
    API_P99_RESPONSE_TIME: float = 1000  # 99%请求应在1秒内完成

    # 数据库查询阈值（毫秒）
    DB_SIMPLE_QUERY_P95: float = 10  # 简单查询
    DB_COMPLEX_QUERY_P95: float = 100  # 复杂查询
    DB_TRANSACTION_P95: float = 50  # 事务操作

    # 连接延迟阈值（毫秒）
    CONNECTION_P95_LATENCY: float = 100

    # 吞吐量阈值（每秒请求数）
    MIN_THROUGHPUT: int = 100  # 最小吞吐量

    # 并发支持
    MAX_CONCURRENT_USERS: int = 1000
    RECOMMENDED_CONCURRENT_USERS: int = 500

    # 内存使用阈值
    MAX_MEMORY_MB: int = 512  # 最大内存使用（MB）

    # 成功率阈值
    MIN_SUCCESS_RATE: float = 0.99  # 最小成功率（99%）


@dataclass
class LoadTestParameters:
    """负载测试参数"""

    # 用户模拟
    MIN_USERS: int = 10
    MAX_USERS: int = 1000
    SPAWN_RATE: float = 10  # 每秒生成的用户数

    # 测试持续时间（秒）
    MIN_DURATION: int = 30
    MAX_DURATION: int = 600  # 10分钟
    DEFAULT_DURATION: int = 60

    # 等待时间范围（秒）
    MIN_WAIT: float = 1
    MAX_WAIT: float = 5

    # 权重分布
    WEIGHT_READ: int = 10  # 读操作权重
    WEIGHT_WRITE: int = 2  # 写操作权重
    WEIGHT_HEAVY: int = 1  # 重操作权重


# 默认配置实例
thresholds = PerformanceThresholds()
load_params = LoadTestParameters()


# 端点性能要求（特定端点的阈值）
ENDPOINT_REQUIREMENTS: Dict[str, Dict[str, float]] = {
    "/api/v1/auth/login": {
        "p95_ms": 500,
        "p99_ms": 1000
    },
    "/api/v1/auth/me": {
        "p95_ms": 100,
        "p99_ms": 200
    },
    "/api/v1/students/[id]/recommendations": {
        "p95_ms": 1000,
        "p99_ms": 2000
    },
    "/api/v1/mistakes/me": {
        "p95_ms": 300,
        "p99_ms": 500
    },
    "/api/v1/reports/generate": {
        "p95_ms": 5000,
        "p99_ms": 10000
    },
    "/health": {
        "p95_ms": 50,
        "p99_ms": 100
    }
}


def get_endpoint_requirement(endpoint: str) -> Dict[str, float]:
    """
    获取端点性能要求

    支持通配符匹配，如 "/api/v1/students/[id]/recommendations"
    """
    # 精确匹配
    if endpoint in ENDPOINT_REQUIREMENTS:
        return ENDPOINT_REQUIREMENTS[endpoint]

    # 模式匹配（处理路径参数）
    pattern_endpoint = endpoint
    for segment in pattern_endpoint.split("/"):
        if segment.startswith("[") and segment.endswith("]"):
            pattern_endpoint = pattern_endpoint.replace(segment, "[id]")

    if pattern_endpoint in ENDPOINT_REQUIREMENTS:
        return ENDPOINT_REQUIREMENTS[pattern_endpoint]

    # 返回默认要求
    return {
        "p95_ms": thresholds.API_P95_RESPONSE_TIME,
        "p99_ms": thresholds.API_P99_RESPONSE_TIME
    }


def check_response_time(endpoint: str, response_time_ms: float) -> tuple[bool, str]:
    """
    检查响应时间是否符合要求

    Returns:
        (是否通过, 描述信息)
    """
    requirements = get_endpoint_requirement(endpoint)

    p95_ok = response_time_ms <= requirements["p95_ms"]
    p99_ok = response_time_ms <= requirements["p99_ms"]

    if not p99_ok:
        return False, f"Response time {response_time_ms:.2f}ms exceeds P99 threshold ({requirements['p99_ms']}ms)"

    if not p95_ok:
        return False, f"Response time {response_time_ms:.2f}ms exceeds P95 threshold ({requirements['p95_ms']}ms)"

    return True, f"Response time {response_time_ms:.2f}ms within acceptable range"
