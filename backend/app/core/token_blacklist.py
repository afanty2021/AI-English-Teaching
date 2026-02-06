"""
Token 黑名单管理
使用 Redis 存储已撤销的 JWT Token，支持单 Token 撤销和用户级 Token 撤销
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import redis.asyncio as redis

from app.core.config import get_settings


class TokenBlacklist:
    """
    Token 黑名单管理器

    功能：
    - 将已注销的 Token 加入黑名单
    - 检查 Token 是否已被撤销
    - 支持用户级 Token 撤销（密码修改等场景）
    - 使用 Redis 存储，支持过期自动清理
    """

    # Redis Key 前缀
    _TOKEN_BLACKLIST_PREFIX = "token:blacklist:"
    _USER_TOKEN_VERSION_PREFIX = "token:version:user:"
    _TOKEN_REFRESH_VERSION_PREFIX = "token:version:refresh:"

    # Token 黑名单默认过期时间（7天）
    _DEFAULT_TTL = 7 * 24 * 60 * 60  # 7 days in seconds

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        初始化 Token 黑名单管理器

        Args:
            redis_client: Redis 客户端实例，如果未提供则从配置创建
        """
        self._redis = redis_client
        self._settings = None  # 懒加载配置

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

    def _get_blacklist_key(self, jti: str) -> str:
        """获取 Token 黑名单的 Redis Key"""
        return f"{self._TOKEN_BLACKLIST_PREFIX}{jti}"

    def _get_user_version_key(self, user_id: str) -> str:
        """获取用户 Token 版本的 Redis Key"""
        return f"{self._USER_TOKEN_VERSION_PREFIX}{user_id}"

    def _get_refresh_version_key(self, user_id: str) -> str:
        """获取用户 Refresh Token 版本的 Redis Key"""
        return f"{self._TOKEN_REFRESH_VERSION_PREFIX}{user_id}"

    async def add_to_blacklist(
        self,
        jti: str,
        user_id: str,
        reason: str = "logout",
        expires_in: Optional[int] = None
    ) -> bool:
        """
        将 Token 加入黑名单

        Args:
            jti: Token 的 JWT ID（唯一标识）
            user_id: 用户 ID
            reason: 撤销原因 ("logout", "password_change", "security", etc.)
            expires_in: 过期时间（秒），默认使用配置中的值

        Returns:
            bool: 是否成功添加
        """
        redis_client = await self._get_redis()

        ttl = expires_in or self._DEFAULT_TTL

        # 获取 Token 的过期时间
        # 注意：实际过期时间应该基于 Token 的 exp claim
        # 这里使用配置的 TTL 作为兜底

        key = self._get_blacklist_key(jti)

        data = {
            "user_id": str(user_id),
            "reason": reason,
            "revoked_at": datetime.now(timezone.utc).isoformat(),
            "jti": jti
        }

        await redis_client.hset(key, mapping=data)
        await redis_client.expire(key, ttl)

        return True

    async def is_revoked(self, jti: str) -> bool:
        """
        检查 Token 是否已被撤销

        Args:
            jti: Token 的 JWT ID

        Returns:
            bool: Token 是否在黑名单中
        """
        redis_client = await self._get_redis()
        key = self._get_blacklist_key(jti)
        return await redis_client.exists(key) > 0

    async def revoke_by_jti(self, jti: str, reason: str = "logout") -> bool:
        """
        通过 JTI 撤销 Token

        Args:
            jti: Token 的 JWT ID
            reason: 撤销原因

        Returns:
            bool: 是否成功撤销
        """
        if await self.is_revoked(jti):
            return True  # 已经在黑名单中

        # 需要获取 user_id，这里简化处理，实际应该从 Token 中解析
        # 由于是主动撤销，通常是在已知 user_id 的情况下调用
        return False  # 需要 user_id 参数

    async def revoke_user_tokens(
        self,
        user_id: str,
        reason: str = "password_change",
        current_jti: Optional[str] = None
    ) -> int:
        """
        撤销用户的所有 Token（用于密码修改等安全场景）

        实现方式：
        1. 增加用户的 token_version
        2. 之后的所有 Token 验证时检查 version

        Args:
            user_id: 用户 ID
            reason: 撤销原因
            current_jti: 当前要撤销的 Token JTI（可选，如果提供则加入黑名单）

        Returns:
            int: 影响的 Token 数量
        """
        redis_client = await self._get_redis()
        version_key = self._get_user_version_key(user_id)

        # 生成新的版本号
        new_version = str(uuid.uuid4())

        # 存储新版本
        await redis_client.set(version_key, new_version, ex=self._DEFAULT_TTL)

        # 如果提供了当前 JTI，也加入黑名单
        if current_jti:
            await self.add_to_blacklist(current_jti, user_id, reason)

        return 1

    async def get_user_token_version(self, user_id: str) -> Optional[str]:
        """
        获取用户的当前 Token 版本

        Args:
            user_id: 用户 ID

        Returns:
            str: 版本号，如果不存在返回 None
        """
        redis_client = await self._get_redis()
        version_key = self._get_user_version_key(user_id)
        return await redis_client.get(version_key)

    async def check_token_version(
        self,
        user_id: str,
        token_version: str
    ) -> bool:
        """
        检查 Token 版本是否匹配

        Args:
            user_id: 用户 ID
            token_version: Token 中的版本号

        Returns:
            bool: 版本是否匹配（True 表示 Token 有效）
        """
        current_version = await self.get_user_token_version(user_id)
        if current_version is None:
            return True  # 没有版本记录，表示 Token 有效

        return current_version == token_version

    async def revoke_refresh_token(
        self,
        user_id: str,
        reason: str = "logout"
    ) -> bool:
        """
        撤销用户的 Refresh Token（用于登出场景）

        Args:
            user_id: 用户 ID
            reason: 撤销原因

        Returns:
            bool: 是否成功撤销
        """
        redis_client = await self._get_redis()
        version_key = self._get_refresh_version_key(user_id)

        # 生成新的版本号
        new_version = str(uuid.uuid4())

        await redis_client.set(version_key, new_version, ex=self._DEFAULT_TTL)

        return True

    async def get_refresh_token_version(self, user_id: str) -> Optional[str]:
        """获取用户的 Refresh Token 版本"""
        redis_client = await self._get_redis()
        version_key = self._get_refresh_version_key(user_id)
        return await redis_client.get(version_key)

    async def close(self):
        """关闭 Redis 连接"""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None


# 创建全局单例
_token_blacklist: Optional[TokenBlacklist] = None


def get_token_blacklist() -> TokenBlacklist:
    """
    获取 Token 黑名单单例

    Returns:
        TokenBlacklist: Token 黑名单管理器实例
    """
    global _token_blacklist
    if _token_blacklist is None:
        _token_blacklist = TokenBlacklist()
    return _token_blacklist


async def init_token_blacklist() -> TokenBlacklist:
    """
    初始化 Token 黑名单（用于应用启动时）

    Returns:
        TokenBlacklist: 初始化的 Token 黑名单实例
    """
    global _token_blacklist
    _token_blacklist = TokenBlacklist()
    return _token_blacklist


async def shutdown_token_blacklist():
    """关闭 Token 黑名单（用于应用关闭时）"""
    global _token_blacklist
    if _token_blacklist is not None:
        await _token_blacklist.close()
        _token_blacklist = None
