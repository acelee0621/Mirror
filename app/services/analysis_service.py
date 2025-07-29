# app/services/analysis_service.py
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.services.rule_based_analysis import find_u_turn_transactions
from app.repository.transaction import transaction_repository
from app.repository.counterparty import counterparty_repository
from app.models.transaction import Transaction
from app.schemas.counterparty import CounterpartyAnalysisSummary


class AnalysisService:
    def __init__(self):
        self.transaction_repo = transaction_repository
        self.counterparty_repo = counterparty_repository

    async def detect_u_turn_transactions(
        self,
        session: AsyncSession,
        *,
        person_id: int,
        amount_threshold: float,
        time_window_hours: int,
        amount_tolerance: float,
    ) -> list[dict[str, Any]]:
        """
        检测一个用户的“快进快出”交易。
        (V2: 返回包含完整ORM对象的事件列表)
        """
        all_transactions = await self.transaction_repo.get_multi_by_person_id(
            session, person_id=person_id, skip=0, limit=100000
        )

        if len(all_transactions) < 2:
            return []

        # 将ORM对象列表转换为DataFrame，仅包含算法需要的列
        transactions_data = [
            {
                "id": t.id,
                "transaction_date": t.transaction_date,
                "transaction_type": t.transaction_type,
                "amount": t.amount,
            }
            for t in all_transactions
        ]
        df = pd.DataFrame(transactions_data)

        # 1. 调用算法，获取包含ID的事件列表
        u_turn_events_with_ids = find_u_turn_transactions(
            transactions_df=df,
            amount_threshold=amount_threshold,
            time_window_hours=time_window_hours,
            amount_tolerance=amount_tolerance,
        )

        # 2. 根据ID，从原始的ORM对象列表中构建包含完整对象的事件列表
        #    我们使用一个字典来快速查找ID对应的ORM对象，避免重复查询数据库
        transactions_map = {t.id: t for t in all_transactions}

        hydrated_events = []
        for event in u_turn_events_with_ids:
            inflow_obj = transactions_map.get(event["inflow_id"])
            outflow_objs = [
                transactions_map.get(oid)
                for oid in event["outflow_ids"]
                if transactions_map.get(oid)
            ]

            if inflow_obj and outflow_objs:
                hydrated_events.append(
                    {
                        "inflow": inflow_obj,
                        "outflows": outflow_objs,
                        "total_outflow": event["total_outflow"],
                        "time_diff_hours": event["time_diff_hours"],
                    }
                )

        return hydrated_events

    async def perform_group_transaction_analysis(
        self, session: AsyncSession, *, person_ids: list[int]
    ) -> list[Transaction]:
        """
        执行多人联合交易流水分析。
        """
        # 直接调用更新后的仓库方法，一次性获取所有人的交易数据
        all_transactions = await self.transaction_repo.get_multi_by_person_ids(
            session, person_ids=person_ids
        )
        return all_transactions

    async def perform_group_counterparty_analysis(
        self, session: AsyncSession, *, person_ids: list[int]
    ) -> list[CounterpartyAnalysisSummary]:
        """
        执行多人联合对手方网络分析。
        """
        summary_data = (
            await self.counterparty_repo.get_summary_by_person_ids_grouped_by_name(
                session, person_ids=person_ids
            )
        )
        # 将数据库返回的原始行数据，转换为Pydantic模型列表
        return [CounterpartyAnalysisSummary.model_validate(row) for row in summary_data]


analysis_service = AnalysisService()
