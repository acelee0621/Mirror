from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from redis.asyncio import Redis
import aio_pika
from app.core.config import settings
from app.core.database import get_db

router = APIRouter(prefix="", tags=["Health Check"])


@router.get("/health/db", summary="数据库健康检查")
async def check_database_health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "detail": "数据库连接正常"}
    except Exception as e:
        return {"status": "error", "detail": f"数据库连接失败: {str(e)}"}


@router.get("/health/redis", summary="Redis 健康检查")
async def check_redis_health():
    try:
        redis = Redis.from_url(
            f"redis://{settings.REDIS_HOST}", encoding="utf-8", decode_responses=True
        )
        pong = await redis.ping()
        await redis.close()
        if pong:
            return {"status": "ok", "detail": "Redis 正常响应"}
        return {"status": "error", "detail": "Redis 未响应"}
    except Exception as e:
        return {"status": "error", "detail": f"Redis 连接失败: {str(e)}"}


@router.get("/health/rabbitmq", summary="RabbitMQ 健康检查")
async def check_rabbitmq_health():
    try:
        conn = await aio_pika.connect_robust(
            f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}"
            f"@{settings.RABBITMQ_HOST}/"
        )
        await conn.close()
        return {"status": "ok", "detail": "RabbitMQ 连接成功"}
    except Exception as e:
        return {"status": "error", "detail": f"RabbitMQ 连接失败: {str(e)}"}


@router.get("/health", summary="聚合健康检查")
async def health_check(
    db_result=Depends(check_database_health),
    redis_result=Depends(check_redis_health),
    rabbitmq_result=Depends(check_rabbitmq_health),
):
    status = (
        "ok 👍 "
        if all(r["status"] == "ok" for r in [db_result, redis_result, rabbitmq_result])
        else "error"
    )
    return {
        "status": status,
        "components": {
            "database": db_result,
            "redis": redis_result,
            "rabbitmq": rabbitmq_result,
        },
    }
