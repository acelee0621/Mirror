from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.person import Person
    from app.models.transaction import Transaction


class Account(Base):
    """
    存储用户自己拥有的银行账户信息。
    """

    __tablename__ = "account"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_name: Mapped[str] = mapped_column(
        String, index=True, comment="账户的自定义名称，如“招行工资卡”"
    )
    account_number: Mapped[str] = mapped_column(
        String, unique=True, comment="本方账户的完整账号或卡号（明文存储）"
    )
    account_type: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="账户类型，如“储蓄卡”、“信用卡”"
    )
    institution: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="所属金融机构，如“招商银行”"
    )

    # Relationship to Person
    owner_id: Mapped[int] = mapped_column(ForeignKey("person.id"))
    owner: Mapped["Person"] = relationship(back_populates="accounts")

    # Relationship to Transaction
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")
