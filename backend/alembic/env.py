"""
Alembic环境配置
支持异步迁移和自动模型导入
"""
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# 添加项目路径到sys.path
import sys
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# 导入配置和模型
from app.core.config import settings
from app.db.base import Base

# 导入所有模型以确保它们被注册到Base.metadata
from app.models.user import User  # noqa: F401
from app.models.organization import Organization  # noqa: F401
from app.models.student import Student  # noqa: F401
from app.models.teacher import Teacher  # noqa: F401
from app.models.knowledge_graph import KnowledgeGraph  # noqa: F401
from app.models.content import (  # noqa: F401
    Content,
    Vocabulary,
    ContentVocabulary,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 从settings设置数据库URL
# 需要将%转义为%%，因为configparser会解析%符号
database_url = str(settings.DATABASE_URL).replace("%", "%%")
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置目标元数据
target_metadata = Base.metadata

# 其他值可以从配置中获取
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """在'离线'模式下运行迁移。

    这仅用URL配置上下文，而不需要Engine。
    通过跳过Engine创建，我们甚至不需要DBAPI可用。

    对context.execute()的调用会将给定的字符串发出到脚本输出。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """执行迁移的实际函数"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """运行异步迁移"""
    configuration = config.get_section(config.config_ini_section)

    create_async_engine_kwargs = {
        "url": configuration["sqlalchemy.url"],
        "echo": False,
        "poolclass": pool.NullPool,
    }

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        **create_async_engine_kwargs,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在'在线'模式下运行迁移。

    在这种情况下，我们需要创建一个Engine并将连接与上下文关联。
    """
    connectable = config.attributes.get("connection", None)

    if connectable is None:
        # asyncio运行器处理异步迁移
        import asyncio

        asyncio.run(run_async_migrations())
    else:
        # 同步模式（如果有同步连接传递）
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
            )

            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
