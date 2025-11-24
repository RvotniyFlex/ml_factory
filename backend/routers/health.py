from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, Query, status

from utils.data_models import HealthCheckApp, HealthCheckS3
from utils.dependents import get_s3_client_factory
from utils.settings import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/app", status_code=status.HTTP_200_OK)
async def health_app() -> HealthCheckApp:
    """
    Проверка, что основное приложение живо.
    """
    return HealthCheckApp.model_validate({"app": "ok"})


@router.get("/s3", status_code=status.HTTP_200_OK)
async def health_s3(
    s3_client_factory=Depends(get_s3_client_factory),
    bucket: str = Query(
        default=settings.s3_bucket, description="Имя бакета для проверки"
    ),
) -> HealthCheckS3:
    """
    Проверка доступности S3-хранилища.
    """
    result: dict = {"bucket": bucket, "s3": None}

    try:
        async with await s3_client_factory() as s3:
            await s3.head_bucket(Bucket=bucket)
            result["s3"] = "ok"
    except ClientError as e:
        code: str = e.response["Error"]["Code"]
        if code == "404":
            result["s3"] = "no-such-bucket"
        else:
            result["s3"] = f"client error: {code}"
    except Exception as e:
        result["s3"] = f"unknown error: {str(e)}"

    return HealthCheckS3.model_validate(result)
