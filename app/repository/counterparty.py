# app/repository/counterparty.py
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.repository.base import BaseRepository
from app.models.counterparty import Counterparty
from app.schemas.counterparty import CounterpartyCreate, CounterpartyUpdate


class CounterpartyRepository(
    BaseRepository[Counterparty, CounterpartyCreate, CounterpartyUpdate]
):
    async def get_or_create(
        self, session: AsyncSession, *, name: str, account_number: str | None
    ) -> Counterparty:
        """
        根据名称或账号获取或创建对手方。
        这个新版本能正确处理同名但不同账号，或同名但无账号的情况。
        """
        # --- 修正点：重构查询逻辑 ---

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
            #    这能唯一确定一个“商户”或“无账号的个人”
            statement = select(self.model).where(
                and_(self.model.name == name, self.model.account_number.is_(None))
            )

        result = await session.scalars(statement)
        existing_counterparty = result.one_or_none()  # 现在这个查询条件能保证结果唯一

        if existing_counterparty:
            return existing_counterparty

        # 3. 如果以上两种情况都找不到，则说明这是一个全新的对手方，创建它
        counterparty_type = "PERSON" if account_number else "MERCHANT"

        new_counterparty = self.model(
            name=name,
            account_number=account_number,
            counterparty_type=counterparty_type,
        )
        session.add(new_counterparty)
        try:
            await session.commit()
            await session.refresh(new_counterparty)
            return new_counterparty
        except IntegrityError:
            # 兜底处理，万一在并发情况下还是创建了重复项
            await session.rollback()
            # 再次查询一次，返回已存在的记录
            result = await session.scalars(statement)
            return result.one()


counterparty_repository = CounterpartyRepository(Counterparty)
