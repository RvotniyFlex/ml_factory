import io
import uuid
from typing import Awaitable, Callable

import pandas as pd
from aiobotocore.client import AioBaseClient

from backend.utils.logger import get_logger
from backend.utils.settings import settings

MAX_STORAGE_MB = 200

logger = get_logger("backend")


async def get_storage_usage_mb(
    user_id: str, s3_client_factory: Callable[[], Awaitable[AioBaseClient]]
) -> float | None:
    """
    Возвращает сколько МБ занимает папка пользователя на S3.
    None — если у пользователя нет файлов.

    Args:
        user_id (str): id пользователя
        s3_client_factory (Callable[[], Awaitable[AioBaseClient]]): Фабрика S3-клиентов

    Returns:
        total_memory: (float | None): размер папки пользователя в МБ или None, если папка пустая
    """
    prefix = f"users/{user_id}/"
    total_bytes: float = 0.0

    async with await s3_client_factory() as s3:
        response: dict = await s3.list_objects_v2(
            Bucket=settings.s3_bucket, Prefix=prefix
        )

        if "Contents" not in response:
            return None

        for obj in response["Contents"]:
            total_bytes += obj["Size"]

    return total_bytes / (1024 * 1024)


async def upload_file(
    user_id: str,
    file_bytes: bytes,
    file_name: str,
    s3_client_factory: Callable[[], Awaitable[AioBaseClient]],
) -> str | None:
    """
    Загрузить файл в хранилище с данными в формате parquet.
    Предварительно проходится проверка, что юзер не заполнил все хранилище больше чем на 200МБ

    Args:
        user_id (str): id пользователя
        file_bytes (str): файл в виде байтов
        file_name (str): имя файла
        s3_client_factory (Callable[[], Awaitable[AioBaseClient]]): Фабрика S3-клиентов

    Returns:
        data_id (str): id файла в хранилище. None - если не удалось загрузить файл
    """
    current_usage: float = await get_storage_usage_mb(user_id, s3_client_factory)
    current_usage: float = current_usage or 0.0

    file_size_mb: float = len(file_bytes) / (1024 * 1024)
    if current_usage + file_size_mb > MAX_STORAGE_MB:
        logger.info(
            f"Пользователь {user_id} превышает квоту ({round(current_usage, 2)} + {round(file_size_mb, 2)} > {MAX_STORAGE_MB} MB)"
        )
        return None

    data_id: str = str(uuid.uuid4())
    key: str = f"users/{user_id}/{data_id}.parquet"

    async with await s3_client_factory() as s3:
        await s3.put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=file_bytes,
            ContentType="application/octet-stream",
            Metadata={
                "original-filename": file_name,
            },
        )
    logger.info(
        f"Пользователь {user_id} загрузил файл {file_name} в хранилище с id {data_id}"
    )
    return data_id


async def delete_file(
    user_id: str,
    data_id: str,
    s3_client_factory: Callable[[], Awaitable[AioBaseClient]],
) -> str | None:
    """
    Удаляет файл по user_id и data_id из S3.
    Возвращает data_id при успехе или None.

    Args:
        user_id (str): id пользователя
        data_id (str): id файла в хранилище
        s3_client_factory (Callable[[], Awaitable[AioBaseClient]]): Фабрика S3-клиентов

    Returns:
        data_id (str | None): id файла в хранилище или None, если файл не найден
    """
    prefix: str = f"users/{user_id}/{data_id}"

    async with await s3_client_factory() as s3:
        response: dict = await s3.list_objects_v2(
            Bucket=settings.s3_bucket, Prefix=prefix
        )

        if "Contents" not in response or len(response["Contents"]) == 0:
            logger.info(
                f"У пользователя {user_id} не найдено файла {data_id}, не удалось удалить"
            )
            return None

        key: str = response["Contents"][0]["Key"]
        await s3.delete_object(Bucket=settings.s3_bucket, Key=key)
        logger.info(f"Пользователь {user_id} удалил файл {data_id}")

    return data_id


async def load_dataframe(
    user_id: str,
    data_id: str,
    s3_client_factory: Callable[[], Awaitable[AioBaseClient]],
) -> pd.DataFrame | None:
    """
    Загружает parquet-файл из хранилища S3 и возвращает DataFrame.

    Args:
        user_id (str): id пользователя
        data_id (str): id файла в хранилище
        s3_client_factory (Callable[[], Awaitable[AioBaseClient]]): Фабрика S3-клиентов

    Returns:
        data (pd.DataFrame | None): DataFrame из файла или None, если файл не найден
    """
    prefix: str = f"users/{user_id}/{data_id}.parquet"

    async with await s3_client_factory() as s3:
        response: dict = await s3.list_objects_v2(
            Bucket=settings.s3_bucket, Prefix=prefix
        )

        if "Contents" not in response or len(response["Contents"]) == 0:
            return None

        key: str = response["Contents"][0]["Key"]
        obj: dict = await s3.get_object(Bucket=settings.s3_bucket, Key=key)
        data: bytes = await obj["Body"].read()

    return pd.read_parquet(io.BytesIO(data))
