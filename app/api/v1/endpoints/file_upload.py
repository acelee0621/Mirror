# app/api/v1/endpoints/file_upload.py
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.services.file_service import file_service
from app.schemas.file_metadata import FileMetadataPublic

# 创建一个新的路由器，用于管理文件上传相关的端点
router = APIRouter(prefix="/files", tags=["File Upload"])


@router.post(
    "/upload",
    response_model=FileMetadataPublic,
    summary="上传银行流水文件",
    description="上传一个Excel或CSV文件，系统将保存文件并为其创建元数据记录。",
)
async def upload_transaction_file(
    # 使用 Depends 注入数据库会话
    session: AsyncSession = Depends(get_db),
    # 从表单数据中获取 account_id。前端需要以 multipart/form-data 形式提交
    account_id: int = Form(...),
    # 获取上传的文件
    file: UploadFile = File(...),
):
    """
    处理银行流水文件的上传请求。

    - **account_id**: 文件所属的银行账户ID。
    - **file**: 要上传的 Excel 或 CSV 文件。
    """
    # 校验文件类型
    allowed_mime_types = [
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]
    if file.content_type not in allowed_mime_types:
        logger.warning(f"上传了不支持的文件类型: {file.content_type}")
        raise HTTPException(
            status_code=400,
            detail="文件类型不支持。请上传 Excel (.xls, .xlsx) 或 CSV (.csv) 文件。",
        )

    try:
        # 调用服务层处理核心逻辑
        logger.info(f"开始处理文件上传: {file.filename} for account_id: {account_id}")
        file_metadata = await file_service.handle_file_upload(
            session=session, file=file, account_id=account_id
        )
        logger.info(f"文件 '{file.filename}' 元数据创建成功，ID: {file_metadata.id}")

        # 返回对前端安全的公开数据模型
        return file_metadata

    # 路由层可以捕获服务层抛出的特定业务异常，并直接返回
    # 其他未捕获的异常将由你的全局异常处理器处理
    except HTTPException as http_exc:
        # 重新抛出，让FastAPI处理
        raise http_exc
    except Exception as e:
        # 对于其他未知错误，记录日志并返回一个通用的服务器错误
        logger.error(f"处理文件上传时发生未知错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="处理文件时发生内部错误。")
