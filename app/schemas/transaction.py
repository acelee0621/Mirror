# app/schemas/transaction.py
import datetime
from pydantic import Field
from app.schemas.base import BaseSchema

# 导入其他模型的公开Schema，用于嵌套
from app.schemas.account import AccountPublic
from app.schemas.counterparty import CounterpartyPublic


# --- 创建模型 ---
# 这个模型现在直接、清晰地定义了创建一条交易记录所需要的所有字段。
class TransactionCreate(BaseSchema):
    """
    创建 Transaction 时使用的模型。
    这些字段将由后台的解析服务提供。
    """

    # 必填字段
    transaction_date: datetime.datetime
    amount: float
    currency: str = Field(..., max_length=10)
    transaction_type: str = Field(..., max_length=20)  # 'DEBIT' or 'CREDIT'
    description: str = Field(..., max_length=500)
    transaction_method: str | None = Field(None, max_length=100)
    bank_transaction_id: str = Field(..., max_length=200)
    account_id: int
    counterparty_id: int

    # 可选字段
    balance_after_txn: float | None = None
    location: str | None = Field(None, max_length=200)
    branch_name: str | None = Field(None, max_length=200)


# --- 更新模型 ---
# 这个模型定义了所有可以被更新的字段，且它们都是可选的。
class TransactionUpdate(BaseSchema):
    """
    更新 Transaction 时使用的模型。
    例如，未来可以用来手动修正交易分类。
    """

    transaction_date: datetime.datetime | None = None
    amount: float | None = None
    currency: str | None = Field(None, max_length=10)
    transaction_type: str | None = Field(None, max_length=20)
    balance_after_txn: float | None = None
    description: str | None = Field(None, max_length=500)
    location: str | None = Field(None, max_length=200)
    branch_name: str | None = Field(None, max_length=200)


# --- 公开模型（API返回）---
# 这个模型定义了通过API返回给前端的、完整的交易公开信息。
class TransactionPublic(BaseSchema):
    """
    通过API返回给前端的、完整的交易公开信息。
    """

    id: int
    transaction_date: datetime.datetime
    amount: float
    currency: str
    transaction_type: str
    balance_after_txn: float | None
    description: str
    transaction_method: str | None
    bank_transaction_id: str
    location: str | None
    branch_name: str | None

    # 嵌套关联对象的公开信息
    account: AccountPublic
    counterparty: CounterpartyPublic
