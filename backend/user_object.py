import json
from typing import Awaitable, Callable

from aiobotocore.client import AioBaseClient

from utils.data_models import DatasetInfo, FitResult, ModelScore
from utils.logger import get_logger
from utils.settings import settings

logger = get_logger("backend")


async def get_user_datasets(
    user_id: str,
    s3_client_factory: Callable[[], Awaitable[AioBaseClient]],
) -> list[DatasetInfo]:
    """
    Получает список датасетов пользователя из S3.

    Args:
        user_id (str): id пользователя
        s3_client_factory (Callable[[], Awaitable[AioBaseClient]]): фабрика S3-клиентов

    Returns:
        datasets (list[DatasetInfo]): cписок датасетов
    """
    prefix: str = f"users/{user_id}/datasets/"
    datasets: list[DatasetInfo] = []

    async with await s3_client_factory() as s3:
        response: dict = await s3.list_objects_v2(
            Bucket=settings.s3_bucket, Prefix=prefix
        )

        if "Contents" not in response:
            return []

        for obj in response["Contents"]:
            key: str = obj["Key"]
            if not key.endswith(".parquet"):
                continue

            dataset_id: str = key.split("/")[-1].replace(".parquet", "")
            meta: str = await s3.head_object(Bucket=settings.s3_bucket, Key=key)
            original_name: str = meta.get("Metadata", {}).get(
                "original-filename", "unknown"
            )

            datasets.append(
                DatasetInfo(
                    data_id=dataset_id,
                    name=original_name,
                )
            )

    return datasets


async def get_user_models(
    user_id: str,
    data_id: str,
    s3_client_factory: Callable[[], Awaitable[AioBaseClient]],
) -> list[str]:
    """
    Получает список моделей пользователя для указанного датасета.

    Args:
        user_id (str): id пользователя
        data_id (str): id датасета
        s3_client_factory (Callable[[], Awaitable[AioBaseClient]]): фабрика S3-клиентов

    Returns:
        model_names (list[str]): cписок моделей
    """
    prefix: str = f"users/{user_id}/models/{data_id}/"
    model_names: list[str] = []

    async with await s3_client_factory() as s3:
        response: dict = await s3.list_objects_v2(
            Bucket=settings.s3_bucket, Prefix=prefix
        )

        if "Contents" not in response:
            return []

        for obj in response["Contents"]:
            key: str = obj["Key"]
            if key.endswith(".joblib"):
                model_name: str = key.split("/")[-2]
                model_names.append(model_name)

    return model_names


async def get_user_scores(
    user_id: str,
    data_id: str,
    s3_client_factory: Callable[[], Awaitable[AioBaseClient]],
) -> list[FitResult]:
    """
    Получает метрики моделей пользователя для указанного датасета.

    Args:
        user_id (str): id пользователя
        data_id  (str): id датасета
        s3_client_factory (Callable[[], Awaitable[AioBaseClient]]): фабрика S3-клиентов

    Returns:
        scores (list[FitResult]): cписок метрик моделей
    """
    prefix = f"users/{user_id}/models/{data_id}/"
    results: list[FitResult] = []

    async with await s3_client_factory() as s3:
        response: str = await s3.list_objects_v2(
            Bucket=settings.s3_bucket, Prefix=prefix
        )

        if "Contents" not in response:
            return []

        for obj in response["Contents"]:
            key: str = obj["Key"]
            if key.endswith("scores.json"):
                try:
                    res: dict = await s3.get_object(Bucket=settings.s3_bucket, Key=key)
                    data: bytes = await res["Body"].read()
                    scores_json: dict = json.loads(data.decode("utf-8"))

                    model_name: str = key.split("/")[-2]
                    scores: list = [
                        ModelScore(name=s["name"], value=float(s["value"]))
                        for s in scores_json.get("scores", [])
                    ]
                    results.append(FitResult(name=model_name, scores=scores))
                except Exception as e:
                    logger.warning(f"Не удалось загрузить {key}: {e}")

    return results
