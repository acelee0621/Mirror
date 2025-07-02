# app/services/counterparty_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.repository.counterparty import counterparty_repository
from app.models.counterparty import Counterparty
from app.core.exceptions import NotFoundException


class CounterpartyService:
    def __init__(self):
        self.repository = counterparty_repository

    async def get_all_counterparties(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Counterparty]:
        """获取所有交易对手方列表"""
        return await self.repository.get_multi(
            session, skip=skip, limit=limit, order_by=["name_asc"]
        )

    async def get_counterparty_by_id(
        self, session: AsyncSession, counterparty_id: int
    ) -> Counterparty:
        """通过ID获取单个交易对手方"""
        counterparty = await self.repository.get(session, id=counterparty_id)
        if not counterparty:
            raise NotFoundException(detail=f"ID为 {counterparty_id} 的交易对手不存在。")
        return counterparty


# 创建服务单例
counterparty_service = CounterpartyService()
