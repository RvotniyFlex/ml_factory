import os

import requests
from dotenv import load_dotenv


class BackendAPI:
    """
    Класс-обёртка для взаимодействия с backend API AutoML.
    Все методы возвращают JSON-ответы от сервера.
    """

    def __init__(self, env_path: str = "../.env"):
        load_dotenv(env_path)
        self.backend_endpoint = os.getenv("BACKEND_ENDPOINT")
        if not self.backend_endpoint:
            raise ValueError("BACKEND_ENDPOINT не найден в .env файле.")
        self.headers = {"accept": "application/json"}

    # -------------------------------
    # 1. Получить использование хранилища
    # -------------------------------
    def storage_size(self, user_id: int):
        url = f"{self.backend_endpoint}/dataset_management/usage/{user_id}"
        return self._get(url)

    # -------------------------------
    # 2. Загрузить файл пользователя
    # -------------------------------
    def upload_dataset(self, user_id: int, file_path: str):
        url = f"{self.backend_endpoint}/dataset_management/upload/{user_id}"
        with open(file_path, "rb") as f:
            files = {"uploaded_file": (os.path.basename(file_path), f, "text/csv")}
            response = requests.post(url, headers=self.headers, files=files)
        return self._to_json(response)

    # -------------------------------
    # 3. Удалить датасет
    # -------------------------------
    def delete_dataset(self, user_id: int, data_id: str):
        url = f"{self.backend_endpoint}/dataset_management/delete/{user_id}/{data_id}"
        return self._delete(url)

    # -------------------------------
    # 4. Получить sample и информацию о датасете
    # -------------------------------
    def load_dataset_info(self, user_id: int, data_id: str):
        url = f"{self.backend_endpoint}/dataset_management/load/{user_id}/{data_id}"
        return self._get(url)

    # -------------------------------
    # 5. Обучить модель по RunConfig
    # -------------------------------
    def train_model(self, user_id: int, data_id: str, run_config: dict):
        url = f"{self.backend_endpoint}/ml_management/train/{user_id}/{data_id}"
        headers = {**self.headers, "Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=run_config)
        return self._to_json(response)

    # -------------------------------
    # 6. Сделать предсказание по модели
    # -------------------------------
    def predict(self, user_id: int, data_id: str, model_name: str, data: list[dict]):
        url = f"{self.backend_endpoint}/ml_management/predict/{user_id}/{data_id}/{model_name}"
        headers = {**self.headers, "Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=data)
        return self._to_json(response)

    # -------------------------------
    # 7. Удалить модель
    # -------------------------------
    def delete_model(self, user_id: int, data_id: str, model_name: str):
        url = f"{self.backend_endpoint}/ml_management/delete/{user_id}/{data_id}/{model_name}"
        return self._delete(url)

    # -------------------------------
    # 8. Получить список всех датасетов пользователя
    # -------------------------------
    def list_datasets(self, user_id: int):
        url = f"{self.backend_endpoint}/user/storage/datasets/{user_id}"
        return self._get(url)

    # -------------------------------
    # 9. Получить список всех моделей для датасета
    # -------------------------------
    def list_models(self, user_id: int, data_id: str):
        url = f"{self.backend_endpoint}/user/storage/models/{user_id}/{data_id}"
        return self._get(url)

    # -------------------------------
    # 10. Получить метрики всех моделей пользователя
    # -------------------------------
    def list_scores(self, user_id: int, data_id: str):
        url = f"{self.backend_endpoint}/user/storage/scores/{user_id}/{data_id}"
        return self._get(url)

    # ==================================================
    # Вспомогательные приватные методы
    # ==================================================
    def _get(self, url: str):
        try:
            response = requests.get(url, headers=self.headers)
            return self._to_json(response)
        except requests.RequestException as e:
            return {"error": str(e)}

    def _delete(self, url: str):
        try:
            response = requests.delete(url, headers=self.headers)
            return self._to_json(response)
        except requests.RequestException as e:
            return {"error": str(e)}

    def _to_json(self, response: requests.Response):
        """Унифицированный парсер JSON-ответов"""
        try:
            response.raise_for_status()
            return response.json()
        except ValueError:
            return {"error": response.text, "status_code": response.status_code}
        except requests.HTTPError as e:
            return {"error": str(e), "status_code": response.status_code}
