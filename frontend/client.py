import os
from typing import Any, Dict

import requests
from dotenv import load_dotenv


class BackendAPI:
    """
    Класс-обёртка для взаимодействия с backend API AutoML.
    """

    def __init__(self, env_path: str = ".env") -> None:
        """
        Инициализация BackendAPI. Загружает переменные окружения и задаёт базовый URL API.

        Args:
            env_path (str): путь к .env файлу с настройками окружения
        """
        load_dotenv(env_path)
        self.backend_endpoint: str | None = os.getenv("BACKEND_ENDPOINT")

        if not self.backend_endpoint:
            raise ValueError("BACKEND_ENDPOINT не найден в .env файле.")

        self.headers: dict[str, str] = {"accept": "application/json"}

    def list_all_models(self) -> Dict[str, Any]:
        """
        Запрашиваем с бэка список всех доступных моделей для обучения.

        Returns:
            dict: Словарь с ключом 'models', содержащим список доступных моделей.
        """
        url = f"{self.backend_endpoint}//ml_management/all_models"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    def storage_size(self, user_id: int) -> dict:
        """
        Получение суммарного размера хранилища пользователя.

        Args:
            user_id (int): ID пользователя

        Returns:
            dict: JSON-ответ от сервера
        """
        url = f"{self.backend_endpoint}/dataset_management/usage/{user_id}"
        return self._get(url)

    def upload_dataset(self, user_id: int, file_path: str) -> dict:
        """
        Загрузка файла пользователя на сервер.

        Args:
            user_id (int): ID пользователя
            file_path (str): путь к файлу

        Returns:
            dict: JSON-ответ от сервера
        """
        url = f"{self.backend_endpoint}/dataset_management/upload/{user_id}"
        with open(file_path, "rb") as f:
            files = {"uploaded_file": (os.path.basename(file_path), f, "text/csv")}
            response = requests.post(url, headers=self.headers, files=files)
        return self._to_json(response)

    def delete_dataset(self, user_id: int, data_id: str) -> dict:
        """
        Удаление датасета пользователя.

        Args:
            user_id (int): ID пользователя
            data_id (str): ID датасета

        Returns:
            dict: JSON-ответ от сервера
        """
        url = f"{self.backend_endpoint}/dataset_management/delete/{user_id}/{data_id}"
        return self._delete(url)

    def load_dataset_info(self, user_id: int, data_id: str) -> dict:
        """
        Получение информации о датасете пользователя.

        Args:
            user_id (int): ID пользователя
            data_id (str): ID датасета

        Returns:
            dict: JSON-ответ от сервера
        """
        url = f"{self.backend_endpoint}/dataset_management/load/{user_id}/{data_id}"
        return self._get(url)

    def train_model(self, user_id: int, data_id: str, run_config: dict) -> dict:
        """
        Обучение модели на сервере.

        Args:
            user_id (int): ID пользователя
            data_id (str): ID датасета
            run_config (dict): конфигурация препроцессинга и модели

        Returns:
            dict: JSON-ответ от сервера
        """
        url = f"{self.backend_endpoint}/ml_management/train/{user_id}/{data_id}"
        headers = {**self.headers, "Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=run_config)
        return self._to_json(response)

    def predict(
        self, user_id: int, data_id: str, model_name: str, data: list[dict]
    ) -> dict:
        """
        Выполнение предсказания по новому датасету.

        Args:
            user_id (int): ID пользователя
            data_id (str): ID датасета
            model_name (str): имя модели
            data (list[dict]): данные для предсказания

        Returns:
            dict: JSON-ответ от сервера
        """
        url = f"{self.backend_endpoint}/ml_management/predict/{user_id}/{data_id}/{model_name}"
        headers = {**self.headers, "Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=data)
        return self._to_json(response)

    def delete_model(self, user_id: int, data_id: str, model_name: str) -> dict:
        """
        Удаление обученной модели.

        Args:
            user_id (int): ID пользователя
            data_id (str): ID датасета
            model_name (str): имя модели

        Returns:
            dict: JSON-ответ от сервера
        """
        url = f"{self.backend_endpoint}/ml_management/delete/{user_id}/{data_id}/{model_name}"
        return self._delete(url)

    def list_datasets(self, user_id: int) -> dict:
        """
        Получение списка всех датасетов пользователя.

        Args:
            user_id (int): ID пользователя

        Returns:
            dict: JSON-ответ от сервера
        """
        url = f"{self.backend_endpoint}/user/storage/datasets/{user_id}"
        return self._get(url)

    def list_models(self, user_id: int, data_id: str) -> dict:
        """
        Получение списка всех моделей пользователя по датасету.

        Args:
            user_id (int): ID пользователя
            data_id (str): ID датасета

        Returns:
            dict: JSON-ответ от сервера
        """
        url = f"{self.backend_endpoint}/user/storage/models/{user_id}/{data_id}"
        return self._get(url)

    def list_scores(self, user_id: int, data_id: str) -> dict:
        """
        Получение списка всех метрик по датасету.

        Args:
            user_id (int): ID пользователя
            data_id (str): ID датасета

        Returns:
            dict: JSON-ответ от сервера
        """
        url = f"{self.backend_endpoint}/user/storage/scores/{user_id}/{data_id}"
        return self._get(url)

    def _get(self, url: str) -> dict:
        """
        Отправка GET-запроса к серверу.

        Args:
            url (str): URL запроса

        Returns:
            dict: JSON-ответ от сервера
        """
        try:
            response = requests.get(url, headers=self.headers)
            return self._to_json(response)
        except requests.RequestException as e:
            return {"error": str(e)}

    def _delete(self, url: str) -> dict:
        """
        Отправка DELETE-запроса к серверу.

        Args:
            url (str): URL запроса

        Returns:
            dict: JSON-ответ от сервера
        """
        try:
            response = requests.delete(url, headers=self.headers)
            return self._to_json(response)
        except requests.RequestException as e:
            return {"error": str(e)}

    def _to_json(self, response: requests.Response) -> dict:
        """
        Унифицированный парсер JSON-ответов от сервера.

        Args:
            response (requests.Response): объект ответа requests

        Returns:
            dict: JSON-ответ или описание ошибки
        """
        try:
            response.raise_for_status()
            return response.json()
        except ValueError:
            return {"error": response.text, "status_code": response.status_code}
        except requests.HTTPError as e:
            return {"error": str(e), "status_code": response.status_code}
