"""
安全模块 - 密码哈希和JWT token管理
提供密码哈希、验证和JWT token生成、解码功能
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# 密码哈希上下文 - 使用argon2算法（兼容Python 3.14）
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希密码是否匹配

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    对密码进行哈希处理

    Args:
        password: 明文密码

    Returns:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str | uuid.UUID,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict[str, Any]] = None
) -> str:
    """
    创建JWT access token

    Args:
        subject: token主体，通常是用户ID
        expires_delta: 过期时间增量，默认使用配置中的ACCESS_TOKEN_EXPIRE_MINUTES
        additional_claims: 额外的声明信息

    Returns:
        str: 编码后的JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: str | uuid.UUID,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建JWT refresh token

    Args:
        subject: token主体，通常是用户ID
        expires_delta: 过期时间增量，默认使用配置中的REFRESH_TOKEN_EXPIRE_DAYS

    Returns:
        str: 编码后的JWT refresh token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """
    解码并验证JWT token

    Args:
        token: JWT token字符串

    Returns:
        dict | None: 解码后的token payload，验证失败返回None
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    验证token并返回用户ID

    Args:
        token: JWT token字符串
        token_type: 期望的token类型 ("access" 或 "refresh")

    Returns:
        Optional[str]: 用户ID，验证失败返回None
    """
    payload = decode_token(token)
    if payload is None:
        return None

    # 检查token类型
    if payload.get("type") != token_type:
        return None

    # 获取用户ID
    user_id: str = payload.get("sub")
    if user_id is None:
        return None

    return user_id


def create_password_reset_token(
    subject: str | uuid.UUID,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建密码重置token

    Args:
        subject: token主体，通常是用户ID
        expires_delta: 过期时间增量，默认1小时

    Returns:
        str: 编码后的JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=1)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "password_reset"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    验证密码重置token并返回用户ID

    Args:
        token: JWT token字符串

    Returns:
        Optional[str]: 用户ID，验证失败返回None
    """
    return verify_token(token, token_type="password_reset")
