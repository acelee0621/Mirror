from datetime import datetime

from app.schemas.base import BaseSchema


# ===================================================================
# File 相关模型
# ===================================================================
# 定义了所有FileMetadata变体共有的字段
class FileMetadataBase(BaseSchema):
    filename: str
    file_path: str
    file_hash: str
    filesize: int
    mime_type: str
    account_id: int


# --- 创建模型 ---
# 在创建新的文件元数据记录时，服务层将使用这个模型。
# 它继承了Base的所有字段，是创建新记录所需数据的完整集合。
class FileMetadataCreate(FileMetadataBase):
    pass


# --- 更新模型 ---
# 用于更新文件处理状态。
# 所有字段都是可选的，这样我们可以实现局部更新（PATCH）。
class FileMetadataUpdate(BaseSchema):
    processing_status: str | None = None
    error_message: str | None = None


# --- 数据库模型（用于读取） ---
# 这个模型代表了从数据库中读取出来的、完整的记录。
# 它包含了像 id 和 upload_timestamp 这样由数据库自动生成的字段。
# ConfigDict(from_attributes=True) 使得Pydantic可以从SQLAlchemy模型对象直接创建实例。
class FileMetadataInDB(FileMetadataBase):
    id: int
    upload_timestamp: datetime
    processing_status: str
    error_message: str | None = None


# --- 公开模型（API返回）---
# 这个模型定义了通过API返回给前端的、公开安全的数据结构。
# 我们通常不会把 file_path 或 file_hash 这类内部信息暴露给前端。
class FileMetadataPublic(BaseSchema):
    id: int
    filename: str
    filesize: int
    upload_timestamp: datetime
    processing_status: str
    error_message: str | None = None
