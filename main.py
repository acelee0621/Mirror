from loguru import logger
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import (
    setup_database_connection,
    shutdown_database_connection,
)
from app.core.taskiq_app import broker
from app.utils.migrations import run_migrations
from app.api.v1 import health
from app.api.v1.endpoints import person, account, file_upload


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
    logger.info("所有资源加载完毕，应用准备就绪。🚀")

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


app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health.router)
app.include_router(person.router)
app.include_router(account.router)
app.include_router(file_upload.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
