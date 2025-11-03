import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder, OneHotEncoder

from backend.utils.data_models import DatasetPreprocessing


def preprocess_dataset(df: pd.DataFrame, preprocessing_cfg: DatasetPreprocessing) -> pd.DataFrame:
    """
    Применяет предобработку к DataFrame на основе конфигурации DatasetPreprocessing.

    Args:
        df (pd.DataFrame): исходный DataFrame
        preprocessing_cfg (DatasetPreprocessing): DTO с конфигурацией обработки

    Returns:
        pd.DataFrame: преобразованный DataFrame
    """
    df: pd.DataFrame = df.copy()

    for col in preprocessing_cfg.dataset_preprocessing:
        col_name = col.name

        if col_name not in df.columns:
            raise ValueError(f"Колонка {col_name} не найдена в данных")
        
        if col.fillna_policy is None:
            pass
        
        if col.fillna_policy == "mean" and col.data_type == "numerical":
            df[col_name] = df[col_name].fillna(df[col_name].mean())

        elif col.fillna_policy == "mode":
            df[col_name] = df[col_name].fillna(df[col_name].mode().iloc[0])

        if col.transformations is None:
            pass

        if col.transformations == "StandardScaler":
            scaler = StandardScaler()
            df[col_name] = scaler.fit_transform(df[[col_name]])

        elif col.transformations == "MinMaxScaler":
            scaler = MinMaxScaler()
            df[col_name] = scaler.fit_transform(df[[col_name]])

        elif col.transformations == "LabelEncoder":
            encoder = LabelEncoder()
            df[col_name] = encoder.fit_transform(df[col_name].astype(str))

        elif col.transformations == "OneHotEncoder":
            encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
            transformed = encoder.fit_transform(df[[col_name]])
            ohe_df = pd.DataFrame(
                transformed,
                columns=[f"{col_name}_{cat}" for cat in encoder.categories_[0]],
                index=df.index,
            )
            df = pd.concat([df.drop(columns=[col_name]), ohe_df], axis=1)

    return df