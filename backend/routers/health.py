from fastapi import APIRouter, Depends, status, Query, Request
from botocore.exceptions import ClientError
from typing import Callable, Awaitable
from aiobotocore.client import AioBaseClient

from backend.utils.settings import settings

router = APIRouter(prefix="/health", tags=["Health"])

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


@router.get("/app", status_code=status.HTTP_200_OK)
async def health_app():
    """
    Проверка, что основное приложение живо.
    """
    return {"app": "ok"}

@router.get("/s3", status_code=status.HTTP_200_OK)
async def health_s3(
    s3_client_factory=Depends(get_s3_client_factory),
    bucket: str = Query(default=settings.s3_bucket, description="Имя бакета для проверки"),
    ):
    """
    Проверка доступности S3-хранилища.
    """
    result = {"bucket": bucket, "s3": None}

    try:
        async with (await s3_client_factory()) as s3:
            await s3.head_bucket(Bucket=bucket)
            result["s3"] = "ok"
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in "404":
            result["s3"] = "no-such-bucket"
        else:
            result["s3"] = f"client error: {code}"
    except Exception as e:
        result["s3"] = f"unknown error: {str(e)}"

    return result