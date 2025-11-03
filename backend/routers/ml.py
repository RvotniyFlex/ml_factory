import io
import json
from typing import Awaitable, Callable

import joblib
import pandas as pd
from aiobotocore.client import AioBaseClient
from fastapi import APIRouter, Depends, HTTPException, status

from backend.dataset_registry import load_dataframe
from backend.preprocessing import preprocess_dataset
from backend.training import save_trained_model, train_regressor_task
from backend.utils.data_models import DatasetPreprocessing, RunConfig
from backend.utils.dependents import get_s3_client_factory
from backend.utils.logger import get_logger
from backend.utils.settings import settings

router = APIRouter(prefix="/model", tags=["Model Training"])
logger = get_logger("backend")


@router.post("/train/{user_id}/{data_id}", status_code=status.HTTP_200_OK)
async def train_model_endpoint(
    user_id: str,
    data_id: str,
    run_config: RunConfig,
    s3_client_factory: Callable[[], Awaitable[AioBaseClient]] = Depends(
        get_s3_client_factory
    ),
):
    """
    Обучает модель по RunConfig, сохраняет её в S3 и возвращает метрики и путь.
    """
    try:
        df = await load_dataframe(user_id, data_id, s3_client_factory)
        if df is None:
            raise HTTPException(status_code=404, detail="Датасет не найден")

        model, preprocessing_config, fit_result = train_regressor_task(df, run_config)

        model_name = fit_result.name
        s3_key = await save_trained_model(
            model=model,
            preprocessing_config=preprocessing_config,
            scores=fit_result,
            user_id=user_id,
            data_id=data_id,
            model_name=model_name,
            s3_client_factory=s3_client_factory,
        )

        if not s3_key:
            raise HTTPException(status_code=500, detail="Не удалось сохранить модель")

        return {
            "user_id": user_id,
            "data_id": data_id,
            "model_name": model_name,
            "s3_key": s3_key,
            "metrics": [s.model_dump() for s in fit_result.scores],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Ошибка при обучении модели пользователя {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/predict/{user_id}/{data_id}/{model_name}",
    status_code=status.HTTP_200_OK,
)
async def predict_endpoint(
    user_id: str,
    data_id: str,
    model_name: str,
    input_data: list[dict],
    s3_client_factory: Callable[[], Awaitable[AioBaseClient]] = Depends(
        get_s3_client_factory
    ),
):
    """
    Делает предсказание по обученной модели пользователя.
    Ожидает JSON: [{"feature1": val1, "feature2": val2, ...}, ...]
    """
    model_key = f"users/{user_id}/models/{data_id}/{model_name}/model.joblib"
    preprocessing_key = (
        f"users/{user_id}/models/{data_id}/{model_name}/preprocessing.json"
    )

    try:
        async with await s3_client_factory() as s3:
            try:
                preproc_obj = await s3.get_object(
                    Bucket=settings.s3_bucket, Key=preprocessing_key
                )
                preproc_data = await preproc_obj["Body"].read()
                preprocessing_dict = json.loads(preproc_data.decode("utf-8"))
                preprocessing_config = DatasetPreprocessing(**preprocessing_dict)
                logger.info(f"Препроцессинг {preprocessing_key} успешно загружен.")
            except s3.exceptions.NoSuchKey:
                raise HTTPException(
                    status_code=404, detail="Файл preprocessing.json не найден."
                )
            except Exception as e:
                logger.exception(f"Ошибка при загрузке preprocessing.json: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Ошибка при чтении конфигурации препроцессинга.",
                )

            try:
                model_obj = await s3.get_object(
                    Bucket=settings.s3_bucket, Key=model_key
                )
                model_bytes = await model_obj["Body"].read()
                model = joblib.load(io.BytesIO(model_bytes))
                logger.info(f"Модель {model_name} успешно загружена из S3.")
            except s3.exceptions.NoSuchKey:
                raise HTTPException(status_code=404, detail="Модель не найдена.")
            except Exception as e:
                logger.exception(f"Ошибка при загрузке модели {model_name}: {e}")
                raise HTTPException(
                    status_code=500, detail="Ошибка при загрузке модели."
                )

        try:
            df = pd.DataFrame(input_data)
            df_preprocessed = preprocess_dataset(df, preprocessing_config)
            preds = model.predict(df_preprocessed)
            logger.info(f"Предсказание выполнено успешно. ({len(preds)} записей)")
            return {"predictions": preds.tolist()}
        except Exception as e:
            logger.exception(f"Ошибка при предсказании: {e}")
            raise HTTPException(
                status_code=500, detail="Ошибка при обработке данных для предсказания."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"Ошибка при инференсе модели {model_name} пользователя {user_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail="Внутренняя ошибка сервера при предсказании."
        )


@router.delete(
    "/delete/{user_id}/{data_id}/{model_name}", status_code=status.HTTP_200_OK
)
async def delete_model_endpoint(
    user_id: str,
    data_id: str,
    model_name: str,
    s3_client_factory: Callable[[], Awaitable[AioBaseClient]] = Depends(
        get_s3_client_factory
    ),
):
    """
    Удаляет сохранённую модель из S3.
    """
    key = f"models/{user_id}/{data_id}/{model_name}.joblib"

    try:
        async with await s3_client_factory() as s3:
            response = await s3.list_objects_v2(Bucket=settings.s3_bucket, Prefix=key)
            if "Contents" not in response or len(response["Contents"]) == 0:
                raise HTTPException(
                    status_code=404, detail=f"Модель {model_name} не найдена"
                )
            await s3.delete_object(Bucket=settings.s3_bucket, Key=key)

        logger.info(f"Модель {model_name} пользователя {user_id} удалена из S3")
        return {
            "user_id": user_id,
            "data_id": data_id,
            "model_name": model_name,
            "status": "deleted",
        }
    except Exception as e:
        logger.exception(
            f"Ошибка при удалении модели {model_name} пользователя {user_id}: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))
