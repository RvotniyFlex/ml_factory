import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from client import BackendAPI

# ==============================
# Настройки Streamlit
# ==============================
st.set_page_config(page_title="AutoML Dashboard", layout="wide")

api = BackendAPI()
USER_ID = 3

st.sidebar.title("📂 Навигация")
page = st.sidebar.radio(
    "Выберите страницу:",
    [
        "1️⃣ Загрузка датасета",
        "2️⃣ Настройка предпроцессинга",
        "3️⃣ Настройка и обучение модели",
        "4️⃣ Дашборд моделей",
        "5️⃣ Инференс модели",
        "6️⃣ Технические операции",
    ],
)

# ==============================
# Session state
# ==============================
if "data_id" not in st.session_state:
    st.session_state.data_id = None
if "preprocessing" not in st.session_state:
    st.session_state.preprocessing = None
if "model_config" not in st.session_state:
    st.session_state.model_config = None
if "run_config" not in st.session_state:
    st.session_state.run_config = None


# ====================================================
# 1️⃣ ЗАГРУЗКА
# ====================================================
if page.startswith("1️⃣"):
    st.title("📥 Загрузка датасета")

    uploaded_file = st.file_uploader("Загрузите CSV файл", type=["csv"])
    if uploaded_file:
        tmp_path = Path("temp") / uploaded_file.name
        tmp_path.parent.mkdir(exist_ok=True)
        with open(tmp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.info("⏳ Загружаем датасет в базу...")
        api.upload_dataset(USER_ID, str(tmp_path))
        st.success("✅ Датасет успешно загружен в S3 через backend")

        st.session_state.data_id = uploaded_file.name
        st.info("Теперь перейдите на вкладку 2️⃣ для настройки модели и препроцессинга.")

# ====================================================
# 2️⃣ НАСТРОЙКА МОДЕЛИ + ПРЕПРОЦЕССИНГ
# ====================================================
elif page.startswith("2️⃣"):
    st.title("⚙️ Настройка модели и препроцессинга")

    # st.info("📡 Загружаем список доступных датасетов...")
    datasets_resp = api.list_datasets(USER_ID)

    if "datasets" not in datasets_resp or not datasets_resp["datasets"]:
        st.warning(
            "❌ У вас пока нет загруженных датасетов. Сначала загрузите хотя бы один на странице 1️⃣."
        )
        st.stop()

    dataset_options = {d["name"]: d["data_id"] for d in datasets_resp["datasets"]}

    selected_name = st.selectbox("📂 Выберите датасет:", list(dataset_options.keys()))
    selected_data_id = dataset_options[selected_name]

    st.session_state.data_id = selected_data_id
    # st.markdown(f"**Выбранный датасет:** `{selected_name}` (ID: {selected_data_id})")

    dataset_info = api.load_dataset_info(USER_ID, selected_data_id)

    if not dataset_info or "columns" not in dataset_info:
        st.error("❌ Не удалось получить информацию о датасете.")
        # st.json(dataset_info)
        st.stop()

    if dataset_info:
        columns = dataset_info.get("columns", [])
        col_type = dataset_info.get("col_type", []).values()
        num_nan = dataset_info.get("na_columns", []).values()
        st.session_state.dataset_info = dataset_info

        target = st.selectbox("🎯 Выберите целевую переменную:", columns)

        edited_rows = []
        edited_rows.append({"target": target})

        if target:
            # st.info("📡 Загружаем информацию о колонках...")
            feature_info = []
            for col, ctype, missing in zip(columns, col_type, num_nan):
                if ctype == "numerical":
                    fillna_policy = "mean" if missing > 0 else "–"
                else:
                    fillna_policy = "mode" if missing > 0 else "–"
                transformations = (
                    "StandardScaler" if ctype == "numerical" else "OneHotEncoder"
                )
                feature_info.append(
                    {
                        "name": col,
                        "col_type": ctype,
                        "missing_count": round(missing, 2),
                        "fillna_policy": fillna_policy,
                        "transformations": transformations,
                    }
                )

            st.markdown("### 🧩 Настройка препроцессинга признаков")

            num_options = ["StandardScaler", "MinMaxScaler", "None"]
            cat_options = ["LabelEncoder", "OneHotEncoder"]

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
                    use_col = st.checkbox("Drop column?", value=False, key=f"use_{i}")

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
            st.write(edited_rows)
            if st.button("💾 Сохранить препроцессинг"):
                st.session_state.preprocessing = edited_rows
                st.success("✅ Конфигурация препроцессинга сохранена!")
                st.info(
                    "Теперь перейдите на вкладку 3️⃣ для настройки и обучения модели."
                )

elif page.startswith("3️⃣"):
    st.markdown("### ⚙️ Настройка модели")
    model_class = st.selectbox(
        "🧠 Класс модели:", ["GradientBoostingRegressor", "ElasticNet"]
    )

    hyperparams = {}
    if model_class == "GradientBoostingRegressor":
        hyperparams["learning_rate"] = st.number_input(
            "learning_rate", value=0.1, min_value=0.001, max_value=1.0
        )
        hyperparams["max_depth"] = st.number_input(
            "max_depth", value=3, min_value=1, max_value=10
        )
        hyperparams["n_estimators"] = st.number_input(
            "n_estimators", value=100, min_value=10, step=10
        )
    else:
        hyperparams["alpha"] = st.number_input(
            "alpha", value=1.0, min_value=0.0, step=0.1
        )
        hyperparams["l1_ratio"] = st.number_input(
            "l1_ratio", value=0.5, min_value=0.0, max_value=1.0, step=0.05
        )

    if st.button("💾 Сохранить конфигурацию"):
        st.session_state.model_config = {
            "hyperparameters": hyperparams,
            "model_class": model_class,
        }
        st.success("✅ Конфигурация модели и препроцессинга сохранена!")

    preprocessing = st.session_state.preprocessing
    model_config = st.session_state.model_config
    data_id = st.session_state.data_id

    target_candidates = [r for r in preprocessing if "target" in r]
    if target_candidates:
        target = target_candidates[0]["target"]
    else:
        columns = [r["name"] for r in preprocessing if "name" in r]
        target = st.selectbox("🎯 Выберите целевую колонку:", options=columns)

    run_config = {
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

    if st.button("🚀 Запустить обучение"):
        response = api.train_model(USER_ID, data_id, run_config)

        if isinstance(response, dict) and "metrics" in response:
            st.success("✅ Модель обучена успешно!")
            model_name = response.get(
                "model_name", run_config["ml_config"]["model_class"]
            )
            df_metrics = pd.DataFrame(response["metrics"])
            df_metrics.insert(0, "model_name", model_name)
            df_metrics.insert(0, "data_id", data_id)

            st.markdown("### 📊 Метрики модели")
            st.dataframe(df_metrics, use_container_width=True, hide_index=True)
            st.info(
                "Теперь перейдите на вкладку 4️⃣ для, чтобы посмотреть дашборд качества."
            )

        else:
            st.error("❌ Ошибка при обучении модели.")
            # st.json(response)


# ====================================================
# 4️⃣ ДАШБОРД МОДЕЛЕЙ
# ====================================================
elif page.startswith("4️⃣"):
    st.title("📊 Дашборд обученных моделей")

    st.info("📡 Загружаем список доступных датасетов...")
    datasets_resp = api.list_datasets(USER_ID)

    if (
        not datasets_resp
        or "datasets" not in datasets_resp
        or not datasets_resp["datasets"]
    ):
        st.warning("❌ У вас пока нет загруженных датасетов.")
        st.stop()

    dataset_options = {d["name"]: d["data_id"] for d in datasets_resp["datasets"]}

    selected_name = st.selectbox("📂 Выберите датасет:", list(dataset_options.keys()))
    selected_data_id = dataset_options[selected_name]
    st.session_state.data_id = selected_data_id

    st.info("📈 Получаем метрики моделей...")
    scores_resp = api.list_scores(USER_ID, selected_data_id)

    if not scores_resp or "scores" not in scores_resp:
        st.warning("⚠️ Для этого датасета ещё нет обученных моделей.")
        st.stop()

    records = []
    for model_entry in scores_resp["scores"]:
        model_name = model_entry.get("name", "unknown_model")
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
        st.warning("⚠️ Нет данных о метриках.")
        st.stop()

    df = pd.DataFrame(records)

    available_metrics = sorted(df["metric"].unique().tolist())
    selected_metric = st.selectbox(
        "📊 Выберите метрику для сортировки:", available_metrics
    )
    df_filtered = df[df["metric"] == selected_metric].sort_values(
        by="value", ascending=False
    )

    st.markdown(
        f"### 📋 Результаты моделей по датасету `{selected_name}` (метрика `{selected_metric}`)"
    )
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)


# ====================================================
# 5️⃣ ИНФЕРЕНС МОДЕЛИ
# ====================================================
elif page.startswith("5️⃣"):
    st.title("🔮 Инференс модели")

    if not st.session_state.get("data_id"):
        st.info("📡 Загружаем список доступных датасетов...")
        datasets_resp = api.list_datasets(USER_ID)

        if (
            not datasets_resp
            or "datasets" not in datasets_resp
            or not datasets_resp["datasets"]
        ):
            st.warning("❌ У вас пока нет загруженных датасетов.")
            st.stop()

        dataset_options = {d["name"]: d["data_id"] for d in datasets_resp["datasets"]}

        selected_name = st.selectbox(
            "📂 Выберите датасет:", list(dataset_options.keys())
        )
        selected_data_id = dataset_options[selected_name]

        if st.button("✅ Подтвердить выбор датасета"):
            st.session_state.data_id = selected_data_id
            st.success(f"Выбран датасет: {selected_name}")
            st.rerun()
        else:
            st.stop()

    selected_data_id = st.session_state.data_id
    st.info(f"📦 Используется датасет ID: `{selected_data_id}`")

    st.info("📡 Загружаем список моделей для выбранного датасета...")
    models_resp = api.list_models(USER_ID, selected_data_id)

    if not models_resp or "models" not in models_resp or not models_resp["models"]:
        st.warning("❌ Для выбранного датасета нет обученных моделей.")
        st.stop()

    model_options = models_resp["models"]

    model_name = st.selectbox("🧠 Выберите модель для инференса:", model_options)

    st.info("📄 Загружаем конфигурацию препроцессинга...")
    preprocessing_info = api.load_dataset_info(USER_ID, selected_data_id)
    st.write(preprocessing_info)
    target = None
    if isinstance(preprocessing_info, dict):
        target = (
            preprocessing_info.get("target")
            or preprocessing_info.get("target_column")
            or preprocessing_info.get("preprocessing_config", {}).get("target")
        )

    uploaded_file = st.file_uploader("📂 Загрузите CSV с новыми данными", type=["csv"])

    if uploaded_file and model_name:
        df_new = pd.read_csv(uploaded_file)
        st.markdown("### 👀 Предпросмотр данных для инференса")
        st.dataframe(df_new.head(), use_container_width=True)

        st.info("⚙️ Отправляем данные на backend для предсказаний...")
        df_new: pd.DataFrame = df_new.replace(
            {np.nan: None, np.inf: None, -np.inf: None}
        )
        data = df_new.to_dict(orient="records")

        response = api.predict(USER_ID, selected_data_id, model_name, data)
        st.write(response)

        st.success("✅ Предсказания получены!")
        if isinstance(response, dict) and "predictions" in response:
            preds = response["predictions"]

            if len(preds) == len(df_new):
                df_result = df_new.copy()
                df_result["prediction"] = preds
            else:
                df_result = pd.DataFrame({"prediction": preds})

            st.markdown("### 📈 Результаты предсказания")
            st.dataframe(df_result, use_container_width=True)

            csv_bytes = df_result.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Скачать результаты в CSV",
                data=csv_bytes,
                file_name=f"predictions_{model_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
        else:
            st.warning("❌ Ванга сегодня не работает.")
# ====================================================
# 6️⃣ ТЕХНИЧЕСКИЕ ОПЕРАЦИИ
# ====================================================
elif page.startswith("6️⃣"):
    st.title("🛠 Технические операции")

    st.subheader("📦 Информация о хранилище")
    st.info("📡 Получаем данные о размере хранилища...")

    usage = api.storage_size(USER_ID)
    if isinstance(usage, dict) and "usage_mb" in usage:
        st.metric("Используемое место", f"{usage['usage_mb']} MB")
    else:
        st.warning("⚠️ Не удалось получить информацию о хранилище.")
        # st.json(usage)

    st.divider()

    st.subheader("🗑 Удаление датасета")

    datasets_resp = api.list_datasets(USER_ID)
    if (
        not datasets_resp
        or "datasets" not in datasets_resp
        or not datasets_resp["datasets"]
    ):
        st.warning("❌ У вас нет загруженных датасетов.")
    else:
        dataset_options = {
            f"{d['name']} ({d['data_id']})": d["data_id"]
            for d in datasets_resp["datasets"]
        }
        dataset_choice = st.selectbox(
            "📂 Выберите датасет для удаления:", list(dataset_options.keys())
        )
        if st.button("🚨 Удалить выбранный датасет"):
            data_id = dataset_options[dataset_choice]
            with st.spinner("Удаляем датасет..."):
                resp = api.delete_dataset(USER_ID, data_id)
            st.success("✅ Датасет успешно удалён!")
            # st.json(resp)
            st.rerun()

    st.divider()

    st.subheader("🧠 Удаление модели")

    datasets_resp = api.list_datasets(USER_ID)
    if (
        not datasets_resp
        or "datasets" not in datasets_resp
        or not datasets_resp["datasets"]
    ):
        st.warning("❌ Сначала загрузите хотя бы один датасет.")
        st.stop()

    dataset_options = {
        f"{d['name']} ({d['data_id']})": d["data_id"] for d in datasets_resp["datasets"]
    }
    selected_dataset_for_model = st.selectbox(
        "📂 Выберите датасет:", list(dataset_options.keys()), key="model_dataset_select"
    )
    selected_data_id = dataset_options[selected_dataset_for_model]

    st.info("📡 Загружаем список моделей...")
    models_resp = api.list_models(USER_ID, selected_data_id)

    if not models_resp or "models" not in models_resp or not models_resp["models"]:
        st.warning("❌ Для выбранного датасета нет обученных моделей.")
    else:
        model_name = st.selectbox(
            "🧠 Выберите модель для удаления:", models_resp["models"]
        )
        if st.button("🔥 Удалить модель"):
            with st.spinner("Удаляем модель..."):
                resp = api.delete_model(USER_ID, selected_data_id, model_name)
            st.success("✅ Модель успешно удалена!")
            # st.json(resp)
            st.rerun()
