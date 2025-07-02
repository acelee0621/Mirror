# app/tasks/tasks.py
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.taskiq_app import broker
from app.core.database import get_db_for_taskiq
from app.tasks.utils.parser_service import parser_service
from app.repository.file_metadata import file_metadata_repository

@broker.task
async def process_file_task(
    file_id: int, session: AsyncSession = get_db_for_taskiq
) -> dict:
    """
    负责处理上传文件的后台任务。
    """
    logger.info(f"Taskiq 开始处理文件 ID: {file_id} ")
    
    # 1. 获取文件元数据
    file_meta = await file_metadata_repository.get(session, id=file_id)
    if not file_meta:
        logger.error(f"任务失败：找不到文件 ID: {file_id}")
        return {"error": "File not found"}

    try:
        # 2. 更新状态为“处理中”
        file_meta.processing_status = "PROCESSING"
        session.add(file_meta)
        await session.commit()

        # 3. 调用核心服务进行解析和入库
        result = await parser_service.process_and_save_transactions(
            session=session,
            file_path=file_meta.file_path,
            account_id=file_meta.account_id
        )
        
        # 4. 更新状态为“成功”
        file_meta.processing_status = "SUCCESS"
        session.add(file_meta)
        await session.commit()
        
        logger.success(f"文件 {file_id} ({file_meta.filename}) 已由 Taskiq 处理成功: {result}")
        return result

    except Exception as e:
        logger.exception(f"Taskiq 处理文件 {file_id} 失败: {e}")
        # 5. 如果失败，更新状态并记录错误信息
        if file_meta:
            file_meta.processing_status = "FAILED"
            file_meta.error_message = str(e)
            session.add(file_meta)
            await session.commit()
        raise # 重新抛出异常，Taskiq会将其标记为失败