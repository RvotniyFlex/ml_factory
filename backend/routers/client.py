from typing import Awaitable, Callable

from aiobotocore.client import AioBaseClient
from fastapi import APIRouter, Depends, HTTPException, Path, status

from backend.user_object import (
    get_user_datasets,
    get_user_models,
    get_user_scores,
)
from utils.data_models import UserDatasets, UserModels, UserScores
from utils.dependents import get_s3_client_factory
from utils.logger import get_logger

logger = get_logger("backend")

router = APIRouter(prefix="/user/storage", tags=["User Storage"])


@router.get("/datasets/{user_id}", status_code=status.HTTP_200_OK)
async def list_user_datasets(
    user_id: str = Path(description="Id пользователя"),
    s3_client_factory: Callable[[], Awaitable[AioBaseClient]] = Depends(
        get_s3_client_factory
    ),
) -> UserDatasets:
    """
    Возвращает список всех датасетов пользователя.
    """
    try:
        datasets = await get_user_datasets(user_id, s3_client_factory)
        if not datasets:
            return UserDatasets.model_validate({"user_id": user_id, "datasets": []})
        return UserDatasets.model_validate({"user_id": user_id, "datasets": datasets})
    except Exception as e:
        logger.exception(f"Ошибка при получении датасетов пользователя {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Ошибка при получении списка датасетов."
        )


@router.get("/models/{user_id}/{data_id}", status_code=status.HTTP_200_OK)
async def list_user_models(
    user_id: str = Path(description="Id пользователя"),
    data_id: str = Path(description="Id датасета"),
    s3_client_factory: Callable[[], Awaitable[AioBaseClient]] = Depends(
        get_s3_client_factory
    ),
) -> UserModels:
    """
    Возвращает список всех моделей пользователя для заданного датасета.
    """
    try:
        models = await get_user_models(user_id, data_id, s3_client_factory)
        if not models:
            return UserModels.model_validate(
                {"user_id": user_id, "data_id": data_id, "models": []}
            )
        return UserModels.model_validate(
            {"user_id": user_id, "data_id": data_id, "models": models}
        )
    except Exception as e:
        logger.exception(f"Ошибка при получении моделей пользователя {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Ошибка при получении списка моделей."
        )


@router.get("/scores/{user_id}/{data_id}", status_code=status.HTTP_200_OK)
async def list_user_scores(
    user_id: str = Path(description="Id пользователя"),
    data_id: str = Path(description="Id датасета"),
    s3_client_factory: Callable[[], Awaitable[AioBaseClient]] = Depends(
        get_s3_client_factory
    ),
) -> UserScores:
    """
    Возвращает список метрик моделей пользователя для заданного датасета.
    """
    try:
        scores = await get_user_scores(user_id, data_id, s3_client_factory)
        if not scores:
            return UserScores.model_validate(
                {"user_id": user_id, "data_id": data_id, "scores": []}
            )
        return UserScores.model_validate(
            {"user_id": user_id, "data_id": data_id, "scores": scores}
        )
    except Exception as e:
        logger.exception(
            f"Ошибка при получении метрик моделей пользователя {user_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail="Ошибка при получении метрик моделей."
        )
