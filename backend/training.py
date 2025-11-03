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
) -> tuple[ElasticNet | GradientBoostingRegressor, FitResult]:
    """
    Обучает модель (ElasticNet или GradientBoostingRegressor) по RunConfig.

    Args:
        df (pd.DataFrame): данные с таргетом
        config (RunConfig): конфигурация предобработки и модели

    Returns:
        model (ElasticNet | GradientBoostingRegressor): обученная модель
        FitResult: результат обучения с метриками
    """

    df_processed: pd.DataFrame = preprocess_dataset(df, config.preprocessing_config)
    target: str = config.ml_config.target

    if target not in df_processed.columns:
        logger.error(f"Целевая переменная '{target}' не найдена в данных")
        return FitResult(name="No target", scores=[])

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
        return FitResult(name="No model class", scores=[])

    model.fit(X, y)
    y_pred: pd.Series = model.predict(X)

    safe_params = re.sub(
        r"[^a-zA-Z0-9]", "_", json.dumps(params.model_dump(), sort_keys=True)
    )
    model_name = f"{model_class}_{safe_params[:40]}.joblib"

    scores = [
        ModelScore(name="R2", value=float(r2_score(y, y_pred))),
        ModelScore(name="MSE", value=float(mean_squared_error(y, y_pred))),
        ModelScore(name="MAE", value=float(mean_absolute_error(y, y_pred))),
    ]

    return model, FitResult(name=model_name, scores=scores)


async def save_trained_model(
    model,
    user_id: str,
    data_id: str,
    model_name: str | None,
    s3_client_factory: Callable[[], Awaitable[AioBaseClient]],
) -> str | None:
    """
    Сохраняет обученную модель в формате joblib и загружает её в S3.

    Args:
        model: обученная модель sklearn
        user_id (str): идентификатор пользователя
        data_id (str): идентификатор набора данных
        model_name (str | None): имя модели (если не задано — генерируется UUID)
        s3_client_factory: фабрика S3-клиентов (из зависимостей FastAPI)

    Returns:
        s3_key (str | None): путь к модели в S3, None — если не удалось сохранить
    """
    try:
        key = f"models/{user_id}/{data_id}/{model_name}.joblib"

        buffer = io.BytesIO()
        joblib.dump(model, buffer)
        buffer.seek(0)

        async with await s3_client_factory() as s3:
            await s3.put_object(
                Bucket=settings.s3_bucket,
                Key=key,
                Body=buffer.getvalue(),
                ContentType="application/octet-stream",
            )

        logger.info(
            f"Модель {model_name} пользователя {user_id} успешно сохранена в S3 ({key})"
        )
        return key

    except Exception as e:
        logger.exception(f"Ошибка при сохранении модели пользователя {user_id}: {e}")
        return None
