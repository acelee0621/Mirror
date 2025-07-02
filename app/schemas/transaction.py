# app/schemas/transaction.py
import datetime
from pydantic import Field
from app.schemas.base import BaseSchema

# 导入其他模型的公开Schema，用于嵌套
from app.schemas.account import AccountPublic
from app.schemas.counterparty import CounterpartyPublic

# --- 创建模型 ---
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
    bank_transaction_id: str = Field(..., max_length=200)
    account_id: int
    counterparty_id: int
    
    # --- 新增字段 ---
    # is_cash 是从原始数据中直接解析得出的事实，创建时就应确定
    is_cash: bool = Field(False, description="是否为现金交易")

    # 可选字段
    balance_after_txn: float | None = None
    transaction_method: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=200)
    branch_name: str | None = Field(None, max_length=200)
    
    # category 是后续分析生成的，创建时不提供
    category: str | None = Field(None, max_length=100, exclude=True)


# --- 更新模型 ---
class TransactionUpdate(BaseSchema):
    """
    更新 Transaction 时使用的模型。
    例如，未来可以用来手动修正交易分类。
    """
    # 允许用户在后续手动修正或添加交易分类
    category: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)
    # 也许未来还想允许修正其他字段...


# --- 公开模型（API返回）---
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
    
    # --- 新增字段 ---
    is_cash: bool
    category: str | None

    location: str | None
    branch_name: str | None

    # 嵌套关联对象的公开信息
    account: AccountPublic
    counterparty: CounterpartyPublic
