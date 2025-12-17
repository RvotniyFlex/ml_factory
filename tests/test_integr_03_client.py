import requests


def test_list_user_datasets(config):
    """Получение списка датасетов"""
    user_id = config["real_user"]
    resp = requests.get(f"{config['BACKEND_ENDPOINT']}/user/storage/datasets/{user_id}")
    assert resp.status_code == 200, f"Ошибка получения списка датасетов: {resp.text}"
    data = resp.json()

    assert "user_id" in data, "Нет поля user_id в ответе"
    assert "datasets" in data, "Нет поля datasets в ответе"
    assert data["user_id"] == user_id, f"Неверный user_id: {data['user_id']}"
    assert isinstance(data["datasets"], list), "Поле datasets должно быть списком"

    if len(data["datasets"]) > 0:
        dataset = data["datasets"][0]
        assert "data_id" in dataset, "Нет поля data_id в датасете"
        assert "name" in dataset, "Нет поля name в датасете"

        filenames = [d["name"] for d in data["datasets"]]
        if config["filename"] in filenames:
            test_dataset = next(
                d for d in data["datasets"] if d["name"] == config["filename"]
            )
            assert "data_id" in test_dataset, "У тестового датасета нет data_id"
