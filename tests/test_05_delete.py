import pytest
import requests


def test_delete_model(config):
    """
    Удаляет модель пользователя из S3.
    """
    user_id = config["real_user"]

    resp = requests.get(f"{config['BACKEND_ENDPOINT']}/user/storage/datasets/{user_id}")
    assert resp.status_code == 200, f"Ошибка получения датасетов: {resp.text}"
    data = resp.json()
    data_id = next(
        (d["data_id"] for d in data["datasets"] if d["name"] == config["filename"]),
        None,
    )

    if data_id is None:
        pytest.skip("Нет датасета для тестирования удаления модели")

    resp = requests.get(
        f"{config['BACKEND_ENDPOINT']}/user/storage/models/{user_id}/{data_id}"
    )
    assert resp.status_code == 200, f"Ошибка получения моделей: {resp.text}"
    data = resp.json()
    assert "models" in data, "Отсутствует поле models в ответе"
    models = data["models"]

    if not models:
        pytest.skip("Нет моделей для тестирования удаления")

    model_to_delete = models[0]

    url = f"{config['BACKEND_ENDPOINT']}/ml_management/delete/{user_id}/{data_id}/{model_to_delete}"
    resp = requests.delete(url)
    assert resp.status_code == 200, f"Ошибка удаления модели: {resp.text}"

    delete_result = resp.json()
    assert "user_id" in delete_result, "Отсутствует поле user_id в ответе"
    assert "data_id" in delete_result, "Отсутствует поле data_id в ответе"
    assert "model_name" in delete_result, "Отсутствует поле model_name в ответе"
    assert (
        delete_result["model_name"] == model_to_delete
    ), "Неверное имя удаленной модели"

    resp = requests.get(
        f"{config['BACKEND_ENDPOINT']}/user/storage/models/{user_id}/{data_id}"
    )
    assert (
        resp.status_code == 200
    ), f"Ошибка получения моделей после удаления: {resp.text}"
    data = resp.json()
    remaining_models = data.get("models", [])
    assert model_to_delete not in remaining_models, "Модель не была удалена"


def test_delete_dataset(config):
    """
    Удаляет датасет пользователя из S3.
    """
    user_id = config["real_user"]

    # Получение списка датасетов
    resp = requests.get(f"{config['BACKEND_ENDPOINT']}/user/storage/datasets/{user_id}")
    assert resp.status_code == 200, f"Ошибка получения датасетов: {resp.text}"
    data = resp.json()
    assert "datasets" in data, "Отсутствует поле datasets в ответе"

    # Поиск датасетов с нужным именем
    datasets_to_delete = [
        d for d in data["datasets"] if d["name"] == config["filename"]
    ]

    if not datasets_to_delete:
        pytest.skip("Нет датасетов для тестирования удаления")

    deleted_names = []
    for dataset in datasets_to_delete:
        data_id = dataset["data_id"]
        dataset_name = dataset["name"]
        url = f"{config['BACKEND_ENDPOINT']}/dataset_management/delete/{user_id}/{data_id}"
        resp = requests.delete(url)
        assert resp.status_code == 200, f"Ошибка удаления датасета: {resp.text}"

        delete_result = resp.json()
        assert "user_id" in delete_result, "Отсутствует поле user_id в ответе"
        assert "data_id" in delete_result, "Отсутствует поле data_id в ответе"
        assert delete_result["data_id"] == data_id, "Неверный data_id в ответе"
        deleted_names.append(dataset_name)

    resp = requests.get(f"{config['BACKEND_ENDPOINT']}/user/storage/datasets/{user_id}")
    assert (
        resp.status_code == 200
    ), f"Ошибка получения датасетов после удаления: {resp.text}"
    data = resp.json()
    remaining_datasets = data.get("datasets", [])

    for deleted_name in deleted_names:
        remaining_names = [d["name"] for d in remaining_datasets]
        assert (
            deleted_name not in remaining_names
        ), f"Датасет {deleted_name} не был удален"


def test_storage_empty(config):
    """
    Проверяет использование хранилища пользователя.
    """
    user_id = config["real_user"]
    url = f"{config['BACKEND_ENDPOINT']}/dataset_management/usage/{user_id}"
    resp = requests.get(url)
    assert resp.status_code == 200, f"Ошибка при проверке использования S3: {resp.text}"

    result = resp.json()
    assert "user_id" in result, "Отсутствует поле user_id в ответе"
    assert "usage_mb" in result, "Отсутствует поле usage_mb в ответе"
    assert result["user_id"] == user_id, "Неверный user_id в ответе"

    usage_mb = result["usage_mb"]
    assert isinstance(usage_mb, (int, float)), "usage_mb должен быть числом"
    assert (
        usage_mb >= 0.0
    ), f"Использование хранилища не может быть отрицательным: {usage_mb}"
