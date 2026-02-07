"""
Redis 连接管理模块

提供全局 Redis 连接管理，使用连接池模式提高性能。
"""
from functools import lru_cache
from typing import Optional

import redis
from redis import asyncio as aioredis

from app.core.config import get_settings


# ============== 同步 Redis 客户端 ==============

@lru_cache
def get_redis(
    decode_responses: bool = True,
    max_connections: Optional[int] = None,
) -> redis.Redis:
    """
    获取同步 Redis 客户端（用于非异步代码）

    Args:
        decode_responses: 是否解码响应为字符串
        max_connections: 最大连接数，None 则使用配置默认值

    Returns:
        Redis 客户端实例

    Example:
        >>> redis_client = get_redis()
        >>> redis_client.set("key", "value")
        >>> value = redis_client.get("key")
    """
    settings = get_settings()
    if max_connections is None:
        max_connections = settings.REDIS_MAX_CONNECTIONS

    return redis.from_url(
        settings.REDIS_URL,
        decode_responses=decode_responses,
        max_connections=max_connections,
    )


# ============== 异步 Redis 客户端 ==============

@lru_cache
async def get_async_redis(
    decode_responses: bool = True,
    max_connections: Optional[int] = None,
) -> aioredis.Redis:
    """
    获取异步 Redis 客户端（用于异步代码）

    Args:
        decode_responses: 是否解码响应为字符串
        max_connections: 最大连接池大小，None 则使用配置默认值

    Returns:
        异步 Redis 客户端实例

    Example:
        >>> redis_client = await get_async_redis()
        >>> await redis_client.set("key", "value")
        >>> value = await redis_client.get("key")
        >>> await redis_client.close()
    """
    settings = get_settings()
    if max_connections is None:
        max_connections = settings.REDIS_MAX_CONNECTIONS

    return await aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=decode_responses,
        max_connections=max_connections,
    )


# ============== FastAPI 依赖注入 ==============

async def get_redis_dependency() -> aioredis.Redis:
    """
    FastAPI 依赖注入函数：获取异步 Redis 客户端

    使用方式:
        >>> from fastapi import Depends
        >>> from app.core.redis import get_redis_dependency
        >>>
        >>> @app.get("/test")
        >>> async def test_route(redis = Depends(get_redis_dependency)):
        >>>     return await redis.ping()

    Returns:
        异步 Redis 客户端实例
    """
    return await get_async_redis()


# ============== 连接池管理 ==============

_redis_pool: Optional[redis.ConnectionPool] = None


def get_redis_pool() -> redis.ConnectionPool:
    """
    获取 Redis 连接池

    使用连接池可以复用连接，提高性能。

    Returns:
        Redis 连接池实例
    """
    global _redis_pool
    if _redis_pool is None:
        settings = get_settings()
        _redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
        )
    return _redis_pool


def close_redis_pool():
    """关闭 Redis 连接池"""
    global _redis_pool
    if _redis_pool is not None:
        _redis_pool.disconnect()
        _redis_pool = None


# ============== 辅助函数 ==============

async def ping_redis() -> bool:
    """
    检查 Redis 连接是否正常

    Returns:
        True 如果连接正常，False 否则
    """
    try:
        client = await get_async_redis()
        return await client.ping() is True
    except Exception:
        return False


def get_redis_info() -> dict:
    """
    获取 Redis 配置信息

    Returns:
        包含 Redis 配置的字典
    """
    settings = get_settings()
    return {
        "url": settings.REDIS_URL,
        "max_connections": settings.REDIS_MAX_CONNECTIONS,
        "cache_ttl": settings.CACHE_TTL,
    }
