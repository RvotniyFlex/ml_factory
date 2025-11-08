import json

import pandas as pd
import requests


def test_train_and_predict(config):
    """Проверка обучения и предсказания"""

    with open("data/titanic_config.json") as f:
        preprocessing_config = json.load(f)

    resp = requests.get(
        f"{config['BACKEND_ENDPOINT']}/user/storage/datasets/{config['real_user']}"
    )
    data = resp.json()
    data_id = [
        d["data_id"] for d in data["datasets"] if d["name"] == config["filename"]
    ][0]

    train_resp = requests.post(
        f"{config['BACKEND_ENDPOINT']}/ml_management/train/{config['real_user']}/{data_id}",
        json=preprocessing_config,
    )
    assert train_resp.status_code == 200, "Ошибка тренировки"
    train_data = train_resp.json()
    assert "model_name" in train_data, "Отсутствует model_name"

    test_data = pd.read_csv("data/test.csv")
    input_data = test_data.drop(columns=["Fare"], axis=1).fillna(0).to_dict("records")
    predict_resp = requests.post(
        f"{config['BACKEND_ENDPOINT']}/ml_management/predict/{config['real_user']}/{data_id}/{train_data['model_name']}",
        json=input_data,
    )
    assert predict_resp.status_code == 200, "Ошибка предсказания"

    preds = predict_resp.json()["predictions"]
    assert len(preds) == len(test_data), "Неверное количество предсказаний"
