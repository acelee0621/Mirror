# app/repository/transaction.py
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, subqueryload
from typing import Any

from app.repository.base import BaseRepository
from app.models.transaction import Transaction
from app.models.person import Person
from app.models.account import Account
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionRepository(
    BaseRepository[Transaction, TransactionCreate, TransactionUpdate]
):
    async def get_with_details(
        self, session: AsyncSession, *, transaction_id: int
    ) -> Transaction | None:
        statement = (
            select(self.model)
            .where(self.model.id == transaction_id)
            .options(
                selectinload(self.model.account), selectinload(self.model.counterparty)
            )
        )
        result = await session.scalars(statement)
        return result.one_or_none()

    async def get_multi_by_account_id(
        self, session: AsyncSession, *, account_id: int, skip: int = 0, limit: int = 100
    ) -> list[Transaction]:
        statement = (
            select(self.model)
            .where(self.model.account_id == account_id)
            .options(
                selectinload(self.model.account), selectinload(self.model.counterparty)
            )
            .order_by(self.model.transaction_date.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.scalars(statement)
        return list(result.all())

    async def get_multi_by_person_id(
        self, session: AsyncSession, *, person_id: int, skip: int = 0, limit: int = 100
    ) -> list[Transaction]:
        """
        获取一个用户所有账户下的全部交易记录。
        (V2: 使用直接查询，更高效且避免了关联代理的复杂性)
        """
        # 直接从 Transaction 表开始查询，通过 JOIN 关联到 Account 来实现过滤
        statement = (
            select(self.model)
            .join(Account, self.model.account_id == Account.id)
            .where(Account.owner_id == person_id)
            .options(
                # 依然使用预加载来避免 N+1 问题
                selectinload(self.model.account),
                selectinload(self.model.counterparty),
            )
            .order_by(self.model.transaction_date.asc())  # 在数据库层面完成排序
            .offset(skip)  # 在数据库层面完成分页
            .limit(limit)
        )
        result = await session.scalars(statement)
        return list(result.all())

    async def bulk_create(
        self,
        session: AsyncSession,
        *,
        transactions_data: list[dict[str, Any]],
        chunk_size: int = 500,
    ):
        """
        批量插入交易数据，并使用分块处理以避免参数数量限制。
        """
        if not transactions_data:
            return

        # --- 分块处理 ---
        for i in range(0, len(transactions_data), chunk_size):
            chunk = transactions_data[i : i + chunk_size]
            if not chunk:
                continue

            statement = insert(Transaction).values(chunk)
            statement = statement.on_conflict_do_nothing(
                index_elements=["bank_transaction_id"]
            )
            await session.execute(statement)

        # 在所有批次都执行完毕后，统一提交事务
        await session.commit()


# 创建仓库单例
transaction_repository = TransactionRepository(Transaction)
