from contextlib import asynccontextmanager

import aioboto3
from botocore.exceptions import ClientError
from fastapi import FastAPI

from backend.routers import client, dataset_management, health, ml_management
from backend.s3_connector import s3_client_factory
from backend.utils.logger import get_logger, setup_logging
from backend.utils.settings import settings

setup_logging()
logger = get_logger("backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер для управления жизненным циклом приложения
    Пытаемся подключиться к S3 и создаем бакет, если его нет

    Args:
        app (FastAPI): Экземпляр приложения FastAPI

    """
    logger.info("Запуск приложения")
    session = aioboto3.Session()
    app.state.s3_client_factory = s3_client_factory(session)

    async with await app.state.s3_client_factory() as s3:
        try:
            await s3.head_bucket(Bucket=settings.s3_bucket)
            logger.info(f"S3 bucket '{settings.s3_bucket}' найден, подключение успешно")
        except ClientError as e:
            code: str = e.response["Error"]["Code"]
            if code == "404":
                await s3.create_bucket(Bucket=settings.s3_bucket)
                logger.info(
                    f"S3 bucket '{settings.s3_bucket}' не найден — создан автоматически"
                )
            else:
                logger.error(f"Ошибка клиента S3: {e}")
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")

    yield
    logger.info("Остановка приложения")

    del app.state.s3_client_factory
    logger.info("S3 соединение закрыто")


app = FastAPI(lifespan=lifespan)
app.include_router(health.router)
app.include_router(dataset_management.router)
app.include_router(ml_management.router)
app.include_router(client.router)
