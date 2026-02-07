"""
应用配置
使用 pydantic-settings 管理配置
"""
import os
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ============== 密钥生成函数 ==============

def generate_secret_key(length: int = 64) -> str:
    """
    生成安全的随机密钥

    Args:
        length: 密钥长度（字节），实际生成字符串长度为 2*length (hex)

    Returns:
        随机密钥字符串
    """
    import secrets
    return secrets.token_hex(length)


def generate_jwt_secret() -> str:
    """
    生成适合 JWT 使用的密钥

    Returns:
        JWT 密钥字符串（64字符 hex = 32字节）
    """
    return generate_secret_key(32)


# ============== 配置类 ==============

class Settings(BaseSettings):
    """应用配置类"""

    # 应用基本信息
    APP_NAME: str = "AI English Teaching Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/english_teaching",
        description="PostgreSQL数据库连接URL"
    )
    DB_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # JWT配置 - 强制从环境变量读取，不提供默认值
    SECRET_KEY: str = Field(
        description="应用主密钥，用于加密敏感数据（如refresh token）"
    )
    JWT_SECRET_KEY: str = Field(
        description="JWT签名密钥，用于生成和验证access token"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS配置
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:58002", "http://localhost:8000"]
    CORS_ALLOW_CREDENTIALS: bool = True

    # AI服务配置
    # 智谱AI (主要AI服务提供商)
    ZHIPUAI_API_KEY: str = Field(
        default="",
        description="智谱AI API密钥"
    )
    ZHIPUAI_MODEL: str = "glm-4.7"
    ZHIPUAI_EMBEDDING_MODEL: str = "embedding-3"
    ZHIPUAI_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    ZHIPUAI_TEMPERATURE: float = 0.7
    ZHIPUAI_MAX_TOKENS: int = 4000
    ZHIPUAI_TOP_P: int = 1
    ZHIPUAI_TOP_K: int = 1
    # 教案生成专用超时配置（秒）
    ZHIPUAI_LESSON_PLAN_TIMEOUT: int = 600

    # OpenAI (备用)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 2000

    # Anthropic Claude (备用)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    ANTHROPIC_TEMPERATURE: float = 0.7
    ANTHROPIC_MAX_TOKENS: int = 2000

    # Qdrant向量数据库配置
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "english_content"
    QDRANT_VECTOR_SIZE: int = 2048  # 智谱embedding-3向量维度

    # AI提供商选择
    AI_PROVIDER: str = "zhipuai"  # zhipuai, openai, anthropic

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    CACHE_TTL: int = 3600

    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # 导出配置
    EXPORT_DIR: Path = Path("exports")
    EXPORT_MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    EXPORT_FILE_RETENTION_DAYS: int = 30
    EXPORT_TASK_RETENTION_DAYS: int = 7
    MAX_CONCURRENT_EXPORTS: int = 5
    EXPORT_TASK_TIMEOUT: int = 300  # 5 minutes

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """解析CORS origins"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @model_validator(mode="after")
    def validate_security_keys(self):
        """验证安全相关密钥长度"""
        MIN_KEY_LENGTH = 32

        # 检查 SECRET_KEY
        if self.SECRET_KEY and len(self.SECRET_KEY) < MIN_KEY_LENGTH:
            raise ValueError(
                f"SECRET_KEY 长度必须至少 {MIN_KEY_LENGTH} 位，"
                f"当前长度: {len(self.SECRET_KEY)}"
            )

        # 检查 JWT_SECRET_KEY
        if self.JWT_SECRET_KEY and len(self.JWT_SECRET_KEY) < MIN_KEY_LENGTH:
            raise ValueError(
                f"JWT_SECRET_KEY 长度必须至少 {MIN_KEY_LENGTH} 位，"
                f"当前长度: {len(self.JWT_SECRET_KEY)}"
            )

        return self


# ============== 懒加载配置实例 ==============
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """
    获取配置单例（懒加载）

    Returns:
        Settings: 应用配置实例
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reload_settings() -> Settings:
    """
    重新加载配置（用于测试等场景）

    Returns:
        Settings: 重新加载的配置实例
    """
    global _settings_instance
    _settings_instance = Settings()
    return _settings_instance


# 为了向后兼容，提供 settings 作为模块属性
# 注意：在生产环境中使用时，如果密钥无效会抛出异常
class _SettingsProxy:
    """配置代理类，支持懒加载并提供清晰的错误信息"""

    def __getattr__(self, name: str):
        try:
            return getattr(get_settings(), name)
        except ValueError as e:
            raise RuntimeError(
                f"配置验证失败: {e}\n\n"
                f"请确保您的 .env 文件中设置了有效的密钥。\n"
                f"生成新密钥的命令:\n"
                f"  SECRET_KEY=$(python -c \"from app.core.config import generate_secret_key; print(generate_secret_key())\")\n"
                f"  JWT_SECRET_KEY=$(python -c \"from app.core.config import generate_jwt_secret; print(generate_jwt_secret())\")\n\n"
                f"或者直接设置环境变量:\n"
                f"  export SECRET_KEY=\"your-secret-key-min-32-chars\"\n"
                f"  export JWT_SECRET_KEY=\"your-jwt-secret-key-min-32-chars\""
            ) from e


settings = _SettingsProxy()
