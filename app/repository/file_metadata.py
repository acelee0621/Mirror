# app/repository/file_metadata.py
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.base import BaseRepository
from app.models.file_metadata import FileMetadata
from app.schemas.file_metadata import FileMetadataCreate, FileMetadataUpdate

class FileMetadataRepository(
    BaseRepository[FileMetadata, FileMetadataCreate, FileMetadataUpdate]
):
    """
    FileMetadata 模型的仓库层。
    """

    async def get_by_file_hash(
        self, session: AsyncSession, *, file_hash: str
    ) -> FileMetadata | None:
        """
        根据文件的 SHA256 哈希值查询一条文件元数据记录。
        """
        statement = select(self.model).where(self.model.file_hash == file_hash)
        result = await session.scalars(statement)
        return result.one_or_none()

    # --- 查询多个文件 ---
    async def get_multi_by_account_id(
        self, session: AsyncSession, *, account_id: int, skip: int = 0, limit: int = 100
    ) -> List[FileMetadata]:
        """
        根据账户ID获取其所有上传文件的元数据列表（支持分页）。
        """
        statement = (
            select(self.model)
            .where(self.model.account_id == account_id)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.upload_timestamp.desc()) # 按上传时间倒序
        )
        result = await session.scalars(statement)
        return list(result.all())


# 创建仓库的单例
file_metadata_repository = FileMetadataRepository(FileMetadata)
