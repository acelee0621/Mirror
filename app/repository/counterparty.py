# app/repository/counterparty.py
from loguru import logger
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.repository.base import BaseRepository
from app.models.counterparty import Counterparty
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
                await session.commit()
                await session.refresh(existing_counterparty)
            return existing_counterparty

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
