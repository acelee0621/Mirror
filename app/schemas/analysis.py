# app/schemas/analysis.py
from pydantic import Field, computed_field, BaseModel
from app.schemas.base import BaseSchema
from app.schemas.transaction import TransactionPublic


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


class UturnAnalysisRequest(BaseModel):
    """“快进快出”分析的请求体模型"""

    amount_threshold: float = Field(10000.0, gt=0, description="定义大额交易的金额门槛")
    time_window_hours: int = Field(
        72, gt=0, description="搜索匹配支出的时间窗口（小时）"
    )
    amount_tolerance: float = Field(
        0.1, ge=0, lt=1, description="金额匹配的容忍度 (0.1 代表 10%)"
    )


class UturnEvent(BaseModel):
    """单个“快进快出”事件的数据结构"""

    inflow: TransactionPublic
    outflows: list[TransactionPublic]
    total_outflow: float
    time_diff_hours: float


class UturnAnalysisResponse(BaseModel):
    """“快进快出”分析的响应体模型"""

    found_events: list[UturnEvent]
