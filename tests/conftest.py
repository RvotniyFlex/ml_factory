import os

import pytest
from dotenv import dotenv_values, find_dotenv

config_dict = dotenv_values(find_dotenv(".env"))


@pytest.fixture(scope="session")
def config() -> str:
    """
    Базовый конфиг тестов, читается из переменной окружения.
    """
    config_dict["real_user"] = "3"
    config_dict["filename"] = "train.csv"

    backend_endpoint = config_dict.get("BACKEND_ENDPOINT", "")
    if backend_endpoint and "backend:8080" in backend_endpoint:
        config_dict["BACKEND_ENDPOINT"] = backend_endpoint.replace(
            "backend:8080", "localhost:8080"
        )
    elif not backend_endpoint:
        config_dict["BACKEND_ENDPOINT"] = "http://localhost:8080"

    env_backend = os.getenv("BACKEND_ENDPOINT")
    if env_backend:
        config_dict["BACKEND_ENDPOINT"] = env_backend

    return config_dict
