from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase
from loguru import logger
from taskiq import TaskiqDepends
from app.core.config import settings


# --- 1. 全局变量定义 ---
# 这些全局变量将由各自的启动逻辑来填充。
engine: Optional[AsyncEngine] = None
SessionLocal: Optional[async_sessionmaker[AsyncSession]] = None

POSTGRES_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

# --- 基类 ---
class Base(DeclarativeBase):
    pass

# --- 2. 通用的数据库初始化和关闭函数 ---
# 这些函数现在是通用的，可以在任何需要初始化数据库的地方调用。
# 它们负责设置全局的 engine 和 SessionLocal。
async def setup_database_connection():
    """
    初始化全局的数据库引擎和会话工厂。
    这是一个通用的设置函数，可以在 FastAPI 或 TaskIQ worker 启动时调用。
    """
    global engine, SessionLocal
    if engine is not None and SessionLocal is not None:
        logger.info("数据库已初始化，跳过重复设置。")
        return

    engine = create_async_engine(
        POSTGRES_DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        echo=settings.DB_ECHO,
    )
    SessionLocal = async_sessionmaker(
        class_=AsyncSession, expire_on_commit=False, bind=engine
    )
    logger.info("数据库引擎和会话工厂已创建。")

async def shutdown_database_connection():
    """
    关闭全局的数据库引擎连接池。
    这是一个通用的关闭函数，可以在 FastAPI 或 TaskIQ worker 关闭时调用。
    """
    global engine
    if engine:
        await engine.dispose()
        engine = None # 清理引用
        SessionLocal = None # 清理引用
        logger.info("数据库引擎连接池已关闭。")


# --- 3. 依赖注入函数 ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    为每个请求或任务提供数据库会话。
    它现在依赖由 setup_database_connection 管理的全局 SessionLocal。
    """
    if SessionLocal is None:
        # 这个错误通常不应该在正确配置的生产环境中出现
        # 它表明 setup_database_connection 未在应用或worker启动时调用
        raise Exception("数据库未初始化。请检查 FastAPI 的 lifespan 或 TaskIQ worker 的启动配置。")

    async with SessionLocal() as session:
        yield session

# TaskIQ 专用的快捷依赖项
get_db_for_taskiq = TaskiqDepends(get_db)


# --- 4. 数据库表创建工具 (如果需要) ---
async def create_db_and_tables():
    if not engine:
        raise Exception("无法创建表，因为数据库引擎未初始化。")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)