# app/services/counterparty_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.repository.counterparty import counterparty_repository
from app.models.counterparty import Counterparty
from app.schemas.counterparty import CounterpartySummary, CounterpartyAnalysisSummary
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

    async def get_analysis_summary_by_person_id(
        self, session: AsyncSession, *, person_id: int
    ) -> List[CounterpartyAnalysisSummary]:
        """获取按名称聚合的对手方分析汇总"""
        summary_data = await self.repository.get_summary_by_person_id_grouped_by_name(
            session, person_id=person_id
        )
        return [CounterpartyAnalysisSummary.model_validate(row) for row in summary_data]

    # 暂时弃用
    async def get_summary_by_person_id(
        self, session: AsyncSession, *, person_id: int
    ) -> List[CounterpartySummary]:
        """
        获取一个用户所有对手方的资金往来汇总统计。
        """

        summary_data = await self.repository.get_summary_by_person_id(
            session, person_id=person_id
        )

        # 将字典列表转换为 Pydantic 模型对象列表，以确保数据格式的规范性
        return [CounterpartySummary.model_validate(row) for row in summary_data]


# 创建服务单例
counterparty_service = CounterpartyService()
