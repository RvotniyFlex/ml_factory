import io

import pandas as pd
import requests


def test_upload_and_load_dataset(config):
    """Проверка загрузки и чтения датасета"""
    filename = config["filename"]

    df = pd.read_csv(f"data/{filename}")
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    files = {"uploaded_file": (filename, buffer, "text/csv")}
    resp = requests.post(
        f"{config['BACKEND_ENDPOINT']}/dataset_management/upload/{config['real_user']}",
        files=files,
    )

    assert resp.status_code == 200, "Ошибка загрузки датасета"
    result = resp.json()

    assert "data_id" in result, "Отсутствует data_id"
    data_id = result["data_id"]

    assert result["filename"] == filename, "Неверное имя файла"

    resp2 = requests.get(
        f"{config['BACKEND_ENDPOINT']}/dataset_management/load/{config['real_user']}/{data_id}"
    )
    assert resp2.status_code == 200, "Ошибка загрузки датасета"
    body = resp2.json()

    assert "rows" in body, "Отсутствует поле rows"
    assert body["rows"] == len(df), "Неверное количество строк"
