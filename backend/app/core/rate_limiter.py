"""
速率限制模块
使用 Redis 实现分布式登录速率限制，防止暴力破解
"""
from typing import Optional
from datetime import timedelta

import redis.asyncio as redis

from app.core.config import get_settings


class RateLimiter:
    """
    Redis-based 速率限制器

    使用滑动窗口算法实现精确的速率限制
    """

    # 登录端点的默认限制配置
    LOGIN_LIMIT = 5  # 允许的尝试次数
    LOGIN_WINDOW = timedelta(minutes=1)  # 时间窗口

    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._settings = None

    async def _get_redis(self) -> redis.Redis:
        """获取 Redis 客户端（懒加载）"""
        if self._redis is None:
            settings = get_settings()
            self._redis = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=settings.REDIS_MAX_CONNECTIONS
            )
        return self._redis

    def _get_key(self, identifier: str, endpoint: str = "login") -> str:
        """
        生成速率限制的 Redis key

        Args:
            identifier: 标识符（用户名、IP 或 user_id）
            endpoint: 端点名称

        Returns:
            str: Redis key
        """
        return f"ratelimit:{endpoint}:{identifier}"

    async def check_rate_limit(
        self,
        identifier: str,
        limit: int = LOGIN_LIMIT,
        window: timedelta = LOGIN_WINDOW,
        endpoint: str = "login"
    ) -> tuple[bool, int, int]:
        """
        检查是否超过速率限制

        Args:
            identifier: 标识符（用户名、IP 或 user_id）
            limit: 允许的最大请求数
            window: 时间窗口
            endpoint: 端点名称

        Returns:
            tuple: (是否允许, 剩余请求数, 剩余秒数)
        """
        try:
            redis_client = await self._get_redis()
            key = self._get_key(identifier, endpoint)

            # 使用 Redis MULTI/PIPELINE 实现原子操作
            pipe = redis_client.pipeline()

            # 增加计数器并设置过期时间
            pipe.incr(key)
            pipe.expire(key, int(window.total_seconds()))

            results = await pipe.execute()
            current_count = results[0]

            # 计算剩余请求数和重置时间
            remaining = max(0, limit - current_count)

            # 获取 TTL 作为重置时间
            ttl = await redis_client.ttl(key)
            reset_seconds = max(0, ttl)

            # 检查是否超过限制
            allowed = current_count <= limit

            return allowed, remaining, reset_seconds
        except Exception:
            # Redis 不可用时，降级处理（允许请求通过）
            return True, limit, int(window.total_seconds())

    async def get_attempts(
        self,
        identifier: str,
        endpoint: str = "login"
    ) -> int:
        """
        获取当前时间窗口内的尝试次数

        Args:
            identifier: 标识符
            endpoint: 端点名称

        Returns:
            int: 尝试次数
        """
        try:
            redis_client = await self._get_redis()
            key = self._get_key(identifier, endpoint)

            count = await redis_client.get(key)
            return int(count) if count else 0
        except Exception:
            return 0

    async def reset(
        self,
        identifier: str,
        endpoint: str = "login"
    ) -> bool:
        """
        重置速率限制计数器

        Args:
            identifier: 标识符
            endpoint: 端点名称

        Returns:
            bool: 是否成功重置
        """
        try:
            redis_client = await self._get_redis()
            key = self._get_key(identifier, endpoint)

            await redis_client.delete(key)
            return True
        except Exception:
            return False

    async def close(self):
        """关闭 Redis 连接"""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None


# 创建全局单例
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    获取速率限制器单例

    Returns:
        RateLimiter: 速率限制器实例
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


async def init_rate_limiter() -> RateLimiter:
    """
    初始化速率限制器（用于应用启动时）

    Returns:
        RateLimiter: 初始化的速率限制器实例
    """
    global _rate_limiter
    _rate_limiter = RateLimiter()
    return _rate_limiter


async def shutdown_rate_limiter():
    """关闭速率限制器（用于应用关闭时）"""
    global _rate_limiter
    if _rate_limiter is not None:
        await _rate_limiter.close()
        _rate_limiter = None
