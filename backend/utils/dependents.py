from typing import Callable, Awaitable
from aiobotocore.client import AioBaseClient
from fastapi import Request

def get_s3_client_factory(request: Request) -> Callable[[], Awaitable[AioBaseClient]]:
    """
    Вспомогательная функция для получения фабрики S3-клиентов.

    Args:
        request (Request): Объект запроса FastAPI.

    Returns:
        factory (Callable[[], Awaitable[AioBaseClient]]): Фабрика S3-клиентов
    """

    factory = request.app.state.s3_client_factory
    return factory