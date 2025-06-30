# app/repository/base.py
from typing import Any, Generic, Type, TypeVar, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc, desc
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

# 导入你的数据库模型基类
from app.core.database import Base
from app.core.exceptions import AlreadyExistsException

# --- 1. 定义泛型类型 ---
# ModelType 用于表示任何 SQLAlchemy 的模型类 (如 Transaction, Account)
ModelType = TypeVar("ModelType", bound=Base)
# CreateSchemaType 和 UpdateSchemaType 用于表示 Pydantic 的模型
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    一个包含通用 CRUD 操作的、可复用的仓库基类。

    这个基类利用 Python 的泛型，使得所有子类仓库都能自动获得
    类型安全的基础数据操作方法。

    参数:
    - `ModelType`: SQLAlchemy 模型类。
    - `CreateSchemaType`: 用于创建记录的 Pydantic 模型。
    - `UpdateSchemaType`: 用于更新记录的 Pydantic 模型。
    """

    def __init__(self, model: Type[ModelType]):
        """
        初始化仓库。

        参数:
            model: 与此仓库关联的 SQLAlchemy 模型类。
        """
        self.model = model

    async def get(self, session: AsyncSession, id: Any) -> ModelType | None:
        """
        根据 ID 获取单个记录。

        参数:
            session: 数据库会话。
            id: 记录的主键 ID。

        返回:
            找到的 SQLAlchemy 模型对象，如果未找到则返回 None。
        """
        # session.get 是获取主键对象的最高效方式
        return await session.get(self.model, id)

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: List[str] | None = None,
    ) -> List[ModelType]:
        """
        获取多个记录（支持分页）。

        参数:
            session: 数据库会话。
            skip: 跳过的记录数。
            limit: 返回的最大记录数。
            order_by: 排序规则列表, e.g., ["name_asc", "created_at_desc"].

        返回:
            SQLAlchemy 模型对象的列表。
        """
        statement = select(self.model)
        # 应用排序逻辑
        if order_by:
            for ob in order_by:
                field, direction = ob.rsplit("_", 1)
                if hasattr(self.model, field):
                    column = getattr(self.model, field)
                    if direction == "desc":
                        statement = statement.order_by(desc(column))
                    else:
                        statement = statement.order_by(asc(column))
        
        statement = statement.offset(skip).limit(limit)
        result = await session.scalars(statement)
        # 将 .all() 返回的 Sequence 显式转换为 list，以匹配类型注解
        return list(result.all())

    async def create(
        self, session: AsyncSession, *, obj_in: CreateSchemaType
    ) -> ModelType:
        """
        创建一个新的记录。

        参数:
            session: 数据库会话。
            obj_in: 包含新记录数据的 Pydantic 模型。

        返回:
            新创建的 SQLAlchemy 模型对象。
        """
        # 将 Pydantic 模型转换为字典
        obj_in_data = obj_in.model_dump()
        # 使用字典解包创建 SQLAlchemy 模型实例
        db_obj = self.model(**obj_in_data)

        session.add(db_obj)
        try:
            await session.commit()
            await session.refresh(db_obj)
            return db_obj
        except IntegrityError:
            await session.rollback()
            # 抛出自定义的业务异常，而不是直接暴露数据库错误
            raise AlreadyExistsException(
                detail=f"{self.model.__name__} with these unique properties already exists."
            )

    async def update(
        self,
        session: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        """
        更新一个已存在的记录。

        参数:
            session: 数据库会话。
            db_obj: 从数据库中获取的、需要更新的 SQLAlchemy 模型对象。
            obj_in: 包含更新数据的 Pydantic 模型或字典。

        返回:
            更新后的 SQLAlchemy 模型对象。
        """
        # 获取原始对象的字典表示
        obj_data = db_obj.__dict__

        # 将 Pydantic 更新模型转换为字典
        if isinstance(obj_in, BaseModel):
            # exclude_unset=True 表示只获取被显式设置了值的字段，用于支持局部更新(PATCH)
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = obj_in

        # 遍历更新数据，并更新原始对象的属性
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def delete(self, session: AsyncSession, *, id: Any) -> None:
        """
        根据 ID 删除一个记录。

        参数:
            session: 数据库会话。
            id: 记录的主键 ID。

        返回:
            成功删除后不返回任何内容。
        """
        obj = await self.get(session, id)
        if obj:
            await session.delete(obj)
            await session.commit()
