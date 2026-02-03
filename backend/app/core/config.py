"""
应用配置
使用 pydantic-settings 管理配置
"""
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # JWT配置
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT密钥，生产环境必须修改"
    )
    JWT_SECRET_KEY: str = Field(
        default="your-jwt-secret-key-change-this",
        description="JWT专用密钥"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS配置
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]
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


# 创建全局配置实例
settings = Settings()
