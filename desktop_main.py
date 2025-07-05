# desktop_main.py
from nicegui import app, ui
from fastapi import FastAPI
from loguru import logger
from contextlib import asynccontextmanager

# 1. 导入我们现有的后端服务和模块
from app.core.taskiq_app import broker
from app.core.database import setup_database_connection, shutdown_database_connection
from app.api.v1.endpoints import person, account, transaction, counterparty, file_upload
from app_nicegui.navigation import build_sidebar_content
from app_nicegui.management_center import show_management_center_page
from app_nicegui.file_upload import show_file_upload_page


# 2. 定义应用的生命周期事件
#    NiceGUI 的 app 对象本身就是一个 FastAPI 实例，我们可以直接复用
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """
    应用生命周期管理：处理启动和关闭事件。
    """
    logger.info("应用启动，开始加载所有资源...")
    try:
        await setup_database_connection()
        logger.info("✅ 数据库初始化成功")
        # 在应用启动时，也需要启动 broker 以便能发送任务
        await broker.startup()
        logger.info("✅ Taskiq Broker 客户端已启动")
    except Exception as e:
        logger.critical(f"❌ 应用启动失败: {e}")
        raise

    yield

    logger.info("应用关闭，开始释放资源...")
    try:
        # 在应用关闭时，也需要关闭 broker
        await broker.shutdown()
        logger.info("✅ Taskiq Broker 客户端已关闭")
        await shutdown_database_connection()
        logger.info("✅ 数据库连接池已关闭")
    except Exception as e:
        logger.error(f"⚠️ 关闭资源时出错: {e}")
        raise
    logger.info("资源释放完毕。")


# 3. 将我们所有的API路由挂载到 /api/v1 路径下
#    这样，即使在桌面应用中，我们的API依然可用，便于未来可能的扩展
app.include_router(person.router, prefix="/api/v1")
app.include_router(account.router, prefix="/api/v1")
app.include_router(transaction.router, prefix="/api/v1")
app.include_router(counterparty.router, prefix="/api/v1")
app.include_router(file_upload.router, prefix="/api/v1")


# --- 统一在页面函数中创建布局 ---
def create_shared_layout():
    """创建一个包含头部和侧边栏的共享布局。在每个页面函数中调用。"""
    # 创建头部
    with ui.header(elevated=True).classes("justify-between text-white bg-primary"):
        ui.label("明镜 D-Sensor 桌面版").classes("text-h5")
        # 按钮现在可以控制侧边栏了
        ui.button(on_click=lambda: left_drawer.toggle(), icon="menu").props(
            "flat color=white"
        )

    # 创建侧边栏，并填充内容
    with ui.left_drawer().classes("bg-grey-2") as left_drawer:
        build_sidebar_content()


# --- 构建UI页面 ---
@ui.page("/")
def index():
    create_shared_layout()
    with ui.column().classes("w-full items-center"):
        ui.label("明镜桌面分析").classes("text-3xl font-bold text-primary mt-8")

        with ui.row().classes("mt-4"):
            ui.button("导入 Excel").classes(
                "bg-green-500 text-white rounded-lg px-4 py-2"
            )
            ui.button("下载报告").classes("bg-blue-500 text-white rounded-lg px-4 py-2")

        ui.markdown("""
        欢迎使用明镜 D-Sensor！你可以上传账单、分析流向、生成报告，一切本地运行。
        """).classes("text-center max-w-xl mt-6")


@ui.page("/management_center")
def management_center_page():
    create_shared_layout()
    show_management_center_page()


# ... 未来在这里为其他页面添加 @ui.page 装饰器 ...


# 5. 启动 NiceGUI 应用，并传入我们的 lifespan
ui.run(
    title="明镜 D-Sensor",
    port=8080,
    #    reload=True,
    lifespan=lifespan,
)
