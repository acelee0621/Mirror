from loguru import logger
from fastapi import FastAPI, Response

from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import (
    setup_database_connection,
    shutdown_database_connection,
)
from app.core.taskiq_app import broker
from app.utils.migrations import run_migrations


# Run migrations on startup
run_migrations()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 应用启动阶段 ---
    logger.info("应用启动，开始加载所有资源...")

    try:
        await setup_database_connection()         
        logger.info("✅ 数据库初始化成功")
    except Exception as e:
        logger.critical(f"❌ 数据库初始化失败: {e}")
        raise
    await broker.startup()
    print("所有资源加载完毕，应用准备就绪。🚀")

    yield

    # --- 应用关闭阶段 ---
    logger.info("应用关闭，开始释放资源...")
    try:
        await shutdown_database_connection()  # 必须异步
        logger.info("✅ 数据库连接池已关闭")
    except Exception as e:
        logger.error(f"⚠️ 关闭数据库时出错: {e}")
        raise
    await broker.shutdown()
    logger.info("资源释放完毕。")


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router()


@app.get("/health")
async def health_check(response: Response):
    response.status_code = 200
    return {"status": "ok 👍 "}
