# app/services/account_service.py
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.account import account_repository
from app.repository.person import person_repository
from app.schemas.account import AccountCreate, AccountUpdate
from app.models.account import Account
from app.core.exceptions import NotFoundException, AlreadyExistsException


class AccountService:
    def __init__(self):
        self.repository = account_repository
        self.person_repo = person_repository

    async def get_account_by_id(
        self, session: AsyncSession, account_id: int
    ) -> Account:
        account = await self.repository.get_with_owner(session, id=account_id)
        if not account:
            raise NotFoundException(detail=f"ID为 {account_id} 的账户不存在。")
        return account

    async def create_account(
        self, session: AsyncSession, *, owner_id: int, account_in: AccountCreate
    ) -> Account:
        """
        为一个已存在的Person创建一个新的Account。
        """
        # 1. 验证 owner_id 对应的 Person 是否存在
        owner = await self.person_repo.get(session, id=owner_id)
        if not owner:
            raise NotFoundException(
                detail=f"ID为 {owner_id} 的用户不存在，无法创建账户。"
            )

        # 2. 验证账号是否已存在
        existing_account = await self.repository.get_by_account_number(
            session, account_number=account_in.account_number
        )
        if existing_account:
            raise AlreadyExistsException(
                detail=f"账号为 '{account_in.account_number}' 的账户已存在。"
            )

        # --- 修正点 ---
        # 3. 直接调用仓库层中为Account定制的、更专业的创建方法
        db_account = await self.repository.create_with_owner(
            session, obj_in=account_in, owner_id=owner_id
        )

        # 4. 为了解决懒加载问题，重新获取并预加载 owner 信息
        refreshed_account = await self.get_account_by_id(
            session, account_id=db_account.id
        )
        return refreshed_account

    async def update_account(
        self, session: AsyncSession, *, account_id: int, account_in: AccountUpdate
    ) -> Account:
        db_account = await self.get_account_by_id(session, account_id)

        if (
            account_in.account_number
            and account_in.account_number != db_account.account_number
        ):
            existing_account = await self.repository.get_by_account_number(
                session, account_number=account_in.account_number
            )
            if existing_account:
                raise AlreadyExistsException(
                    detail=f"账号为 '{account_in.account_number}' 的账户已存在。"
                )

        updated_account = await self.repository.update(
            session, db_obj=db_account, obj_in=account_in
        )
        return await self.get_account_by_id(session, account_id=updated_account.id)

    async def delete_account(self, session: AsyncSession, *, account_id: int) -> None:
        await self.get_account_by_id(session, account_id)
        await self.repository.delete(session, id=account_id)


account_service = AccountService()
