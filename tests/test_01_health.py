import requests


def test_health_app(config):
    """Проверка, что приложение живо"""
    response = requests.get(f"{config['BACKEND_ENDPOINT']}/health/app")
    assert response.status_code == 200, "Приложение не запущено"
    assert response.json() == {"app": "ok"}


def test_health_s3(config):
    """Проверка доступности S3"""
    response = requests.get(
        f"{config['BACKEND_ENDPOINT']}/health/s3", params={"bucket": "models-bucket"}
    )
    assert response.status_code == 200, "S3 не запущено"

    response_dict = response.json()
    assert response_dict["bucket"] == "models-bucket", "Неверный бакет"
    assert response_dict["s3"] in ["ok", "no-such-bucket"], "Неверный статус S3"
