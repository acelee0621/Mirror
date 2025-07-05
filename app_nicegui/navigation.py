# app_nicegui/navigation.py
from nicegui import ui


def build_sidebar_content():
    """
    这个函数只负责渲染侧边栏的 *内容*，
    不再创建 ui.left_drawer 容器本身。
    """
    ui.label("功能导航").classes("text-h6 q-pa-md")

    ui.link("主页", "/").classes("w-full")
    ui.link("账户明细", "/account_details").classes("w-full")
    ui.link("个人全局视图", "/global_dashboard").classes("w-full")
    ui.link("对手方网络", "/counterparty_analysis").classes("w-full")

    ui.separator()

    ui.link("文件上传", "/file_upload").classes("w-full")
    ui.link("管理中心", "/management_center").classes("w-full")
