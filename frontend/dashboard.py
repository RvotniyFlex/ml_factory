import datetime
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import streamlit as st
from client import BackendAPI

sys.path.append(str(Path(__file__).resolve().parents[1]))
from backend.utils.logger import get_logger, setup_logging

st.set_page_config(page_title="AutoML Dashboard", layout="wide")

api = BackendAPI()
USER_ID: int = 3

st.sidebar.title("📂 Навигация")
page: str = st.sidebar.radio(
    "Выберите страницу:",
    [
        "1️⃣ Загрузка датасета",
        "2️⃣ Настройка предпроцессинга и модели",
        "3️⃣ Дашборд моделей",
        "4️⃣ Инференс модели",
        "5️⃣ Технические операции",
    ],
)

if "logger_initialized" not in st.session_state:
    setup_logging()
    st.session_state.logger_initialized = True
logger = get_logger("frontend")

# Инициализируем session state

if "data_id" not in st.session_state:
    st.session_state.data_id: Optional[str] = None
if "preprocessing" not in st.session_state:
    st.session_state.preprocessing: Optional[List[Dict[str, Any]]] = None
if "model_config" not in st.session_state:
    st.session_state.model_config: Optional[Dict[str, Any]] = None
if "run_config" not in st.session_state:
    st.session_state.run_config: Optional[Dict[str, Any]] = None

# Часть 1. Загружаем датасет пользователья

