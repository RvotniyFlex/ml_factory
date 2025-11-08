import requests


def test_list_user_datasets(config):
    """Получение списка датасетов"""
    resp = requests.get(
        f"{config['BACKEND_ENDPOINT']}/user/storage/datasets/{config['real_user']}"
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "user_id" in data, "Нет поля user_id"
    assert len(data["datasets"]) > 0, "Нет датасетов"

    filenames = [d["name"] for d in data["datasets"]]
    assert config["filename"] in filenames, "Отсутствует тестовый датасет"
