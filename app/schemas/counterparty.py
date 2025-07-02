# app/schemas/counterparty.py
from pydantic import Field
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
