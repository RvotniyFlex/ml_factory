from typing import Literal, Optional

from pydantic import BaseModel, Field


class GBRHParams(BaseModel):
    learning_rate: float = Field(description="Шаг градиента")
    max_depth: int = Field(description="Максимальная глубина дерева")
    n_estimators: int = Field(description="Количество деревьев")


class ElasticNetParams(BaseModel):
    alpha: float = Field(description="Коэффициент регуляризации")
    l1_ratio: float = Field(description="Соотношение между L1 и L2 регуляризацией")


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
