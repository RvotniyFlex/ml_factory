import json

import pandas as pd
import requests


def test_train_and_predict(config):
    """Проверка обучения и предсказания"""
    user_id = config["real_user"]

    with open("data/titanic_config.json") as f:
        preprocessing_config = json.load(f)

    resp = requests.get(f"{config['BACKEND_ENDPOINT']}/user/storage/datasets/{user_id}")
    assert resp.status_code == 200, f"Ошибка получения датасетов: {resp.text}"
    data = resp.json()

    datasets = [d for d in data["datasets"] if d["name"] == config["filename"]]
    assert len(datasets) > 0, f"Датасет {config['filename']} не найден"
    data_id = datasets[0]["data_id"]

    train_resp = requests.post(
        f"{config['BACKEND_ENDPOINT']}/ml_management/train/{user_id}/{data_id}",
        json=preprocessing_config,
    )
    assert train_resp.status_code == 200, f"Ошибка тренировки: {train_resp.text}"
    train_data = train_resp.json()

    assert "model_name" in train_data, "Отсутствует model_name в ответе"
    assert "user_id" in train_data, "Отсутствует user_id в ответе"
    assert "data_id" in train_data, "Отсутствует data_id в ответе"
    assert "s3_key" in train_data, "Отсутствует s3_key в ответе"
    assert "metrics" in train_data, "Отсутствует metrics в ответе"
    assert train_data["user_id"] == user_id, "Неверный user_id в ответе"
    assert train_data["data_id"] == data_id, "Неверный data_id в ответе"
    assert isinstance(train_data["metrics"], list), "metrics должен быть списком"

    model_name = train_data["model_name"]

    test_data = pd.read_csv("data/test.csv")
    if "Fare" in test_data.columns:
        input_data = (
            test_data.drop(columns=["Fare"], axis=1).fillna(0).to_dict("records")
        )
    else:
        input_data = test_data.fillna(0).to_dict("records")

    predict_resp = requests.post(
        f"{config['BACKEND_ENDPOINT']}/ml_management/predict/{user_id}/{data_id}/{model_name}",
        json=input_data,
    )
    assert predict_resp.status_code == 200, f"Ошибка предсказания: {predict_resp.text}"

    predict_data = predict_resp.json()
    assert "predictions" in predict_data, "Отсутствует поле predictions в ответе"
    preds = predict_data["predictions"]
    assert isinstance(preds, list), "predictions должен быть списком"
    assert len(preds) == len(
        test_data
    ), f"Неверное количество предсказаний: {len(preds)} != {len(test_data)}"