if page.startswith("1️⃣"):
    st.title("📥 Загрузка датасета")

    uploaded_file = st.file_uploader("Загрузите CSV файл", type=["csv"])
    if uploaded_file:
        tmp_path: Path = Path("temp") / uploaded_file.name
        tmp_path.parent.mkdir(exist_ok=True)
        with open(tmp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        with st.spinner("Загружаем датасет в базу..."):
            api.upload_dataset(USER_ID, str(tmp_path))
        st.success("Датасет успешно загружен!")

        st.session_state.data_id = uploaded_file.name
        st.info("Теперь перейдите на вкладку 2️⃣ для настройки модели и препроцессинга.")


# Часть 2. Настраиваем предпроцессинг модели и запускаем обучение

elif page.startswith("2️⃣"):
    st.title("⚙️ Настройка модели и препроцессинга")

    datasets_resp: Dict[str, Any] = api.list_datasets(USER_ID)

    if "datasets" not in datasets_resp or not datasets_resp["datasets"]:
        st.warning(
            "У вас пока нет загруженных датасетов. Сначала загрузите хотя бы один на странице 1️⃣."
        )
        logger.error(
            "У вас пока нет загруженных датасетов. Сначала загрузите хотя бы один на странице 1️⃣."
        )
        st.stop()

    dataset_options: Dict[str, str] = {
        d["name"]: d["data_id"] for d in datasets_resp["datasets"]
    }
    selected_name: str = st.selectbox("Выберите датасет:", list(dataset_options.keys()))
    selected_data_id: str = dataset_options[selected_name]

    st.session_state.data_id = selected_data_id
    dataset_info: Optional[Dict[str, Any]] = api.load_dataset_info(
        USER_ID, selected_data_id
    )

    if not dataset_info or "columns" not in dataset_info:
        st.error("Не удалось получить информацию о датасете.")
        logger.error("Не удалось получить информацию о датасете.")
        st.stop()

    if dataset_info:
        columns: List[str] = dataset_info.get("columns", [])
        col_type = dataset_info.get("col_type", []).values()
        num_nan = dataset_info.get("na_columns", []).values()
        st.session_state.dataset_info = dataset_info

        target: str = st.selectbox("Выберите целевую переменную:", columns)

        edited_rows: List[Dict[str, Any]] = [{"target": target}]

        if target:
            feature_info: List[Dict[str, Any]] = []
            for col, ctype, missing in zip(columns, col_type, num_nan):
                fillna_policy: str = (
                    "mean"
                    if (ctype == "numerical" and missing > 0)
                    else ("mode" if ctype != "numerical" and missing > 0 else "–")
                )
                transformations: str = (
                    "StandardScaler" if ctype == "numerical" else "OneHotEncoder"
                )
                feature_info.append(
                    {
                        "name": col,
                        "col_type": ctype,
                        "missing_count": missing,
                        "fillna_policy": fillna_policy,
                        "transformations": transformations,
                    }
                )

            st.markdown("### Настройка препроцессинга признаков")

            num_options: List[str] = ["StandardScaler", "MinMaxScaler", "None"]
            cat_options: List[str] = ["LabelEncoder", "OneHotEncoder"]

            header_cols = st.columns([3, 2, 2, 2, 3, 2])
            with header_cols[0]:
                st.markdown("**Название переменной**")
            with header_cols[1]:
                st.markdown("**Тип переменной**")
            with header_cols[2]:
                st.markdown("**Кол-во пропусков**")
            with header_cols[3]:
                st.markdown("**FillNA**")
            with header_cols[4]:
                st.markdown("**Преобразование**")
            with header_cols[5]:
                st.markdown("**Удалить из модели?**")

            st.divider()

            for i, row in enumerate(feature_info):
                c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 2, 2, 3, 2])
                with c1:
                    st.markdown(f"**{row['name']}**")
                with c2:
                    st.text(row["col_type"])
                with c3:
                    st.text(f"{row['missing_count']}")

                with c4:
                    if row["col_type"] == "numerical":
                        fill_options = (
                            ["mean", "mode"]
                            if row["missing_count"] > 0
                            else ["–", "mean", "mode"]
                        )
                    else:
                        fill_options = (
                            ["mode"] if row["missing_count"] > 0 else ["–", "mode"]
                        )
                    fillna_policy = st.selectbox(
                        "FillNA",
                        options=fill_options,
                        index=fill_options.index(row["fillna_policy"])
                        if row["fillna_policy"] in fill_options
                        else 0,
                        key=f"fill_{i}",
                    )

                with c5:
                    transformations: str
                    if row["col_type"] == "numerical":
                        transformations = st.selectbox(
                            "Transformation",
                            options=num_options,
                            index=num_options.index(row["transformations"]),
                            key=f"trans_{i}",
                        )
                    else:
                        transformations = st.selectbox(
                            "Transformation",
                            options=cat_options,
                            index=cat_options.index(row["transformations"]),
                            key=f"trans_{i}",
                        )
                with c6:
                    use_col: bool = st.checkbox(
                        "Drop column?", value=False, key=f"use_{i}"
                    )

                edited_rows.append(
                    {
                        "name": row["name"],
                        "col_type": row["col_type"],
                        "missing_count": row["missing_count"],
                        "fillna_policy": fillna_policy,
                        "transformations": transformations,
                        "drop": use_col,
                    }
                )

        if st.button("💾 Сохранить препроцессинг"):
            st.session_state.preprocessing = edited_rows
            st.session_state.preprocessing_saved = True
            st.success("Конфигурация препроцессинга сохранена!")

        if st.session_state.get("preprocessing_saved"):
            st.markdown("### ⚙️ Настройка модели")

            models_resp = api.list_all_models()
            available_models = models_resp.get("models", [])

            if not available_models:
                st.error("Не удалось получить список доступных моделей с сервера.")
                logger.error("Не удалось получить список доступных моделей с сервера.")
                st.stop()

            model_names = [m["name"] for m in available_models]
            model_class: str = st.selectbox(
                "Класс модели:", model_names, key="model_class_select"
            )

            selected_model = next(
                (m for m in available_models if m["name"] == model_class), None
            )

            if not selected_model or "hyperparameters" not in selected_model:
                st.error("У выбранной модели нет описания гиперпараметров.")
                logger.error("У выбранной модели нет описания гиперпараметров.")
                st.stop()

            st.markdown(f"**Настройка гиперпараметров для {model_class}**")
            hyperparams: Dict[str, Any] = {}

            for param_name, default_value in selected_model["hyperparameters"].items():
                if isinstance(default_value, float):
                    hyperparams[param_name] = st.number_input(
                        param_name,
                        value=float(default_value),
                        step=0.01,
                        key=f"{model_class}_{param_name}",
                    )
                elif isinstance(default_value, int):
                    hyperparams[param_name] = st.number_input(
                        param_name,
                        value=int(default_value),
                        step=1,
                        key=f"{model_class}_{param_name}",
                    )
                else:
                    hyperparams[param_name] = st.text_input(
                        param_name,
                        value=str(default_value),
                        key=f"{model_class}_{param_name}",
                    )

            if st.button("💾 Сохранить конфигурацию и запустить обучение"):
                st.session_state.model_config = {
                    "hyperparameters": hyperparams,
                    "model_class": model_class,
                }
                st.session_state.model_saved = True
                st.success("Модель сохранена!")

                preprocessing: List[Dict[str, Any]] = st.session_state.preprocessing
                model_config: Dict[str, Any] = st.session_state.model_config
                data_id: str = st.session_state.data_id

                run_config: Dict[str, Any] = {
                    "preprocessing_config": {
                        "dataset_preprocessing": [
                            {
                                "name": row["name"],
                                "data_type": row["col_type"],
                                "fillna_policy": None
                                if row["fillna_policy"] in ["–", "-", "None"]
                                else row["fillna_policy"],
                                "transformations": None
                                if row["transformations"] in ["None", "-", "–"]
                                else row["transformations"],
                                "drop": row["drop"],
                            }
                            for row in preprocessing
                            if "name" in row
                        ],
                        "target": target,
                    },
                    "ml_config": model_config,
                }

                st.session_state.run_config = run_config
                with st.spinner("Обучаем модель..."):
                    response: Dict[str, Any] = api.train_model(
                        USER_ID, data_id, run_config
                    )
                if isinstance(response, dict) and "metrics" in response:
                    st.success("Модель обучена успешно!")
                    df_metrics: pd.DataFrame = pd.DataFrame(response["metrics"])
                    st.dataframe(df_metrics, use_container_width=True, hide_index=True)
                else:
                    st.error("Ошибка при обучении модели.")
                    logger.error("Ошибка при обучении модели.")

