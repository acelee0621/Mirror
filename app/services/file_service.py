# app/services/file_service.py
import os
import hashlib
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.config import settings
from app.repository.file_metadata import file_metadata_repository
from app.schemas.file_metadata import FileMetadataCreate
from app.models.file_metadata import FileMetadata
from app.core.exceptions import AlreadyExistsException, NotFoundException


class FileService:
    """
    处理文件上传和相关业务逻辑的服务层。
    """

    def __init__(self):
        self.repository = file_metadata_repository
        self.upload_path = Path(settings.LOCAL_STORAGE_PATH)
        self.upload_path.mkdir(parents=True, exist_ok=True)

    def _calculate_file_hash(self, content: bytes) -> str:
        """计算文件的 SHA256 哈希值"""
        sha256_hash = hashlib.sha256()
        sha256_hash.update(content)
        return sha256_hash.hexdigest()

    def _save_file_locally(
        self, file_content: bytes, file_hash: str, extension: str
    ) -> str:
        """将文件同步保存到本地，并以文件哈希值命名"""
        file_location = self.upload_path / f"{file_hash}{extension}"
        try:
            file_location.write_bytes(file_content)
            return str(file_location)
        except IOError as e:
            logger.error(f"无法将文件写入磁盘: {e}")
            raise HTTPException(status_code=500, detail="服务器无法保存上传的文件。")

    async def handle_file_upload(
        self, session: AsyncSession, *, file: UploadFile, account_id: int
    ) -> FileMetadata:
        """
        处理文件上传的核心逻辑。
        """
        try:
            # --- 使用 assert 进行类型收窄 ---
            # 我们断言这些值必须存在，否则就是无效的上传请求。
            # Pylance 会理解 assert 语句，并在后续代码中认为这些变量是非 None 类型。
            assert file.filename is not None, "缺少文件名。"
            assert file.size is not None, "缺少文件大小信息。"
            assert file.content_type is not None, "缺少文件类型信息。"
        except AssertionError as e:
            # 捕获断言错误，并将其转换为对前端友好的400错误。
            raise HTTPException(status_code=400, detail=f"上传的文件元数据不完整: {e}")

        # 1. 读取文件内容并计算哈希
        file_content = await file.read()
        file_hash = self._calculate_file_hash(file_content)

        # 2. 检查文件是否已存在
        existing_file = await self.repository.get_by_file_hash(
            session, file_hash=file_hash
        )
        if existing_file:
            raise AlreadyExistsException(
                detail=f"文件 '{file.filename}' 已于 {existing_file.upload_timestamp} 上传。"
            )

        # 3. 保存文件到本地
        # 经过 assert 后，file.filename 在这里已经被Pylance认为是 str 类型
        file_extension = Path(file.filename).suffix
        file_path = self._save_file_locally(file_content, file_hash, file_extension)

        # 4. 准备要存入数据库的元数据
        file_meta_in = FileMetadataCreate(
            filename=file.filename,
            file_path=file_path,
            file_hash=file_hash,
            filesize=file.size,
            mime_type=file.content_type,
            account_id=account_id,
        )

        # 5. 调用仓库层，创建数据库记录
        db_file_meta = await self.repository.create(session, obj_in=file_meta_in)

        return db_file_meta
    
    
    async def get_files_by_account(
        self, session: AsyncSession, *, account_id: int, skip: int = 0, limit: int = 100
    ) -> list[FileMetadata]:
        """获取指定账户下的所有文件元数据"""
        return await self.repository.get_multi_by_account_id(
            session, account_id=account_id, skip=skip, limit=limit
        )

    async def get_file_by_id(self, session: AsyncSession, *, file_id: int) -> FileMetadata:
        """通过ID获取单个文件元数据"""
        file_meta = await self.repository.get(session, id=file_id)
        if not file_meta:
            raise NotFoundException(detail=f"ID为 {file_id} 的文件不存在。")
        return file_meta

    async def delete_file(self, session: AsyncSession, *, file_id: int) -> None:
        """删除一个文件，包括数据库记录和物理文件"""
        # 1. 先获取元数据，确保文件存在，并拿到物理路径
        file_to_delete = await self.get_file_by_id(session, file_id=file_id)
        
        # 2. 删除物理文件
        try:
            file_path = Path(file_to_delete.file_path)
            if file_path.exists():
                os.remove(file_path)
                logger.info(f"已成功删除物理文件: {file_path}")
        except Exception as e:
            # 即使物理文件删除失败，也只记录错误，继续删除数据库记录
            logger.error(f"删除物理文件失败: {file_to_delete.file_path}. 错误: {e}")

        # 3. 删除数据库记录
        await self.repository.delete(session, id=file_id)


# 创建一个服务层的单例，方便在路由层注入和使用
file_service = FileService()
