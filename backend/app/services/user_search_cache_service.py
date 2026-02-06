"""
用户搜索缓存服务

使用Redis缓存热门教师搜索结果，提高搜索性能。
"""
import json
import uuid
from typing import List, Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.models import User, UserRole


class UserSearchCacheService:
    """用户搜索缓存服务"""

    # 缓存键前缀
    SEARCH_KEY_PREFIX = "user_search:"
    HOT_SEARCH_KEY = "user_search:hot_queries"

    # 缓存过期时间（秒）
    CACHE_TTL = 300  # 5分钟
    HOT_QUERY_TTL = 3600  # 1小时

    def _get_search_key(self, query: str, role: Optional[str] = None) -> str:
        """生成搜索缓存键"""
        role_suffix = f":{role}" if role else ""
        return f"{self.SEARCH_KEY_PREFIX}{query}{role_suffix}"

    async def get_cached_results(
        self,
        query: str,
        role: Optional[str] = None
    ) -> Optional[List[dict]]:
        """
        从缓存获取搜索结果

        Args:
            query: 搜索关键词
            role: 角色筛选

        Returns:
            缓存的用户列表，如果不存在则返回None
        """
        try:
            redis = get_redis()
            key = self._get_search_key(query, role)
            cached = await redis.get(key)

            if cached:
                return json.loads(cached)
            return None

        except Exception as e:
            print(f"Error getting cached results: {e}")
            return None

    async def cache_search_results(
        self,
        query: str,
        users: List[dict],
        role: Optional[str] = None
    ) -> None:
        """
        缓存搜索结果

        Args:
            query: 搜索关键词
            users: 用户列表
            role: 角色筛选
        """
        try:
            redis = get_redis()
            key = self._get_search_key(query, role)
            await redis.setex(
                key,
                self.CACHE_TTL,
                json.dumps(users)
            )

            # 记录热门搜索
            await self._record_hot_query(query)

        except Exception as e:
            print(f"Error caching search results: {e}")

    async def search_and_cache(
        self,
        db: AsyncSession,
        query: str,
        role: Optional[UserRole] = None,
        limit: int = 20
    ) -> List[dict]:
        """
        执行搜索并缓存结果

        Args:
            db: 数据库会话
            query: 搜索关键词
            role: 角色筛选
            limit: 返回数量限制

        Returns:
            用户列表
        """
        # 尝试从缓存获取
        cached = await self.get_cached_results(query, role.value if role else None)
        if cached is not None:
            return cached

        # 缓存未命中，执行搜索
        search_pattern = f"%{query}%"
        conditions = [
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.full_name.ilike(search_pattern) if User.full_name is not None else False
            )
        ]

        if role:
            conditions.append(User.role == role.value)

        query_obj = select(User).where(*conditions).limit(limit)
        result = await db.execute(query_obj)
        users = result.scalars().all()

        # 转换为字典列表
        users_data = [
            {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
            }
            for user in users
        ]

        # 缓存结果
        await self.cache_search_results(
            query,
            users_data,
            role.value if role else None
        )

        return users_data

    async def _record_hot_query(self, query: str) -> None:
        """
        记录热门搜索查询

        Args:
            query: 搜索关键词
        """
        try:
            redis = get_redis()
            # 使用有序集合记录热门搜索
            await redis.zincrby(self.HOT_SEARCH_KEY, 1, query)
            # 设置过期时间
            await redis.expire(self.HOT_SEARCH_KEY, self.HOT_QUERY_TTL)
        except Exception as e:
            print(f"Error recording hot query: {e}")

    async def get_hot_queries(self, limit: int = 10) -> List[str]:
        """
        获取热门搜索查询

        Args:
            limit: 返回数量限制

        Returns:
            热门搜索查询列表
        """
        try:
            redis = get_redis()
            # 获取搜索次数最多的查询
            results = await redis.zrevrange(
                self.HOT_SEARCH_KEY,
                0,
                limit - 1,
                withscores=True
            )

            return [query for query, _ in results] if results else []

        except Exception as e:
            print(f"Error getting hot queries: {e}")
            return []

    async def invalidate_cache(self, user_id: uuid.UUID) -> None:
        """
        使用户数据变更时失效相关缓存

        Args:
            user_id: 用户ID
        """
        try:
            redis = get_redis()
            # 查找所有包含该用户ID的缓存键
            # 由于Redis没有直接的模式匹配删除，我们记录用户特定的缓存
            # 这里简化处理，实际可以使用Redis的SCAN命令
            pass
        except Exception as e:
            print(f"Error invalidating cache: {e}")


# 全局单例
_user_search_cache_service: Optional[UserSearchCacheService] = None


def get_user_search_cache_service() -> UserSearchCacheService:
    """获取用户搜索缓存服务单例"""
    global _user_search_cache_service
    if _user_search_cache_service is None:
        _user_search_cache_service = UserSearchCacheService()
    return _user_search_cache_service