# Часть 3. Дашборд

elif page.startswith("3️⃣"):
    st.title("📊 Дашборд обученных моделей")

    datasets_resp: Dict[str, Any] = api.list_datasets(USER_ID)

    if (
        not datasets_resp
        or "datasets" not in datasets_resp
        or not datasets_resp["datasets"]
    ):
        st.warning("У вас пока нет загруженных датасетов.")
        logger.error("У вас пока нет загруженных датасетов.")
        st.stop()

    dataset_options: Dict[str, str] = {
        d["name"]: d["data_id"] for d in datasets_resp["datasets"]
    }
    selected_name: str = st.selectbox("Выберите датасет:", list(dataset_options.keys()))
    selected_data_id: str = dataset_options[selected_name]
    st.session_state.data_id = selected_data_id

    scores_resp: Dict[str, Any] = api.list_scores(USER_ID, selected_data_id)

    if not scores_resp or "scores" not in scores_resp:
        st.warning("Для этого датасета ещё нет обученных моделей.")
        st.stop()

    records: List[Dict[str, Any]] = []
    for model_entry in scores_resp["scores"]:
        model_name: str = model_entry.get("name", "unknown_model")
        for metric in model_entry.get("scores", []):
            records.append(
                {
                    "data_id": scores_resp.get("data_id"),
                    "model_name": model_name,
                    "metric": metric.get("name"),
                    "value": metric.get("value"),
                }
            )

    if not records:
        st.warning("Нет данных о метриках.")
        st.stop()

    df: pd.DataFrame = pd.DataFrame(records)

    available_metrics: List[str] = sorted(df["metric"].unique().tolist())
    selected_metric: str = st.selectbox(
        "Выберите метрику для сортировки:", available_metrics
    )
    df_filtered: pd.DataFrame = df[df["metric"] == selected_metric].sort_values(
        by="value", ascending=False
    )

    st.markdown(
        f"### Результаты моделей по датасету `{selected_name}` (метрика `{selected_metric}`)"
    )
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

# Часть 4. Предсказания на новых данных

