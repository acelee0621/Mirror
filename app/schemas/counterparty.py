# app/schemas/counterparty.py
from pydantic import Field, computed_field
from app.schemas.base import BaseSchema


# --- 基础模型 ---
class CounterpartyBase(BaseSchema):
    """
    Counterparty 模型的共用基础字段。
    """

    name: str | None = Field(None, max_length=200)
    account_number: str | None = Field(None, max_length=100)
    counterparty_type: str | None = Field(
        None, max_length=50
    )  # e.g., 'PERSON' or 'MERCHANT'


# --- 创建模型 ---
class CounterpartyCreate(CounterpartyBase):
    """
    创建 Counterparty 时使用的模型。
    """

    name: str = Field(..., max_length=200)
    counterparty_type: str = Field(..., max_length=50)


# --- 更新模型 ---
class CounterpartyUpdate(CounterpartyBase):
    """
    更新 Counterparty 时使用的模型。所有字段都是可选的。
    """

    pass


# --- 公开模型（API返回）---
class CounterpartyPublic(CounterpartyBase):
    """
    通过API返回给前端的公开模型。
    """

    id: int


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


class CounterpartyAnalysisSummary(BaseSchema):
    """用于按名称聚合的对手方分析模型"""

    name: str
    total_income: float
    total_expense: float
    transaction_count: int

    @computed_field
    @property
    def net_flow(self) -> float:
        return self.total_income + self.total_expense

    @computed_field
    @property
    def total_flow(self) -> float:
        return abs(self.total_income) + abs(self.total_expense)
