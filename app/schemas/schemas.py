from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


# ===================================================================
# 通用配置和基础类
# ===================================================================


class BaseSchema(BaseModel):
    # 配置Pydantic模型以兼容ORM对象
    model_config = ConfigDict(from_attributes=True)
    
    
# ===================================================================
# File 相关模型
# ===================================================================


class SourceDocumentBase(BaseSchema):    
    original_filename: str = Field(..., max_length=255, description="原始文件名")
    content_type: str = Field(..., max_length=100, description="文件MIME类型")
    size: int = Field(..., description="文件大小(字节)")


class SourceDocumentCreate(SourceDocumentBase):
    pass


class SourceDocumentUpdate(BaseSchema):
    pass


class SourceDocumentResponse(SourceDocumentBase):
    id: int = Field(..., description="附件ID")    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")