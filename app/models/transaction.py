import datetime

from sqlalchemy import Integer, String, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.counterparty import Counterparty


class Transaction(Base):
    """
    事实表，存储每一笔交易的核心事实和元数据。
    """

    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

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
    balance_after_txn: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True, comment="此次交易发生后，本方账户的余额"
    )

    description: Mapped[str] = mapped_column(
        String, nullable=False, comment="银行提供的交易摘要或描述"
    )
    bank_transaction_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        comment="银行系统生成的唯一交易流水号，用于防止重复导入",
    )

    # Forensic metadata
    location: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="交易发生地点"
    )
    branch_name: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="交易发生的具体网点名称"
    )

    # Relationships
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"))
    account: Mapped["Account"] = relationship(back_populates="transactions")

    counterparty_id: Mapped[int] = mapped_column(ForeignKey("counterparty.id"))
    counterparty: Mapped["Counterparty"] = relationship()
