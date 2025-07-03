# app/models/counterparty.py
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Counterparty(Base):
    """
    存储所有交易对手方的信息，无论是个人还是商户。
    """

    __tablename__ = "counterparty"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String, index=True, comment="对手方名称，如“张三”或“京东商城”"
    )
    account_number: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True, comment="对手方的账号"
    )
    counterparty_type: Mapped[str] = mapped_column(
        String, comment="对手类型，如“PERSON”或“MERCHANT”"
    )
