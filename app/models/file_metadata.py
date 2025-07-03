# app/models/file_metadata.py
import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.account import Account


class FileMetadata(Base):
    __tablename__ = "file_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    filesize: Mapped[int] = mapped_column(Integer)
    mime_type: Mapped[str] = mapped_column(String)
    upload_timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC)
    )
    processing_status: Mapped[str] = mapped_column(
        String, default="PENDING"
    )  # PENDING, PROCESSING, SUCCESS, FAILED
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 关系：这个文件属于哪个银行账户
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"))
    account: Mapped["Account"] = relationship(back_populates="files")
