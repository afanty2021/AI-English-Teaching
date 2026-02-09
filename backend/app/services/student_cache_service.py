"""
学生数据缓存服务
提供学生档案、知识图谱等高频访问数据的Redis缓存
"""
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import redis.asyncio as redis

from app.core.config import get_settings


class StudentCacheService:
    """
    学生数据缓存服务

    缓存策略：
    - 学生档案：TTL 5分钟（数据变化不频繁）
    - 知识图谱：TTL 10分钟（图谱更新频率低）
    - 用户信息：TTL 5分钟
    """

    # 缓存 Key 前缀
    _STUDENT_PROFILE_PREFIX = "cache:student:profile:"
    _STUDENT_KG_PREFIX = "cache:student:kg:"
    _USER_PROFILE_PREFIX = "cache:user:profile:"
    _CLASS_STUDENTS_PREFIX = "cache:class:students:"

    # TTL配置（秒）
    _STUDENT_PROFILE_TTL = 5 * 60  # 5分钟
    _STUDENT_KG_TTL = 10 * 60  # 10分钟
    _USER_PROFILE_TTL = 5 * 60  # 5分钟
    _CLASS_STUDENTS_TTL = 2 * 60  # 2分钟（班级学生列表变化较频繁）

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        初始化缓存服务

        Args:
            redis_client: Redis 客户端实例，如果未提供则从配置创建
        """
        self._redis = redis_client
        self._settings = None  # 懒加载配置

    async def _get_redis(self) -> redis.Redis:
        """获取 Redis 客户端（懒加载）"""
        if self._redis is None:
            if self._settings is None:
                self._settings = get_settings()
            self._redis = redis.from_url(
                self._settings.REDIS_URL,
                decode_responses=True,
                max_connections=self._settings.REDIS_MAX_CONNECTIONS
            )
        return self._redis

    def _get_student_profile_key(self, student_id: str) -> str:
        """获取学生档案缓存 Key"""
        return f"{self._STUDENT_PROFILE_PREFIX}{student_id}"

    def _get_student_kg_key(self, student_id: str) -> str:
        """获取学生知识图谱缓存 Key"""
        return f"{self._STUDENT_KG_PREFIX}{student_id}"

    def _get_user_profile_key(self, user_id: str) -> str:
        """获取用户档案缓存 Key"""
        return f"{self._USER_PROFILE_PREFIX}{user_id}"

    def _get_class_students_key(self, class_id: str) -> str:
        """获取班级学生列表缓存 Key"""
        return f"{self._CLASS_STUDENTS_PREFIX}{class_id}"

    async def get_student_profile(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        获取学生档案缓存

        Args:
            student_id: 学生ID

        Returns:
            缓存的学生档案字典，如果未命中返回None
        """
        try:
            redis_client = await self._get_redis()
            key = self._get_student_profile_key(student_id)
            cached = await redis_client.get(key)

            if cached:
                return json.loads(cached)
            return None
        except Exception:
            return None

    async def set_student_profile(
        self,
        student_id: str,
        profile: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置学生档案缓存

        Args:
            student_id: 学生ID
            profile: 学生档案字典
            ttl: 缓存时间（秒），默认使用配置值

        Returns:
            是否设置成功
        """
        try:
            redis_client = await self._get_redis()
            key = self._get_student_profile_key(student_id)
            ttl = ttl or self._STUDENT_PROFILE_TTL

            await redis_client.setex(
                key,
                ttl,
                json.dumps(profile, default=str)
            )
            return True
        except Exception:
            return False

    async def invalidate_student_profile(self, student_id: str) -> bool:
        """
        使学生档案缓存失效

        Args:
            student_id: 学生ID

        Returns:
            是否删除成功
        """
        try:
            redis_client = await self._get_redis()
            key = self._get_student_profile_key(student_id)
            await redis_client.delete(key)
            return True
        except Exception:
            return False

    async def get_student_knowledge_graph(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        获取学生知识图谱缓存

        Args:
            student_id: 学生ID

        Returns:
            缓存的知识图谱字典，如果未命中返回None
        """
        try:
            redis_client = await self._get_redis()
            key = self._get_student_kg_key(student_id)
            cached = await redis_client.get(key)

            if cached:
                return json.loads(cached)
            return None
        except Exception:
            return None

    async def set_student_knowledge_graph(
        self,
        student_id: str,
        knowledge_graph: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置学生知识图谱缓存

        Args:
            student_id: 学生ID
            knowledge_graph: 知识图谱字典
            ttl: 缓存时间（秒），默认使用配置值

        Returns:
            是否设置成功
        """
        try:
            redis_client = await self._get_redis()
            key = self._get_student_kg_key(student_id)
            ttl = ttl or self._STUDENT_KG_TTL

            await redis_client.setex(
                key,
                ttl,
                json.dumps(knowledge_graph, default=str)
            )
            return True
        except Exception:
            return False

    async def invalidate_student_knowledge_graph(self, student_id: str) -> bool:
        """
        使学生知识图谱缓存失效

        Args:
            student_id: 学生ID

        Returns:
            是否删除成功
        """
        try:
            redis_client = await self._get_redis()
            key = self._get_student_kg_key(student_id)
            await redis_client.delete(key)
            return True
        except Exception:
            return False

    async def invalidate_student_all(self, student_id: str) -> bool:
        """
        使学生所有相关缓存失效

        Args:
            student_id: 学生ID

        Returns:
            是否删除成功
        """
        try:
            redis_client = await self._get_redis()
            # 删除学生档案、知识图谱缓存
            keys = [
                self._get_student_profile_key(student_id),
                self._get_student_kg_key(student_id)
            ]
            await redis_client.delete(*keys)
            return True
        except Exception:
            return False

    async def invalidate_class_students(self, class_id: str) -> bool:
        """
        使班级学生列表缓存失效

        Args:
            class_id: 班级ID

        Returns:
            是否删除成功
        """
        try:
            redis_client = await self._get_redis()
            key = self._get_class_students_key(class_id)
            await redis_client.delete(key)
            return True
        except Exception:
            return False

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存服务统计信息

        Returns:
            统计信息字典
        """
        try:
            redis_client = await self._get_redis()
            info = await redis_client.info("stats")

            return {
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                ),
                "connected": True,
            }
        except Exception:
            return {
                "hits": 0,
                "misses": 0,
                "hit_rate": 0,
                "connected": False,
            }

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """计算缓存命中率"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round(hits / total * 100, 2)

    async def close(self):
        """关闭 Redis 连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None


# 单例实例
_student_cache: Optional[StudentCacheService] = None


async def get_student_cache() -> StudentCacheService:
    """
    获取学生缓存服务单例

    Returns:
        StudentCacheService 实例
    """
    global _student_cache
    if _student_cache is None:
        _student_cache = StudentCacheService()
    return _student_cache
