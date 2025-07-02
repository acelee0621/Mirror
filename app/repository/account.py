# app/repository/account.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.repository.base import BaseRepository
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate
from app.core.exceptions import AlreadyExistsException


class AccountRepository(BaseRepository[Account, AccountCreate, AccountUpdate]):
    """
    Account 模型的仓库层。
    """

    async def create_with_owner(
        self, session: AsyncSession, *, obj_in: AccountCreate, owner_id: int
    ) -> Account:
        """
        创建一个新的Account记录，并将其与一个已存在的Person关联。
        这是为Account模型定制的创建方法。
        """
        # 将 Pydantic 模型转换为字典
        obj_in_data = obj_in.model_dump()
        # 创建 SQLAlchemy 模型实例，并手动添加 owner_id
        db_obj = self.model(**obj_in_data, owner_id=owner_id)

        session.add(db_obj)
        try:
            await session.commit()
            await session.refresh(db_obj)
            return db_obj
        except IntegrityError:
            await session.rollback()
            raise AlreadyExistsException(
                detail=f"账号 '{obj_in.account_number}' 已存在。"
            )

    async def get_by_account_number(
        self, session: AsyncSession, *, account_number: str
    ) -> Account | None:
        """
        根据账号查询账户，用于防止创建重复账号。
        """
        statement = select(self.model).where(
            self.model.account_number == account_number
        )
        result = await session.scalars(statement)
        return result.one_or_none()

    async def get_with_owner(self, session: AsyncSession, id: int) -> Account | None:
        """
        获取账户信息，并预加载其所有者(owner)信息。
        """
        statement = (
            select(self.model)
            .where(self.model.id == id)
            .options(selectinload(self.model.owner))
        )
        result = await session.scalars(statement)
        return result.one_or_none()

    async def get_with_files(self, session: AsyncSession, id: int) -> Account | None:
        """
        获取一个账户，并预先加载其关联的 files 集合。
        """
        statement = (
            select(self.model)
            .where(self.model.id == id)
            .options(selectinload(self.model.files))  # <--- 核心：在这里指定预加载
        )
        result = await session.scalars(statement)
        return result.one_or_none()


# 创建仓库的单例
account_repository = AccountRepository(Account)
