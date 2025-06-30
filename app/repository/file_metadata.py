# app/repository/file_metadata.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 导入我们通用的基类
from app.repository.base import BaseRepository

# 导入模型和Schemas
from app.models.file_metadata import FileMetadata
from app.schemas.file_metadata import FileMetadataCreate, FileMetadataUpdate


class FileMetadataRepository(
    BaseRepository[FileMetadata, FileMetadataCreate, FileMetadataUpdate]
):
    """
    FileMetadata 模型的仓库层。

    它继承了 BaseRepository，自动获得了所有基础的 CRUD 方法。
    我们在这里添加针对 FileMetadata 模型的特殊查询方法。
    """

    async def get_by_file_hash(
        self, session: AsyncSession, *, file_hash: str
    ) -> FileMetadata | None:
        """
        根据文件的 SHA256 哈希值查询一条文件元数据记录。

        这个方法对于防止用户重复上传和处理同一个文件至关重要。

        参数:
            session: 数据库会话。
            file_hash: 要查询的文件的哈希值。

        返回:
            找到的 FileMetadata 对象，如果未找到则返回 None。
        """
        statement = select(self.model).where(self.model.file_hash == file_hash)
        result = await session.scalars(statement)
        return result.one_or_none()


# 创建一个仓库的单例，方便在项目的其他地方（如服务层）直接导入和使用。
file_metadata_repository = FileMetadataRepository(FileMetadata)
