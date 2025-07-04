# app/schemas/analysis.py
from pydantic import Field, computed_field
from app.schemas.base import BaseSchema

class CounterpartySummary(BaseSchema):
    """
    用于对手方分析汇总的公开数据模型。
    """
    id: int
    name: str
    account_number: str | None = None
    counterparty_type: str
    
    total_income: float = Field(..., description="总收入金额")
    total_expense: float = Field(..., description="总支出金额 (负数)")
    transaction_count: int = Field(..., description="总交易笔数")

    @computed_field
    @property
    def net_flow(self) -> float:
        """计算净流入/流出金额"""
        return self.total_income + self.total_expense
