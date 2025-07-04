# app/services/transaction_service.py
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.transaction import transaction_repository
from app.models.transaction import Transaction
from app.core.exceptions import NotFoundException


class TransactionService:
    def __init__(self):
        self.repository = transaction_repository

    async def get_transactions_for_account(
        self, session: AsyncSession, *, account_id: int, skip: int = 0, limit: int = 100
    ) -> list[Transaction]:
        """获取指定账户下的所有交易记录"""
        return await self.repository.get_multi_by_account_id(
            session, account_id=account_id, skip=skip, limit=limit
        )

    async def get_transactions_for_person(
        self, session: AsyncSession, *, person_id: int, skip: int = 0, limit: int = 100
    ) -> list[Transaction]:
        """
        获取一个用户所有账户下的全部交易记录。
        """
        return await self.repository.get_multi_by_person_id(
            session, person_id=person_id, skip=skip, limit=limit
        )

    async def get_transaction_by_id(
        self, session: AsyncSession, transaction_id: int
    ) -> Transaction:
        """通过ID获取单笔交易"""

        transaction = await self.repository.get_with_details(
            session, transaction_id=transaction_id
        )

        if not transaction:
            raise NotFoundException(detail=f"ID为 {transaction_id} 的交易不存在。")
        return transaction


# 创建服务单例
transaction_service = TransactionService()