elif page.startswith("4️⃣"):
    st.title("🔮 Инференс модели")

    datasets_resp: Dict[str, Any] = api.list_datasets(USER_ID)

    if "datasets" not in datasets_resp or not datasets_resp["datasets"]:
        st.warning(
            "У вас пока нет загруженных датасетов. Сначала загрузите хотя бы один на странице 1️⃣."
        )
        st.stop()

    dataset_options: Dict[str, str] = {
        d["name"]: d["data_id"] for d in datasets_resp["datasets"]
    }
    selected_name: str = st.selectbox("Выберите датасет:", list(dataset_options.keys()))
    selected_data_id: str = dataset_options[selected_name]

    st.session_state.data_id = selected_data_id

    models_resp: Dict[str, Any] = api.list_models(USER_ID, selected_data_id)

    if not models_resp or "models" not in models_resp or not models_resp["models"]:
        st.warning("Для выбранного датасета нет обученных моделей.")
        st.stop()

    model_options: List[str] = models_resp["models"]
    model_name: str = st.selectbox("Выберите модель для инференса:", model_options)

    preprocessing_info = api.load_dataset_info(USER_ID, selected_data_id)

    target = None
    if isinstance(preprocessing_info, dict):
        target = (
            preprocessing_info.get("target")
            or preprocessing_info.get("target_column")
            or preprocessing_info.get("preprocessing_config", {}).get("target")
        )

    uploaded_file = st.file_uploader("Загрузите CSV с новыми данными", type=["csv"])

    if uploaded_file and model_name:
        df_new: pd.DataFrame = pd.read_csv(uploaded_file)
        st.markdown("### Предпросмотр данных для инференса")
        st.dataframe(df_new.head(), use_container_width=True)

        st.info("Отправляем данные для предсказаний...")
        df_new: pd.DataFrame = df_new.replace(
            {np.nan: None, np.inf: None, -np.inf: None}
        )
        data: List[Dict[str, Any]] = df_new.to_dict(orient="records")
        response: Dict[str, Any] = api.predict(
            USER_ID, selected_data_id, model_name, data
        )

        st.success("Предсказания получены!")
        if isinstance(response, dict) and "predictions" in response:
            preds: List[float] = response["predictions"]

            if len(preds) == len(df_new):
                df_result: pd.DataFrame = df_new.copy()
                df_result["prediction"] = preds
            else:
                df_result = pd.DataFrame({"prediction": preds})

            st.markdown("### Результаты предсказания")
            st.dataframe(df_result, use_container_width=True)

            csv_bytes: bytes = df_result.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Скачать результаты в CSV",
                data=csv_bytes,
                file_name=f"predictions_{model_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
        else:
            st.warning("Ванга сегодня не работает.")
            logger.error("Предсказания не получены.")

# Часть 5. Технические операции

elif page.startswith("5️⃣"):
    st.title("🛠 Технические операции")

    st.subheader("Информация о хранилище")
    st.info("Получаем данные о размере хранилища...")

    usage: Dict[str, Any] = api.storage_size(USER_ID)
    if isinstance(usage, dict) and "usage_mb" in usage:
        st.metric("Используемое место", f"{usage['usage_mb']} MB")
    else:
        st.warning("Не удалось получить информацию о хранилище.")

    st.divider()

    st.subheader("Удаление датасета")

    datasets_resp: Dict[str, Any] = api.list_datasets(USER_ID)
    if (
        not datasets_resp
        or "datasets" not in datasets_resp
        or not datasets_resp["datasets"]
    ):
        st.warning("У вас нет загруженных датасетов.")
    else:
        dataset_options: Dict[str, str] = {
            f"{d['name']} ({d['data_id']})": d["data_id"]
            for d in datasets_resp["datasets"]
        }
        dataset_choice: str = st.selectbox(
            "Выберите датасет для удаления:", list(dataset_options.keys())
        )
        if st.button("Удалить выбранный датасет"):
            data_id: str = dataset_options[dataset_choice]
            with st.spinner("Удаляем датасет..."):
                resp = api.delete_dataset(USER_ID, data_id)
            st.success("Датасет успешно удалён!")
            st.rerun()

    st.divider()

    st.subheader("Удаление модели")

    datasets_resp = api.list_datasets(USER_ID)
    if (
        not datasets_resp
        or "datasets" not in datasets_resp
        or not datasets_resp["datasets"]
    ):
        st.warning("Сначала загрузите хотя бы один датасет.")
        st.stop()

    dataset_options = {
        f"{d['name']} ({d['data_id']})": d["data_id"] for d in datasets_resp["datasets"]
    }
    selected_dataset_for_model: str = st.selectbox(
        "Выберите датасет:", list(dataset_options.keys()), key="model_dataset_select"
    )
    selected_data_id: str = dataset_options[selected_dataset_for_model]

    st.info("Загружаем список моделей...")
    models_resp: Dict[str, Any] = api.list_models(USER_ID, selected_data_id)

    if not models_resp or "models" not in models_resp or not models_resp["models"]:
        st.warning("Для выбранного датасета нет обученных моделей.")
    else:
        model_name = st.selectbox(
            "Выберите модель для удаления:", models_resp["models"]
        )
        if st.button("Удалить модель"):
            with st.spinner("Удаляем модель..."):
                resp = api.delete_model(USER_ID, selected_data_id, model_name)
            st.success("Модель успешно удалена!")
            st.rerun()
