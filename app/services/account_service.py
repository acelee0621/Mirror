# app/services/account_service.py
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.account import account_repository
from app.repository.person import person_repository
from app.schemas.account import AccountCreate, AccountUpdate
from app.models.account import Account
from app.core.exceptions import NotFoundException, AlreadyExistsException
from app.services.file_service import file_service


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
        # 1. 预加载获取账户对象
        account_to_delete = await self.repository.get_with_files(session, id=account_id)
        if not account_to_delete:
            raise NotFoundException(detail=f"ID为 {account_id} 的账户不存在。")

        # 2. 循环调用delete_file方法
        # 注意：这里我们倒序遍历，只是一个好习惯，非必需
        for file_meta in reversed(account_to_delete.files):
            logger.info(
                f"准备删除账户 {account_id} 的关联文件: {file_meta.filename} (ID: {file_meta.id})"
            )
            # 这个调用不会commit
            await file_service.delete_file(session, file_id=file_meta.id)

        # 3. 删除账户本身（这会级联删除所有Transaction）
        logger.info(f"准备删除账户 {account_id} 及其所有交易记录...")
        await self.repository.delete_obj(session, db_obj=account_to_delete)

        # 4. 所有操作都已加入session，在最后进行一次总提交！
        await session.commit()
        logger.success(f"账户 {account_id} 已被彻底删除。")


account_service = AccountService()
