# app/models/person.py
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.account import Account


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
