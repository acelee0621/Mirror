# app_nicegui/file_upload.py
from nicegui import ui, app
from typing import Dict, Any
import pandas as pd
import asyncio
import os

# 导入我们需要的服务层和数据库会话工厂
from app.services.person_service import person_service
from app.services.file_service import file_service

from app.core.database import get_session_local

# 使用环境变量读取API基础URL
# 注意：在NiceGUI的直接上传模式下，这个URL主要用于API的健康检查或未来可能的其他API调用
API_BASE_URL = os.getenv("STREAMLIT_API_BASE_URL", "http://127.0.0.1:8000/api/v1")


def format_status(status: str) -> str:
    """美化状态显示"""
    status_map = {
        "SUCCESS": "✅ 成功",
        "FAILED": "❌ 失败",
        "PROCESSING": "⏳ 处理中",
        "PENDING": "⌛ 等待中",
    }
    return status_map.get(status, status)


def show_file_upload_page():
    """渲染文件上传页面的所有UI元素"""
    ui.label("上传银行流水文件").classes("text-h4 q-ma-md")

    # 使用一个字典来管理页面的响应式状态
    state: Dict[str, Any] = {
        "person_options": {},
        "account_options": {},
        "file_history": [],
    }

    async def load_persons():
        """异步加载所有用户"""
        session_local = get_session_local()
        async with session_local() as session:
            try:
                all_persons = await person_service.get_all_persons(session)
                state["person_options"] = {p.id: p.full_name for p in all_persons}
                person_select.set_options(state["person_options"], clearable=True)
                person_select.update()
            except Exception as e:
                ui.notify(f"加载用户列表失败: {e}", type="negative")

    async def update_accounts(person_id: int | None):
        """当用户选择变化时，更新账户下拉列表"""
        if not person_id:
            state["account_options"] = {}
        else:
            session_local = get_session_local()
            async with session_local() as session:
                person = await person_service.get_person_by_id(
                    session, person_id=person_id
                )
                state["account_options"] = {
                    acc.id: acc.account_name for acc in person.accounts
                }

        account_select.set_options(state["account_options"], clearable=True)
        account_select.value = None  # 清空账户选择
        state["file_history"].clear()  # 清空文件历史
        history_table.update()  # 更新表格

    async def refresh_history(account_id: int | None):
        """刷新文件历史记录"""
        if not account_id:
            state["file_history"] = []
        else:
            session_local = get_session_local()
            async with session_local() as session:
                try:
                    files = await file_service.get_files_by_account(
                        session, account_id=account_id
                    )
                    # 【修复点 1】: 手动将 SQLAlchemy 对象转换为字典
                    state["file_history"] = [
                        {
                            "id": f.id,
                            "filename": f.filename,
                            "processing_status": f.processing_status,
                            "filesize": f.filesize,
                            "upload_timestamp": f.upload_timestamp,
                            "error_message": f.error_message,
                        }
                        for f in files
                    ]
                except Exception as e:
                    ui.notify(f"刷新文件历史失败: {e}", type="negative")
                    state["file_history"] = []
        history_table.update()

    # --- UI 布局 ---
    with ui.card().classes("w-full"):
        # 【修复点 2】: on_change 现在直接传递值，回调函数不再有循环引用问题
        person_select = ui.select(
            options={}, label="第一步：选择用户", on_change=update_accounts
        ).classes("w-full")
        account_select = ui.select(
            options={}, label="第二步：选择银行账户", on_change=refresh_history
        ).classes("w-full")

        # 【修复点 3】: 将文件上传的逻辑完全解耦
        upload = ui.upload(
            label="第三步：上传文件",
            on_upload=lambda e: app.storage.user["upload_info"](
                e
            ),  # 将文件信息存入会话
            auto_upload=True,
            max_files=1,
        ).props('accept=".csv, .xlsx, .xls"')

    async def handle_upload_logic():
        """一个独立的函数来处理上传逻辑，在按钮点击时调用"""
        account_id = account_select.value
        upload_event = app.storage.user.get("latest_upload")

        if not account_id:
            ui.notify("请先选择一个银行账户！", type="warning")
            return
        if not upload_event:
            ui.notify("请先选择一个文件！", type="warning")
            return

        with ui.spinner():
            session_local = get_session_local()
            async with session_local() as session:
                try:
                    # 我们在Python端重新构建一个模拟的UploadFile对象
                    from starlette.datastructures import UploadFile
                    from io import BytesIO

                    temp_file = UploadFile(
                        filename=upload_event.name,
                        file=BytesIO(upload_event.content.read()),
                    )

                    await file_service.handle_file_upload(
                        session, file=temp_file, account_id=account_id
                    )
                    ui.notify(
                        f"🎉 文件 '{upload_event.name}' 上传成功！后台正在处理...",
                        type="positive",
                    )
                    await refresh_history()
                    app.storage.user.pop("latest_upload", None)  # 清除已处理的文件
                    upload.clear()  # 清空上传组件
                except Exception as ex:
                    ui.notify(f"上传失败: {ex}", type="negative", multi_line=True)

    # 将上传信息存储到会话中，以便按钮可以访问
    app.storage.user["upload_info"] = lambda e: app.storage.user.update(latest_upload=e)
    ui.button("🚀 开始上传和处理", on_click=handle_upload_logic).classes("q-mt-md")

    ui.separator().classes("q-my-md")

    ui.label("📂 文件上传历史").classes("text-h6")
    ui.button(
        "🔄 手动刷新",
        on_click=lambda: asyncio.create_task(refresh_history(account_select.value)),
    )

    columns = [
        {"name": "filename", "label": "文件名", "field": "filename", "align": "left"},
        {
            "name": "processing_status",
            "label": "处理状态",
            "field": "processing_status",
            "format": format_status,
        },
        {
            "name": "filesize",
            "label": "大小(KB)",
            "field": "filesize",
            "format": lambda v: f"{(v / 1024):.2f}",
        },
        {
            "name": "upload_timestamp",
            "label": "上传时间",
            "field": "upload_timestamp",
            "format": lambda v: pd.to_datetime(v).strftime("%Y-%m-%d %H:%M:%S"),
        },
        {
            "name": "error_message",
            "label": "错误信息",
            "field": "error_message",
            "format": lambda v: v or "无",
        },
    ]
    history_table = ui.table(
        columns=columns, rows=state["file_history"], row_key="id"
    ).classes("w-full")

    app.on_startup(load_persons)
