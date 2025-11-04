import asyncio
import io
import json

import aioboto3
import grpc
import joblib
import numpy as np
import pandas as pd
from botocore.exceptions import ClientError

from backend.dataset_registry import (
    delete_file,
    get_storage_usage_mb,
    load_dataframe,
    upload_file,
)

# ===== gRPC контракты =====
from backend.grpc.contracts import contracts_pb2, contracts_pb2_grpc
from backend.preprocessing import preprocess_dataset
from backend.s3_connector import s3_client_factory
from backend.training import save_trained_model, train_regressor_task
from backend.user_object import (
    get_user_datasets,
    get_user_models,
    get_user_scores,
)
from backend.utils.data_models import DatasetPreprocessing, RunConfig
from backend.utils.logger import get_logger

# ===== Импорты внутренних модулей =====
from backend.utils.settings import settings

# ===== Настройки =====
logger = get_logger("grpc_server")
session = aioboto3.Session()
s3_client_factory = s3_client_factory(session)

# ============================================================
#                        СЕРВИСЫ
# ============================================================


# ---------- Health ----------
class HealthService(contracts_pb2_grpc.HealthServiceServicer):
    async def CheckApp(self, request, context):
        """Проверка, что приложение живо"""
        return contracts_pb2.HealthResponse(app="ok")

    async def CheckS3(self, request, context):
        """Проверка доступности S3"""
        bucket = request.bucket or settings.s3_bucket
        try:
            async with await s3_client_factory() as s3:
                await s3.head_bucket(Bucket=bucket)
            return contracts_pb2.HealthResponse(app="ok", s3="ok", bucket=bucket)
        except ClientError as e:
            code = e.response["Error"]["Code"]
            return contracts_pb2.HealthResponse(
                app="ok", s3=f"error: {code}", bucket=bucket
            )
        except Exception as e:
            return contracts_pb2.HealthResponse(
                app="ok", s3=f"unknown error: {str(e)}", bucket=bucket
            )


