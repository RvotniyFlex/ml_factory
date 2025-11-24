from typing import Awaitable, Callable

import aioboto3
from aiobotocore.client import AioBaseClient
from botocore.config import Config

from utils.settings import settings


def s3_client_factory(
    session: aioboto3.Session,
) -> Callable[[], Awaitable[AioBaseClient]]:
    """
    Создание кратковременных клиентов для S3

    Args:
        session (aioboto3.Session): сессия S3 для создания клиентов

    Returns:
        client (Awaitable):  асинхронная функция, создающая S3-клиента при вызове
    """
    cfg: Config = Config(
        region_name=settings.s3_region,
        retries={"max_attempts": settings.s3_max_attempts, "mode": "standard"},
        connect_timeout=settings.s3_connect_timeout,
        read_timeout=settings.s3_read_timeout,
        max_pool_connections=settings.s3_max_pool,
    )

    async def _client() -> AioBaseClient:
        """
        Функция создания клиента

        Returns:
            client (AioBaseClient):  клиент S3 для запросов
        """
        return session.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=cfg,
        )

    return _client
