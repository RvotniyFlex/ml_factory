from typing import Literal, Optional

from pydantic import BaseModel, Field


class GBRHParams(BaseModel):
    learning_rate: float = Field(description="Шаг градиента")
    max_depth: int = Field(description="Максимальная глубина дерева")
    n_estimators: int = Field(description="Количество деревьев")


class ElasticNetParams(BaseModel):
    alpha: float = Field(description="Коэффициент регуляризации")
    l1_ratio: float = Field(description="Соотношение между L1 и L2 регуляризацией")


class ModelDescription(BaseModel):
    name: Literal["ElasticNet", "GradientBoostingRegressor"] = Field(
        description="Название модели"
    )
    hyperparameters: GBRHParams | ElasticNetParams = Field(
        description="Гиперпараметры модели"
    )


class AvailableModels(BaseModel):
    models: list[ModelDescription] = Field(description="Список доступных моделей")


class ModelConfig(BaseModel):
    hyperparameters: GBRHParams | ElasticNetParams = Field(
        description="Гиперпараметры модели"
    )
    model_class: Literal["GradientBoostingRegressor", "ElasticNet"] = Field(
        description="Класс модели"
    )


class ColumnPreprocessing(BaseModel):
    name: str = Field(description="Название колонки")
    data_type: Literal["numerical", "categorical"] = Field(description="Тип данных")
    fillna_policy: Optional[Literal["mean", "mode"]] = Field(
        description="Политика заполнения пропусков"
    )
    transformations: Optional[
        Literal["StandardScaler", "MinMaxScaler", "LabelEncoder", "OneHotEncoder"]
    ] = Field(description="Преобразования данных")
    drop: bool = Field(description="Удалить колонку")


class DatasetPreprocessing(BaseModel):
    dataset_preprocessing: list[ColumnPreprocessing] = Field(
        description="Список преобразований данных"
    )
    target: str = Field(description="Целевая переменная")


class RunConfig(BaseModel):
    preprocessing_config: DatasetPreprocessing = Field(
        description="Конфигурация предобработки данных"
    )
    ml_config: ModelConfig = Field(description="Конфигурация модели")


class ModelScore(BaseModel):
    name: Literal["R2", "MSE", "MAE"] = Field(description="Название метрики")
    value: float = Field(description="Значение метрики")


class FitResult(BaseModel):
    name: str = Field(description="Название модели")
    scores: list[ModelScore] = Field(description="Список метрик модели")


class DatasetInfo(BaseModel):
    name: str = Field(description="Название датасета")
    data_id: str = Field(description="id датасета")


class UserStorage(BaseModel):
    user_id: str = Field(description="Идентификатор пользователя")
    usage_mb: float = Field(description="Использование хранилища в МБ")


class UploadDatasetResponse(BaseModel):
    user_id: str = Field(description="Идентификатор пользователя")
    data_id: str = Field(description="Идентификатор датасета")
    filename: str = Field(description="Имя файла")


class DeleteDatasetResponse(BaseModel):
    user_id: str = Field(description="Идентификатор пользователя")
    data_id: str = Field(description="Идентификатор датасета")


class DatasetDescription(BaseModel):
    user_id: str = Field(description="Идентификатор пользователя")
    data_id: str = Field(description="Идентификатор датасета")
    columns: list[str] = Field(description="Список колонок")
    na_columns: dict[str, int] = Field(description="Количество пропусков")
    col_type: dict[str, Literal["categorical", "numerical"]] = Field(
        description="Тип колонок"
    )
    rows: int = Field(description="Количество строк")
    sample: list[dict] = Field(description="Пример данных")


class UserDatasets(BaseModel):
    user_id: str = Field(description="Идентификатор пользователя")
    datasets: list[DatasetInfo] = Field(description="Список датасетов пользователя")


class UserModels(BaseModel):
    user_id: str = Field(description="Идентификатор пользователя")
    data_id: str = Field(description="Идентификатор датасета")
    models: list[str] = Field(description="Список моделей")


class UserScores(BaseModel):
    user_id: str = Field(description="Идентификатор пользователя")
    data_id: str = Field(description="Идентификатор датасета")
    scores: list[FitResult] = Field(description="Список результатов обучения")


class HealthCheckApp(BaseModel):
    app: Literal["ok"] = Field(description="Статус приложения")


class HealthCheckS3(BaseModel):
    s3: str = Field(description="Статус S3")
    bucket: str = Field(description="Имя бакета")


class FittedModel(BaseModel):
    user_id: str = Field(description="Идентификатор пользователя")
    data_id: str = Field(description="Идентификатор датасета")
    model_name: str = Field(description="Имя модели")
    s3_key: str = Field(description="Ключ модели в S3")
    metrics: list[ModelScore] = Field(description="Метрики модели на трейне")


class ModelPred(BaseModel):
    predictions: list[float] = Field(description="Предсказания модели")


class DeleteModelResponse(BaseModel):
    user_id: str = Field(description="Идентификатор пользователя")
    data_id: str = Field(description="Идентификатор датасета")
    model_name: str = Field(description="Имя модели")
