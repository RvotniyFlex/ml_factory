import pandas as pd
from sklearn.preprocessing import (
    LabelEncoder,
    MinMaxScaler,
    OneHotEncoder,
    StandardScaler,
)

from utils.data_models import ColumnPreprocessing, DatasetPreprocessing


def apply_fillna_policy(df: pd.DataFrame, col_cfg: ColumnPreprocessing) -> pd.DataFrame:
    """
    Применяет стратегию заполнения пропусков для заданной колонки.

    Args:
        df (pd.DataFrame): исходный DataFrame
        col_cfg (ColumnPreprocessing): конфигурация колонки

    Returns:
        pd.DataFrame: DataFrame с обработанными пропусками
    """
    col_name: str = col_cfg.name

    if col_name not in df.columns:
        return df

    if col_cfg.fillna_policy == "mean" and col_cfg.data_type == "numerical":
        df[col_name] = df[col_name].fillna(df[col_name].mean())

    elif col_cfg.fillna_policy == "mode":
        df[col_name] = df[col_name].fillna(df[col_name].mode().iloc[0])

    return df


def apply_transformations(
    df: pd.DataFrame, col_cfg: ColumnPreprocessing, transformer: any
) -> tuple[pd.DataFrame, any]:
    """
    Применяет указанные преобразования данных для колонки.

    Args:
        df (pd.DataFrame): исходный DataFrame
        col_cfg (ColumnPreprocessing): конфигурация колонки
        transformer (any | None): текущий трансформатор (если есть)

    Returns:
        pd.DataFrame (DataFrame): с применёнными преобразованиями
        transformer (any): препроцессор
    """
    col_name: str = col_cfg.name

    if col_name not in df.columns:
        return df

    if col_cfg.transformations == "StandardScaler":
        if not transformer:
            transformer = StandardScaler()
            df[col_name] = transformer.fit_transform(df[[col_name]])
        else:
            df[col_name] = transformer.transform(df[[col_name]])

    elif col_cfg.transformations == "MinMaxScaler":
        if not transformer:
            transformer = MinMaxScaler()
            df[col_name] = transformer.fit_transform(df[[col_name]])
        else:
            df[col_name] = transformer.transform(df[[col_name]])

    elif col_cfg.transformations == "LabelEncoder":
        if not transformer:
            transformer = LabelEncoder()
            df[col_name] = transformer.fit_transform(df[col_name].astype(str))
        else:
            df[col_name] = transformer.transform(df[col_name])

    elif col_cfg.transformations == "OneHotEncoder":
        if not transformer:
            transformer = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
            transformed: pd.DataFrame = transformer.fit_transform(df[[col_name]])
            ohe_df: pd.DataFrame = pd.DataFrame(
                transformed,
                columns=[f"{col_name}_{cat}" for cat in transformer.categories_[0]],
                index=df.index,
            )
            df: pd.DataFrame = pd.concat([df.drop(columns=[col_name]), ohe_df], axis=1)
        else:
            transformed: pd.DataFrame = transformer.transform(df[[col_name]])
            ohe_df: pd.DataFrame = pd.DataFrame(
                transformed,
                columns=[f"{col_name}_{cat}" for cat in transformer.categories_[0]],
                index=df.index,
            )
            df: pd.DataFrame = pd.concat([df.drop(columns=[col_name]), ohe_df], axis=1)

    return transformer, df


def preprocess_dataset(
    df: pd.DataFrame, preprocessing_cfg: DatasetPreprocessing, transformers: dict
) -> tuple[pd.DataFrame, dict]:
    """
    Применяет предобработку к DataFrame на основе DatasetPreprocessing.

    Args:
        df (pd.DataFrame): исходный DataFrame
        preprocessing_cfg (DatasetPreprocessing): конфигурация обработки
        transformers (dict): словарь с трансформаторами (если пустой, то создаются)

    Returns:
        pd.DataFrame: преобразованный DataFrame
        transformers (dict): словарь с трансформаторами (если пустой, то создаются)
    """
    df: pd.DataFrame = df.copy()
    fit = True if not transformers else False

    for col_cfg in preprocessing_cfg.dataset_preprocessing:
        col_name: str = col_cfg.name

        if col_cfg.drop:
            if col_name in df.columns:
                df: pd.DataFrame = df.drop(columns=[col_name])
            continue

        if (col_name not in df.columns) and (col_name == preprocessing_cfg.target):
            continue

        if (col_name not in df.columns) and (col_name != preprocessing_cfg.target):
            raise ValueError(f"Нет обязательного фактора: {col_name}")

        df: pd.DataFrame = apply_fillna_policy(df, col_cfg)
        transformer, df = apply_transformations(df, col_cfg, transformers.get(col_name))
        if fit:
            transformers[col_name] = transformer

    df: pd.DataFrame = df.dropna()
    return df, transformers
