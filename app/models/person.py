# app/models/person.py
from typing import TYPE_CHECKING, cast

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.associationproxy import association_proxy, AssociationProxy
from app.core.database import Base


if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.transaction import Transaction


class Person(Base):
    """
    存储用户信息，即流水的所有者。
    """

    __tablename__ = "person"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String, index=True)
    id_type: Mapped[str | None] = mapped_column(String, nullable=True)
    id_number: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationship to Account
    accounts: Mapped[list["Account"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )

    # --- 【核心新增代码】 ---
    # 3. 创建一个名为 transactions 的关联代理
    # 它能“穿透” accounts 关系，直接访问到所有账户下的所有交易
    transactions: AssociationProxy[list["Transaction"]] = cast(
        AssociationProxy, association_proxy("accounts", "transactions")
    )
