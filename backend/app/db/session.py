"""
数据库会话管理
提供便捷的数据库会话操作工具
"""
from typing import Any, AsyncGenerator, Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.base import Base, engine

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话 (FastAPI依赖注入)

    Yields:
        AsyncSession: 数据库会话

    Example:
        ```python
        @app.get("/users/{user_id}")
        async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
            user = await crud_user.get(db, user_id)
            return user
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """CRUD基础类，提供通用的数据库操作"""

    def __init__(self, model: Type[ModelType]):
        """
        初始化CRUD对象

        Args:
            model: SQLAlchemy模型类
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        根据ID获取单条记录

        Args:
            db: 数据库会话
            id: 记录ID

        Returns:
            模型实例或None
        """
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        获取多条记录

        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            模型实例列表
        """
        result = await db.execute(
            select(self.model).offset(skip).limit(limit).order_by(self.model.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        创建新记录

        Args:
            db: 数据库会话
            obj_in: 创建数据Schema

        Returns:
            创建的模型实例
        """
        obj_in_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> ModelType:
        """
        更新记录

        Args:
            db: 数据库会话
            db_obj: 数据库模型实例
            obj_in: 更新数据Schema或字典

        Returns:
            更新后的模型实例
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """
        删除记录

        Args:
            db: 数据库会话
            id: 记录ID

        Returns:
            被删除的模型实例
        """
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def count(self, db: AsyncSession) -> int:
        """
        统计记录总数

        Args:
            db: 数据库会话

        Returns:
            记录总数
        """
        from sqlalchemy import func

        result = await db.execute(select(func.count()).select_from(self.model))
        return result.scalar()
