from loguru import logger
from taskiq_aio_pika import AioPikaBroker
from taskiq_redis import RedisAsyncResultBackend

from app.core.config import settings
from app.core.database import setup_database_connection, shutdown_database_connection


class CustomAioPikaBroker(AioPikaBroker):
    async def startup(self) -> None:
        """
        TaskIQ worker 启动时调用此方法。
        在此处初始化数据库引擎和会话。
        """
        await super().startup()  # 首先调用父类的启动方法，确保 AioPika 连接建立
        await setup_database_connection()  # 调用通用的数据库设置函数
        logger.info("TaskIQ worker: 数据库引擎和会话工厂已初始化。")

    async def shutdown(self) -> None:
        """
        TaskIQ worker 关闭时调用此方法。
        在此处关闭数据库引擎。
        """
        await super().shutdown()  # 首先调用父类的关闭方法，确保 AioPika 连接关闭
        await shutdown_database_connection()  # 调用通用的数据库关闭函数
        logger.info("TaskIQ worker: 数据库引擎连接池已关闭。")


# 使用您的自定义 broker 类创建 broker 实例
broker = CustomAioPikaBroker(
    f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}"
    f"@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}//"
)

# 创建使用 Redis 的结果后端
result_backend = RedisAsyncResultBackend(
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/2",
)

# 配置 broker
broker.result_backend = result_backend

# 导入任务模块 (确保任务被 TaskIQ 发现，防止循环引用)
# 如果启用任务发现就不需要
# from app.tasks import tasks

# 启动 worker 命令
# （官方推荐的命令，但是一定要将任务文件放在app/tasks/tasks.py中）
# uv run taskiq worker app.core.taskiq_app:broker --log-level INFO --fs-discover

# 另一个可用的命令
# uv run taskiq worker app.core.taskiq_app:broker --log-level INFO --tasks-pattern "app/tasks/*.py"