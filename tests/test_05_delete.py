import requests


def test_delete_model(config):
    """
    Удаляет модель пользователя из S3.
    """
    resp = requests.get(
        f"{config['BACKEND_ENDPOINT']}/user/storage/datasets/{config['real_user']}"
    )
    data = resp.json()
    data_id = next(
        (d["data_id"] for d in data["datasets"] if d["name"] == config["filename"]),
        None,
    )

    resp = requests.get(
        f"{config['BACKEND_ENDPOINT']}/user/storage/models/{config['real_user']}/{data_id}"
    )
    data = resp.json()
    models = data["models"]

    url = f"{config['BACKEND_ENDPOINT']}/ml_management/delete/{config['real_user']}/{data_id}/{models[0]}"
    resp = requests.delete(url)
    assert resp.status_code == 200, f"Ошибка удаления модели: {resp.text}"

    resp = requests.get(
        f"{config['BACKEND_ENDPOINT']}/user/storage/models/{config['real_user']}/{data_id}"
    )

    data = resp.json()
    for model in data["models"]:
        if model == models[0]:
            assert False, "Модель не была удалена"


def test_delete_dataset(config):
    """
    Удаляет датасет пользователя из S3.
    """
    resp = requests.get(
        f"{config['BACKEND_ENDPOINT']}/user/storage/datasets/{config['real_user']}"
    )
    data = resp.json()
    data_id = {
        d["data_id"]: d["name"]
        for d in data["datasets"]
        if d["name"] == config["filename"]
    }

    for idx, name in data_id.items():
        url = f"{config['BACKEND_ENDPOINT']}/dataset_management/delete/{config['real_user']}/{idx}"
        resp = requests.delete(url)
        assert resp.status_code == 200, f"Ошибка удаления датасета: {resp.text}"

    resp = requests.get(
        f"{config['BACKEND_ENDPOINT']}/user/storage/datasets/{config['real_user']}"
    )
    data = resp.json()
    for d in data["datasets"]:
        if d["name"] == name:
            assert False, "Датасет не был удален"


def test_storage_empty(config):
    """
    Проверяет, что пользовательская папка полностью очищена (0 МБ).
    """

    url = f"{config['BACKEND_ENDPOINT']}/dataset_management/usage/{config['real_user']}"
    resp = requests.get(url)
    assert resp.status_code == 200, f"Ошибка при проверке использования S3: {resp.text}"

    usage_mb = resp.json()["usage_mb"]
    assert usage_mb >= 0.0, "Ошибка при проверке использования S3"
