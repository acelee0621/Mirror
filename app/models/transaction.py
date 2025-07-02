# app/models/transaction.py
import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, ForeignKey, Numeric, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.counterparty import Counterparty


class Transaction(Base):
    """
    事实表，存储每一笔交易的核心事实和元数据。
    字段已按逻辑重要性重新排序。
    """

    __tablename__ = "transaction"

    # --- 身份标识 ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # --- 核心交易事实 ---
    transaction_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), index=True, comment="交易发生的精确日期和时间"
    )
    amount: Mapped[float] = mapped_column(
        Numeric(12, 2), comment="交易金额。正数为收入，负数为支出。"
    )
    currency: Mapped[str] = mapped_column(String(3), comment="货币类型，如“CNY”")
    transaction_type: Mapped[str] = mapped_column(
        String, comment="交易类型, 'DEBIT' (支出) 或 'CREDIT' (收入)"
    )

    # --- 核心上下文 ---
    description: Mapped[str] = mapped_column(
        String, nullable=False, comment="银行提供的交易摘要或描述"
    )
    transaction_method: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="原始交易类型或渠道，如'快捷支付'"
    )

    # --- 状态与标识符 ---
    balance_after_txn: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True, comment="此次交易发生后，本方账户的余额"
    )
    bank_transaction_id: Mapped[str] = mapped_column(
        String, unique=True, index=True, comment="银行系统生成的唯一交易流水号"
    )

    # --- 法证元数据 (Forensic Metadata) ---
    is_cash: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否为现金交易"
    )
    location: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="交易发生地点"
    )
    branch_name: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="交易发生的具体网点名称"
    )

    # --- 衍生/分析字段 (Derived/Analysis Fields) ---
    category: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True, comment="由系统分析得出的交易分类"
    )

    # --- 关系外键 (Relationships) ---
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"))
    counterparty_id: Mapped[int] = mapped_column(ForeignKey("counterparty.id"))

    # --- ORM 关系属性 ---
    account: Mapped["Account"] = relationship(back_populates="transactions")
    counterparty: Mapped["Counterparty"] = relationship()
