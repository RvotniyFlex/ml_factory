import io
import json
import re
from typing import Awaitable, Callable

import joblib
import pandas as pd
from aiobotocore.client import AioBaseClient
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from backend.preprocessing import preprocess_dataset
from backend.utils.data_models import (
    DatasetPreprocessing,
    ElasticNetParams,
    FitResult,
    GBRHParams,
    ModelScore,
    RunConfig,
)
from backend.utils.logger import get_logger
from backend.utils.settings import settings

logger = get_logger("backend")


def train_regressor_task(
    df: pd.DataFrame, config: RunConfig
) -> tuple[
    ElasticNet | GradientBoostingRegressor, DatasetPreprocessing, FitResult, dict
]:
    """
    Обучает модель (ElasticNet или GradientBoostingRegressor) по RunConfig.

    Args:
        df (pd.DataFrame): данные с таргетом
        config (RunConfig): конфигурация предобработки и модели

    Returns:
        model (ElasticNet | GradientBoostingRegressor): обученная модель
        preprocessing_config (DatasetPreprocessing): конфигурация предобработки данных
        scores (FitResult): результат обучения с метриками
        transformers (dict): словарь преобразователей данных
    """

    df_processed, transformers = preprocess_dataset(
        df, config.preprocessing_config, transformers={}
    )
    target: str = config.preprocessing_config.target

    if target not in df_processed.columns:
        logger.error(f"Целевая переменная '{target}' не найдена в данных")
        raise ValueError(f"Целевая переменная '{target}' не найдена в данных")

    X: pd.DataFrame = df_processed.drop(columns=[target])
    y: pd.DataFrame = df_processed[target]

    model_class: str = config.ml_config.model_class
    params: ElasticNetParams | GBRHParams = config.ml_config.hyperparameters

    if model_class == "ElasticNet":
        model = ElasticNet(
            alpha=params.alpha, l1_ratio=params.l1_ratio, random_state=42
        )
    elif model_class == "GradientBoostingRegressor":
        model = GradientBoostingRegressor(
            learning_rate=params.learning_rate,
            max_depth=params.max_depth,
            n_estimators=params.n_estimators,
            random_state=42,
        )
    else:
        logger.error(f"Неизвестный класс модели: {model_class}")
        raise ValueError(f"Неизвестный класс модели: {model_class}")

    model.fit(X, y)
    y_pred: pd.Series = model.predict(X)

    safe_params = re.sub(
        r"[^a-zA-Z0-9]", "_", json.dumps(params.model_dump(), sort_keys=True)
    )
    model_name: str = f"{model_class}_{safe_params}"

    scores: list = [
        ModelScore(name="R2", value=float(r2_score(y, y_pred))),
        ModelScore(name="MSE", value=float(mean_squared_error(y, y_pred))),
        ModelScore(name="MAE", value=float(mean_absolute_error(y, y_pred))),
    ]

    return (
        model,
        config.preprocessing_config,
        FitResult(name=model_name, scores=scores),
        transformers,
    )


async def save_trained_model(
    model,
    preprocessing_config: DatasetPreprocessing,
    transformers: dict,
    scores: FitResult,
    user_id: str,
    data_id: str,
    model_name: str | None,
    s3_client_factory: Callable[[], Awaitable[AioBaseClient]],
) -> str | None:
    """
    Сохраняет обученную модель в формате joblib и загружает её в S3.

    Args:
        model: обученная модель sklearn
        preprocessing_config (dict): конфигурация предобработки данных
        transformers (dict): словарь преобразователей данных
        scores (dict): метрики модели
        user_id (str): идентификатор пользователя
        data_id (str): идентификатор набора данных
        model_name (str | None): имя модели (если не задано — генерируется UUID)
        s3_client_factory: фабрика S3-клиентов (из зависимостей FastAPI)

    Returns:
        s3_key (str | None): путь к модели в S3, None — если не удалось сохранить
    """
    try:
        key: str = f"users/{user_id}/models/{data_id}/{model_name}"
        buffer = io.BytesIO()
        joblib.dump(model, buffer)
        buffer.seek(0)

        async with await s3_client_factory() as s3:
            await s3.put_object(
                Bucket=settings.s3_bucket,
                Key=key + "/model.joblib",
                Body=buffer.getvalue(),
                ContentType="application/octet-stream",
            )

        async with await s3_client_factory() as s3:
            await s3.put_object(
                Bucket=settings.s3_bucket,
                Key=key + "/preprocessing.json",
                Body=json.dumps(
                    preprocessing_config.model_dump(), ensure_ascii=False, indent=2
                ).encode("utf-8"),
                ContentType="application/json",
            )

        async with await s3_client_factory() as s3:
            await s3.put_object(
                Bucket=settings.s3_bucket,
                Key=key + "/scores.json",
                Body=json.dumps(
                    scores.model_dump(), ensure_ascii=False, indent=2
                ).encode("utf-8"),
                ContentType="application/json",
            )

        buffer = io.BytesIO()
        joblib.dump(transformers, buffer)
        buffer.seek(0)
        async with await s3_client_factory() as s3:
            await s3.put_object(
                Bucket=settings.s3_bucket,
                Key=key + "/transformers.joblib",
                Body=buffer.getvalue(),
                ContentType="application/octet-stream",
            )

        logger.info(
            f"Объекты {model_name} пользователя {user_id} успешно сохранена в S3"
        )
        return key

    except Exception as e:
        logger.exception(f"Ошибка при сохранении модели пользователя {user_id}: {e}")
        return None
