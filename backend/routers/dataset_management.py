import io

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile, status

from backend.dataset_registry import (
    delete_file,
    get_storage_usage_mb,
    load_dataframe,
    upload_file,
)
from backend.utils.data_models import (
    DatasetDescription,
    DeleteDatasetResponse,
    UploadDatasetResponse,
    UserStorage,
)
from backend.utils.dependents import get_s3_client_factory

router = APIRouter(
    prefix="/dataset_management",
    tags=["Datasets"],
)


@router.get("/usage/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_storage_usage(
    user_id: str = Path(description="Id пользователя"),
    s3_client_factory=Depends(get_s3_client_factory),
) -> UserStorage:
    """
    Получить объём хранилища, занимаемый пользователем.
    """
    usage = await get_storage_usage_mb(user_id, s3_client_factory)
    if usage is None:
        return UserStorage.model_validate({"user_id": user_id, "usage_mb": 0.0})
    return UserStorage.model_validate({"user_id": user_id, "usage_mb": round(usage, 2)})


@router.post("/upload/{user_id}", status_code=status.HTTP_200_OK)
async def upload_user_file(
    user_id: str = Path(description="Id пользователя"),
    uploaded_file: UploadFile = File(...),
    s3_client_factory=Depends(get_s3_client_factory),
) -> UploadDatasetResponse:
    """
    Загрузить parquet-файл пользователя в S3.
    """

    try:
        contents = await uploaded_file.read()
        filename = uploaded_file.filename.lower()

        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        elif filename.endswith(".parquet"):
            df = pd.read_parquet(io.BytesIO(contents), engine="pyarrow")
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Поддерживаются только файлы .csv, .xlsx и .parquet",
            )

        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, index=False, engine="pyarrow")
        parquet_buffer.seek(0)

        data_id = await upload_file(
            user_id=user_id,
            file_bytes=parquet_buffer.getvalue(),
            file_name=uploaded_file.filename,
            s3_client_factory=s3_client_factory,
        )

        if data_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Пользователь {user_id} превысил квоту в 200 МБ",
            )

        return UploadDatasetResponse.model_validate(
            {
                "user_id": user_id,
                "data_id": data_id,
                "filename": uploaded_file.filename,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при загрузке файла пользователем {user_id}: {str(e)}",
        )


@router.delete("/delete/{user_id}/{data_id}", status_code=status.HTTP_200_OK)
async def delete_user_file(
    user_id: str = Path(description="Id пользователя"),
    data_id: str = Path(description="Id датасета"),
    s3_client_factory=Depends(get_s3_client_factory),
) -> DeleteDatasetResponse:
    """
    Удалить файл пользователя по ID.
    """
    deleted = await delete_file(user_id, data_id, s3_client_factory)
    if deleted is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Файл {data_id} пользователя {user_id} не найден",
        )
    return DeleteDatasetResponse.model_validate(
        {"user_id": user_id, "data_id": data_id}
    )


@router.get("/load/{user_id}/{data_id}", status_code=status.HTTP_200_OK)
async def load_user_dataframe(
    user_id: str = Path(description="Id пользователя"),
    data_id: str = Path(description="Id датасета"),
    s3_client_factory=Depends(get_s3_client_factory),
) -> DatasetDescription:
    """
    Семл данных пользователя и информация о данных.
    """
    df: pd.DataFrame | None = await load_dataframe(user_id, data_id, s3_client_factory)

    if df is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Файл {data_id} пользователя {user_id} не найден",
        )

    col_type = {}
    for col in df.columns:
        data_type = "categorical" if df[col].dtype == "object" else "numerical"
        col_type[col] = data_type

    df: pd.DataFrame = df.replace({np.nan: None, np.inf: None, -np.inf: None})
    na_columns: dict = df.isna().sum().to_dict()

    sample = df.head(5).to_dict(orient="records")

    return DatasetDescription.model_validate(
        {
            "user_id": user_id,
            "data_id": data_id,
            "columns": list(df.columns),
            "na_columns": na_columns,
            "col_type": col_type,
            "rows": len(df),
            "sample": sample,
        }
    )