# ---------- User Storage ----------
class UserStorageService(contracts_pb2_grpc.UserStorageServiceServicer):
    async def ListDatasets(self, request, context):
        try:
            datasets = await get_user_datasets(request.user_id, s3_client_factory)
            response = contracts_pb2.DatasetsResponse(user_id=request.user_id)
            for ds in datasets:
                response.datasets.add(data_id=ds.data_id, name=ds.name)
            return response
        except Exception as e:
            logger.exception(e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return contracts_pb2.DatasetsResponse(user_id=request.user_id)

    async def ListModels(self, request, context):
        try:
            models = await get_user_models(
                request.user_id, request.data_id, s3_client_factory
            )
            return contracts_pb2.ModelsResponse(
                user_id=request.user_id, data_id=request.data_id, models=models
            )
        except Exception as e:
            logger.exception(e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return contracts_pb2.ModelsResponse(
                user_id=request.user_id, data_id=request.data_id
            )

    async def ListScores(self, request, context):
        try:
            scores = await get_user_scores(
                request.user_id, request.data_id, s3_client_factory
            )
            resp = contracts_pb2.ScoresResponse(
                user_id=request.user_id, data_id=request.data_id
            )
            for fit in scores:
                fit_msg = resp.scores.add(name=fit.name)
                for s in fit.scores:
                    fit_msg.scores.add(name=s.name, value=s.value)
            return resp
        except Exception as e:
            logger.exception(e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return contracts_pb2.ScoresResponse(
                user_id=request.user_id, data_id=request.data_id
            )


# ---------- Dataset Registry ----------
class DatasetRegistryService(contracts_pb2_grpc.DatasetRegistryServiceServicer):
    async def GetUsage(self, request, context):
        try:
            usage = await get_storage_usage_mb(request.user_id, s3_client_factory)
            return contracts_pb2.UsageResponse(
                user_id=request.user_id, usage_mb=round(usage or 0.0, 2)
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return contracts_pb2.UsageResponse(user_id=request.user_id)

    async def UploadFile(self, request, context):
        try:
            filename = request.filename.lower()
            file_bytes = request.file_bytes

            # читаем файл в DataFrame
            if filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(file_bytes))
            elif filename.endswith(".parquet"):
                df = pd.read_parquet(io.BytesIO(file_bytes), engine="pyarrow")
            elif filename.endswith(".xlsx"):
                df = pd.read_excel(io.BytesIO(file_bytes))
            else:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Поддерживаются только .csv, .xlsx, .parquet")
                return contracts_pb2.UploadResponse(
                    user_id=request.user_id, filename=request.filename
                )

            # сохраняем parquet
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False, engine="pyarrow")
            buffer.seek(0)

            data_id = await upload_file(
                user_id=request.user_id,
                file_bytes=buffer.getvalue(),
                file_name=request.filename,
                s3_client_factory=s3_client_factory,
            )

            if data_id is None:
                context.set_code(grpc.StatusCode.RESOURCE_EXHAUSTED)
                context.set_details("Превышен лимит хранилища")
                return contracts_pb2.UploadResponse(user_id=request.user_id)

            return contracts_pb2.UploadResponse(
                user_id=request.user_id,
                data_id=data_id,
                filename=request.filename,
            )

        except Exception as e:
            logger.exception(e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return contracts_pb2.UploadResponse(user_id=request.user_id)

    async def DeleteFile(self, request, context):
        try:
            deleted = await delete_file(
                request.user_id, request.data_id, s3_client_factory
            )
            status = "deleted" if deleted else "not_found"
            return contracts_pb2.DeleteResponse(
                user_id=request.user_id, data_id=request.data_id, status=status
            )
        except Exception as e:
            logger.exception(e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return contracts_pb2.DeleteResponse(user_id=request.user_id)

    async def LoadSample(self, request, context):
        try:
            df = await load_dataframe(
                request.user_id, request.data_id, s3_client_factory
            )
            if df is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Файл не найден")
                return contracts_pb2.LoadResponse(user_id=request.user_id)

            df = df.replace({np.nan: None, np.inf: None, -np.inf: None})
            sample = df.head(5).to_dict(orient="records")

            return contracts_pb2.LoadResponse(
                user_id=request.user_id,
                data_id=request.data_id,
                columns=list(df.columns),
                rows=len(df),
                sample_json=json.dumps(sample, ensure_ascii=False),
            )
        except Exception as e:
            logger.exception(e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return contracts_pb2.LoadResponse(user_id=request.user_id)


# ---------- Model Service ----------
class ModelService(contracts_pb2_grpc.ModelServiceServicer):
    async def Train(self, request, context):
        try:
            run_config = RunConfig(**json.loads(request.run_config_json))
            df = await load_dataframe(
                request.user_id, request.data_id, s3_client_factory
            )
            if df is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Датасет не найден")
                return contracts_pb2.TrainResponse()

            model, preprocessing_config, fit_result = train_regressor_task(
                df, run_config
            )
            model_name = fit_result.name
            s3_key = await save_trained_model(
                model=model,
                preprocessing_config=preprocessing_config,
                scores=fit_result,
                user_id=request.user_id,
                data_id=request.data_id,
                model_name=model_name,
                s3_client_factory=s3_client_factory,
            )

            return contracts_pb2.TrainResponse(
                user_id=request.user_id,
                data_id=request.data_id,
                model_name=model_name,
                s3_key=s3_key or "",
                metrics_json=json.dumps([s.model_dump() for s in fit_result.scores]),
            )
        except Exception as e:
            logger.exception(e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return contracts_pb2.TrainResponse()

    async def Predict(self, request, context):
        model_key = f"users/{request.user_id}/models/{request.data_id}/{request.model_name}/model.joblib"
        preproc_key = f"users/{request.user_id}/models/{request.data_id}/{request.model_name}/preprocessing.json"

        try:
            async with await s3_client_factory() as s3:
                preproc_obj = await s3.get_object(
                    Bucket=settings.s3_bucket, Key=preproc_key
                )
                preproc_json = await preproc_obj["Body"].read()
                preprocessing_config = DatasetPreprocessing(**json.loads(preproc_json))

                model_obj = await s3.get_object(
                    Bucket=settings.s3_bucket, Key=model_key
                )
                model_data = await model_obj["Body"].read()
                model = joblib.load(io.BytesIO(model_data))

            df = pd.DataFrame(json.loads(request.input_data_json))
            df_preprocessed = preprocess_dataset(df, preprocessing_config)

            print(df_preprocessed)
            preds = model.predict(df_preprocessed)

            return contracts_pb2.PredictResponse(predictions=[float(p) for p in preds])
        except Exception as e:
            logger.exception(e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return contracts_pb2.PredictResponse()

    async def Delete(self, request, context):
        prefix = (
            f"users/{request.user_id}/models/{request.data_id}/{request.model_name}/"
        )
        try:
            async with await s3_client_factory() as s3:
                response = await s3.list_objects_v2(
                    Bucket=settings.s3_bucket, Prefix=prefix
                )
                if "Contents" not in response:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    return contracts_pb2.ModelDeleteResponse(
                        user_id=request.user_id,
                        data_id=request.data_id,
                        model_name=request.model_name,
                        status="not_found",
                    )
                delete_list = [{"Key": obj["Key"]} for obj in response["Contents"]]
                await s3.delete_objects(
                    Bucket=settings.s3_bucket, Delete={"Objects": delete_list}
                )
            return contracts_pb2.ModelDeleteResponse(
                user_id=request.user_id,
                data_id=request.data_id,
                model_name=request.model_name,
                status="deleted",
            )
        except Exception as e:
            logger.exception(e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return contracts_pb2.ModelDeleteResponse()


# ============================================================
#                        SERVER RUNNER
# ============================================================
async def serve():
    server = grpc.aio.server()
    contracts_pb2_grpc.add_HealthServiceServicer_to_server(HealthService(), server)
    contracts_pb2_grpc.add_UserStorageServiceServicer_to_server(
        UserStorageService(), server
    )
    contracts_pb2_grpc.add_DatasetRegistryServiceServicer_to_server(
        DatasetRegistryService(), server
    )
    contracts_pb2_grpc.add_ModelServiceServicer_to_server(ModelService(), server)

    server.add_insecure_port("[::]:50051")
    logger.info("🚀 gRPC MLFactory server started on port 50051")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
