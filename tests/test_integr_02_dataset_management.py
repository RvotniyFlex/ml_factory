import io

import pandas as pd
import requests


def test_upload_and_load_dataset(config):
    """Проверка загрузки и чтения датасета"""
    filename = config["filename"]
    user_id = config["real_user"]

    df = pd.read_csv(f"data/{filename}")
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    files = {"uploaded_file": (filename, buffer, "text/csv")}

    resp = requests.post(
        f"{config['BACKEND_ENDPOINT']}/dataset_management/upload/{user_id}",
        files=files,
    )

    assert resp.status_code == 200, f"Ошибка загрузки датасета: {resp.text}"
    result = resp.json()

    assert "data_id" in result, "Отсутствует data_id в ответе"
    assert "filename" in result, "Отсутствует filename в ответе"
    assert "user_id" in result, "Отсутствует user_id в ответе"
    data_id = result["data_id"]
    assert result["filename"] == filename, f"Неверное имя файла: {result['filename']}"
    assert result["user_id"] == user_id, f"Неверный user_id: {result['user_id']}"

    resp2 = requests.get(
        f"{config['BACKEND_ENDPOINT']}/dataset_management/load/{user_id}/{data_id}"
    )
    assert resp2.status_code == 200, f"Ошибка загрузки датасета: {resp2.text}"
    body = resp2.json()

    assert "rows" in body, "Отсутствует поле rows"
    assert "columns" in body, "Отсутствует поле columns"
    assert "user_id" in body, "Отсутствует поле user_id"
    assert "data_id" in body, "Отсутствует поле data_id"
    assert body["rows"] == len(
        df
    ), f"Неверное количество строк: {body['rows']} != {len(df)}"
    assert body["data_id"] == data_id, "Неверный data_id в ответе"
    assert body["user_id"] == user_id, "Неверный user_id в ответе"
