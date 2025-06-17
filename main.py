import asyncio

from fastapi import FastAPI, Response

from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import (
    initialize_database_for_fastapi,
    close_database_for_fastapi,
)

from app.utils.migrations import run_migrations



# Run migrations on startup
run_migrations()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 应用启动阶段 ---
    print("应用启动，开始并行加载所有资源...")

    # 将所有同步的、耗时的启动任务都封装成一个可在事件循环中等待的对象
    # 这样可以防止它们阻塞主线程
    startup_tasks = [
        asyncio.to_thread(initialize_database_for_fastapi),
        
    ]

    # 使用 asyncio.gather 来【并行】执行所有启动任务
    # 这会比一个一个顺序执行要快得多
    await asyncio.gather(*startup_tasks)

    print("所有资源加载完毕，应用准备就绪。🚀")

    yield

    # --- 应用关闭阶段 ---
    print("应用关闭，开始释放资源...")
    await close_database_for_fastapi()
    print("资源释放完毕。")


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
