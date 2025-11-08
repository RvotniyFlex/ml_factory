import pytest
from dotenv import dotenv_values, find_dotenv

config_dict = dotenv_values(find_dotenv(".env"))


@pytest.fixture(scope="session")
def config() -> str:
    """
    Базовый конфиг тестов, читается из переменной окружения.
    """
    config_dict["real_user"] = "47"
    config_dict["filename"] = "train.csv"
    return config_dict
