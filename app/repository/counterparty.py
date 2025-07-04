# app/repository/counterparty.py
from typing import Any

from loguru import logger
from sqlalchemy import select, and_, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.repository.base import BaseRepository
from app.models.counterparty import Counterparty
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.enums import CounterpartyType
from app.schemas.counterparty import CounterpartyCreate, CounterpartyUpdate


class CounterpartyRepository(
    BaseRepository[Counterparty, CounterpartyCreate, CounterpartyUpdate]
):
    async def get_or_create(
        self,
        session: AsyncSession,
        *,
        name: str,
        account_number: str | None,
        counterparty_type: str,
    ) -> Counterparty:
        """
        根据名称或账号获取或创建对手方。
        """

        # 1. 优先使用账号查询，这是最可靠的唯一标识
        if (
            account_number
            and isinstance(account_number, str)
            and account_number.strip()
        ):
            statement = select(self.model).where(
                self.model.account_number == account_number
            )
        else:
            # 2. 如果没有账号，则查找“同名且账号为空”的记录
            statement = select(self.model).where(
                and_(self.model.name == name, self.model.account_number.is_(None))
            )

        result = await session.scalars(statement)
        existing_counterparty = result.one_or_none()  # 现在这个查询条件能保证结果唯一

        if existing_counterparty:
            # 如果找到了记录，但新传入的分类更准确，就更新它
            # 例如，之前是PERSON，现在通过关键词识别出是MERCHANT，就覆盖掉旧分类。
            if (
                existing_counterparty.counterparty_type != counterparty_type
                and counterparty_type != CounterpartyType.UNKNOWN.value
            ):  # 不用UNKNOWN覆盖已知类型
                logger.info(
                    f"更新对手 '{name}' 的类型: "
                    f"从 {existing_counterparty.counterparty_type} -> {counterparty_type}"
                )
                existing_counterparty.counterparty_type = counterparty_type
                session.add(existing_counterparty)
                await session.flush()
                await session.refresh(existing_counterparty)
            return existing_counterparty

        new_counterparty = self.model(
            name=name,
            account_number=account_number,
            counterparty_type=counterparty_type,
        )
        session.add(new_counterparty)
        try:
            await session.flush()
            await session.refresh(new_counterparty)
            return new_counterparty
        except IntegrityError:
            # 兜底处理，万一在并发情况下还是创建了重复项
            await session.rollback()
            # 再次查询一次，返回已存在的记录
            result = await session.scalars(statement)
            return result.one()

    async def get_summary_by_person_id_grouped_by_name(
        self, session: AsyncSession, *, person_id: int
    ) -> list[dict[str, Any]]:
        """
        获取一个用户所有对手方的资金往来汇总统计，按对手方名称进行分组。
        """
        income_case = case(
            (Transaction.transaction_type == "CREDIT", Transaction.amount), else_=0
        )
        expense_case = case(
            (Transaction.transaction_type == "DEBIT", Transaction.amount), else_=0
        )

        statement = (
            select(
                # 我们只选择需要聚合的字段
                self.model.name,
                func.sum(income_case).label("total_income"),
                func.sum(expense_case).label("total_expense"),
                func.count(Transaction.id).label("transaction_count"),
            )
            .join(Transaction, self.model.id == Transaction.counterparty_id)
            .join(Account, Transaction.account_id == Account.id)
            .where(Account.owner_id == person_id)
            .group_by(self.model.name)  # <-- 核心思路：按名称分组
        )

        result = await session.execute(statement)
        return [row._asdict() for row in result.all()]

    # 暂时弃用，但仍保留代码，以备不时之需
    async def get_summary_by_person_id(
        self, session: AsyncSession, *, person_id: int
    ) -> list[dict[str, Any]]:
        """
        获取一个用户所有对手方的资金往来汇总统计。
        """
        # 使用 case 表达式来分别计算收入和支出
        income_case = case(
            (Transaction.transaction_type == "CREDIT", Transaction.amount), else_=0
        )
        expense_case = case(
            (Transaction.transaction_type == "DEBIT", Transaction.amount), else_=0
        )

        # 构建聚合查询
        statement = (
            select(
                self.model.id,
                self.model.name,
                self.model.account_number,
                self.model.counterparty_type,
                func.sum(income_case).label("total_income"),
                func.sum(expense_case).label("total_expense"),
                func.count(Transaction.id).label("transaction_count"),
            )
            .join(Transaction, self.model.id == Transaction.counterparty_id)
            .join(Account, Transaction.account_id == Account.id)
            .where(Account.owner_id == person_id)
            .group_by(self.model.id)
            .order_by(
                func.sum(func.abs(Transaction.amount)).desc()
            )  # 按总交易绝对值降序
        )

        result = await session.execute(statement)
        # 将结果转换为字典列表，方便上层使用
        return [row._asdict() for row in result.all()]


counterparty_repository = CounterpartyRepository(Counterparty)
