import requests


def test_health_app(config):
    """Проверка, что приложение живо"""
    response = requests.get(f"{config['BACKEND_ENDPOINT']}/health/app")
    assert response.status_code == 200, f"Приложение не запущено: {response.text}"
    result = response.json()
    assert "app" in result, "Отсутствует поле app в ответе"
    assert result["app"] == "ok", f"Неверный статус приложения: {result['app']}"


def test_health_s3(config):
    """Проверка доступности S3"""
    test_bucket = config.get("S3_BUCKET", "models-bucket")
    response = requests.get(
        f"{config['BACKEND_ENDPOINT']}/health/s3", params={"bucket": test_bucket}
    )
    assert response.status_code == 200, f"S3 не запущено: {response.text}"

    response_dict = response.json()
    assert "bucket" in response_dict, "Отсутствует поле bucket в ответе"
    assert "s3" in response_dict, "Отсутствует поле s3 в ответе"
    assert (
        response_dict["bucket"] == test_bucket
    ), f"Неверный бакет: {response_dict['bucket']}"
    assert response_dict["s3"] in [
        "ok",
        "no-such-bucket",
        "client error: 404",
    ], f"Неверный статус S3: {response_dict['s3']}"

    response_default = requests.get(f"{config['BACKEND_ENDPOINT']}/health/s3")
    assert (
        response_default.status_code == 200
    ), f"S3 не запущено: {response_default.text}"
    assert "bucket" in response_default.json(), "Отсутствует поле bucket в ответе"
    assert "s3" in response_default.json(), "Отсутствует поле s3 в ответе"
