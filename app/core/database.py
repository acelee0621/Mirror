from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# --- 1. 全局变量定义 ---
# 将原来的直接创建，改为先定义变量并初始化为 None。
# 它们将由 FastAPI 的生命周期事件来填充和管理。
engine: Optional[AsyncEngine] = None
SessionLocal: Optional[async_sessionmaker[AsyncSession]] = None


POSTGRES_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

class Base(DeclarativeBase):
    pass


# --- 2. FastAPI 生命周期管理函数 ---
# 这两个函数是【专门】给 FastAPI 在 main.py 的 lifespan 中调用的。

def initialize_database_for_fastapi():
    """
    在 FastAPI 应用启动时，创建全局的数据库引擎和会话工厂。
    """
    global engine, SessionLocal
    
    engine = create_async_engine(
        POSTGRES_DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600,
        echo=False,
    )
    SessionLocal = async_sessionmaker(
        class_=AsyncSession, expire_on_commit=False, bind=engine
    )
    print("数据库引擎和会话工厂已为 FastAPI 创建。")


async def close_database_for_fastapi():
    """
    在 FastAPI 应用关闭时，关闭全局的数据库引擎。
    """
    global engine
    if engine:
        await engine.dispose()
        print("FastAPI 的数据库引擎连接池已关闭。")

# --- 3. FastAPI 依赖注入函数 ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 依赖项，为每个请求提供数据库会话。
    它现在依赖由 lifespan 管理的全局 SessionLocal。
    """
    if SessionLocal is None:
        raise Exception("数据库未初始化。请检查 FastAPI 的 lifespan 配置。")
    
    async with SessionLocal() as session:
        yield session

# --- 4. Taskiq 专属的工厂函数 ---
# 给 Taskiq 任务使用
def create_engine_and_session_for_celery():
    """
    为单个 Celery 任务创建一次性的、独立的数据库引擎和会话工厂。
    它创建的是局部变量，与上面的全局 engine 和 SessionLocal 无关。
    """
    # 注意：这里创建的是局部变量 celery_engine, CelerySessionLocal
    celery_engine = create_async_engine(POSTGRES_DATABASE_URL, echo=False)
    CelerySessionLocal = async_sessionmaker(class_=AsyncSession, expire_on_commit=False, bind=celery_engine)
    
    # 返回这两个新创建的、临时的实例
    return celery_engine, CelerySessionLocal


# --- 5. 数据库表创建工具  ---
# 目前通过 Alembic 管理数据库迁移，但如果需要，这个函数仍然可用。
async def create_db_and_tables():
    if not engine:
        raise Exception("无法创建表，因为数据库引擎未初始化。")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)