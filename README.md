### Проект

Проект сделан в рамках курса "Запуск ML моделей в промышленной среде". Сервис позволяет обучать линейную модель и градиентного бустинга для задачи регрессии. Сервис включает в себя реализацию протоколов gRPC и REST api на python. Интерактивное взаимодействие с сервисом происходит через python streamlit и масштабируется на нескольких пользователей, прошедших авторизацию. Модели и датасеты хранятся на S3 хранилище с квотой на 200 МБ на юзера.

### Команда

* Кондратьева Валерия
* Васильев Николай
* Мамедов Ильгар

### Структура проекта

```bash
ML_FACTORY/
├── .github/workflows/
│   └── ci.yaml                    # CI-пайплайн GitHub Actions (тесты, линтинг и т.д.)
├── backend/                       # Основной backend-код приложения
│   ├── auth # Логика авторизации
│   │   ├── google_oauth.py        # Авторизация через oAuth Google
│   │   └── jwt_manager.py         # Создание/управление токеном логина
│   ├── grpc/                      # gRPC сервер и контракты
│   │   ├── contracts/             
│   │   │   ├── contracts_pb2.py           # Автоматически сгенерированные protobuf-классы
│   │   │   └── contracts_pb2_grpc.py      # Автоматически сгенерированные gRPC-сервисы
│   │   ├── client.ipynb                   # Jupyter notebook для тестов gRPC клиента
│   │   └── server.py                      # Основной gRPC сервер (Health, Dataset, Model и т.д.)
│   │
│   ├── logs/                      # Логи работы backend-а
│   │   └── app.log                # Основной файл логов
│   │
│   ├── protos/
│   │   └── contracts.proto        # Исходный .proto файл с описанием gRPC API
│   │
│   ├── routers/                   # FastAPI маршруты (REST API)
│   │   ├── client.py              # Эндпоинты для работы с пользователем
│   │   ├── auth_routes.py         # Авторизация и получение токена для логина
│   │   ├── dataset_management.py  # Операции с датасетами
│   │   ├── health.py              # Проверки состояния приложения и S3
│   │   └── ml_management.py       # Обучение, предсказание и удаление моделей
│   │
│   ├── utils/                     # Вспомогательные модули
│   │   ├── __init__.py
│   │   ├── data_models.py         # Pydantic модели данных (RunConfig, DatasetPreprocessing и др.)
│   │   ├── dependents.py          # Зависимости FastAPI (s3_client_factory)
│   │   ├── logger.py              # Настройка логирования
│   │   ├── settings.py            # Настройки окружения и конфигурация (Модель данных .env)
│   │   ├── dataset_registry.py    # Функции для загрузки и удаления датасетов из S3
│   │   ├── main.py                # Точка входа FastAPI-приложения
│   │   ├── preprocessing.py       # Предобработка данных и сериализация трансформеров
│   │   ├── s3_connector.py        # Подключение к S3-хранилищу (aioboto3)
│   │   ├── training.py            # Обучение ML-моделей, сохранение и загрузка
│   │   └── user_object.py         # Управление объектами пользователя (датасеты, модели)
│
├── data/                          # Примеры данных и конфигураций
│   ├── test.csv                   # Тестовый CSV-дataset
│   ├── train.csv                  # Обучающий CSV-дataset
│   └── titanic_config.json        # Пример конфигурации препроцессинга/модели для Titanic
│
├── frontend/                         # Веб-интерфейс Streamlit
│   ├── __init__.py
│   ├── dashboard.py                   # Основной Streamlit-дэшборд
│   ├── client.py                      # Класс BackendAPI (взаимодействие с backend)
│   └── auth_client.py                 # Авторизация / токены (если нужно)
│
├── tests/                         # Автоматические тесты проекта (pytest)
│   ├── conftest.py                # Общие фикстуры (например, базовый URL)
│   ├── test_01_health.py          # Тесты эндпоинтов /health
│   ├── test_02_dataset_management.py  # Тесты CRUD операций с датасетами
│   ├── test_03_client.py          # Тесты взаимодействия с пользователем
│   ├── test_04_ml_management.py   # Тесты обучения и инференса моделей
│   └── test_05_delete.py          # Тест удаления моделей и датасетов + проверка “0 веса”
│
├── .env                           # Конфигурация окружения (S3, базы данных и т.д.)
├── .gitignore                     # Игнорируемые файлы Git
├── .pre-commit-config.yaml        # Настройки pre-commit хуков (линтеры, форматтеры)
├── docker-compose.yaml            # Описание docker-сервисов (S3)
├── poetry.lock                    # Зафиксированные версии зависимостей
├── makefile                       # Быстрый запуск сервиса
├── pyproject.toml                 # Конфигурация Poetry (зависимости, entrypoints и т.д.)
└── README.md                      # Документация проекта
```

### Запуск проекта

Установка зависимостей 

```bash
poetry install
```

Запуск всего сервиса (бек, фрон, хранилище)

```bash
make run
```

После запуска будут доступны три сервиса:

* Интерфейс (http://localhost:8501) - Streamlit
* Бекэнд (http://localhost:8080/docs#/) - Swagger
* S3 (http://localhost:9001) - WebUI


Остановка всех сервисов

```bash
make stop
```

#### Запуск отдельных блоков

Поднятие хранилище S3

```bash
docker compose up -d
```

Запуск приложения на REST-api

```bash
poetry run uvicorn backend.main:app --host 0.0.0.0 --port 8080
```

Взаимодействие возможно через встроенный Swagger Fast-api __http://localhost:8080/docs__

Запуск приложения на gRPC-api

```bash
poetry run python backend/grpc/server.py
```

Взаимодействие возможно через ноутбук-клиент __backend/grpc/client.ipynb__

Запуск интерфейса

```bash
poetry run streamlit run frontend/dashboard.py --server.port 8501 --server.headless true
```

### Тестирование

Для разработки и отладки были написаны тесты на основные функции

```bash
poetry run pytest tests 
```

### <a id='fastapi-endpoints'></a> `FastAPI Endpoints`

#### `GET /health/app`

**Описание:** Health App

> Проверка, что основное приложение живо.


**Ответы:**

- **Код 200:** Successful Response
  - Использует схему: [HealthCheckApp](#schema-healthcheckapp)

---

#### `GET /health/s3`

**Описание:** Health S3

> Проверка доступности S3-хранилища.


**Параметры:**

- `bucket` (необязательный): Имя бакета для проверки

**Ответы:**

- **Код 200:** Successful Response
  - Использует схему: [HealthCheckS3](#schema-healthchecks3)
- **Код 422:** Validation Error
  - Использует схему: [HTTPValidationError](#schema-httpvalidationerror)

---

#### `GET /dataset_management/usage/{user_id}`

**Описание:** Get User Storage Usage

> Получить объём хранилища, занимаемый пользователем.


**Параметры:**

- `user_id` (обязательный): Id пользователя

**Ответы:**

- **Код 200:** Successful Response
  - Использует схему: [UserStorage](#schema-userstorage)
- **Код 422:** Validation Error
  - Использует схему: [HTTPValidationError](#schema-httpvalidationerror)

---

#### `POST /dataset_management/upload/{user_id}`

**Описание:** Upload User File

> Загрузить parquet-файл пользователя в S3.


**Параметры:**

- `user_id` (обязательный): Id пользователя

**Request Body:**

- Использует схему: [Body_upload_user_file_dataset_management_upload__user_id__post](#schema-body_upload_user_file_dataset_management_upload__user_id__post)

**Ответы:**

- **Код 200:** Successful Response
  - Использует схему: [UploadDatasetResponse](#schema-uploaddatasetresponse)
- **Код 422:** Validation Error
  - Использует схему: [HTTPValidationError](#schema-httpvalidationerror)

---

#### `DELETE /dataset_management/delete/{user_id}/{data_id}`

**Описание:** Delete User File

> Удалить файл пользователя по ID.


**Параметры:**

- `user_id` (обязательный): Id пользователя
- `data_id` (обязательный): Id датасета

**Ответы:**

- **Код 200:** Successful Response
  - Использует схему: [DeleteDatasetResponse](#schema-deletedatasetresponse)
- **Код 422:** Validation Error
  - Использует схему: [HTTPValidationError](#schema-httpvalidationerror)

---

#### `GET /dataset_management/load/{user_id}/{data_id}`

**Описание:** Load User Dataframe

> Семл данных пользователя и информация о данных.


**Параметры:**

- `user_id` (обязательный): Id пользователя
- `data_id` (обязательный): Id датасета

**Ответы:**

- **Код 200:** Successful Response
  - Использует схему: [DatasetDescription](#schema-datasetdescription)
- **Код 422:** Validation Error
  - Использует схему: [HTTPValidationError](#schema-httpvalidationerror)

---

#### `GET /ml_management/all_models`

**Описание:** List All Models

> Возвращает список всех доступных моделей для обучения.


**Ответы:**

- **Код 200:** Successful Response
  - Использует схему: [AvailableModels](#schema-availablemodels)

---

#### `POST /ml_management/train/{user_id}/{data_id}`

**Описание:** Train Model Endpoint

> Обучает модель по RunConfig, сохраняет её в S3 и возвращает метрики и путь.


**Параметры:**

- `user_id` (обязательный): Id пользователя
- `data_id` (обязательный): Id датасета

**Request Body:**

- Использует схему: [RunConfig](#schema-runconfig)

**Ответы:**

- **Код 200:** Successful Response
  - Использует схему: [FittedModel](#schema-fittedmodel)
- **Код 422:** Validation Error
  - Использует схему: [HTTPValidationError](#schema-httpvalidationerror)

---

#### `POST /ml_management/predict/{user_id}/{data_id}/{model_name}`

**Описание:** Predict Endpoint

> Делает предсказание по обученной модели пользователя.


**Параметры:**

- `user_id` (обязательный): Id пользователя
- `data_id` (обязательный): Id датасета
- `model_name` (обязательный): Название модели

**Request Body:**

```json
{
  "type": "array",
  "items": {
    "type": "object",
    "additionalProperties": true
  },
  "description": "Данные для предсказания",
  "title": "Input Data"
}
```

**Ответы:**

- **Код 200:** Successful Response
  - Использует схему: [ModelPred](#schema-modelpred)
- **Код 422:** Validation Error
  - Использует схему: [HTTPValidationError](#schema-httpvalidationerror)

---

#### `DELETE /ml_management/delete/{user_id}/{data_id}/{model_name}`

**Описание:** Delete Model Endpoint

> Удаляет сохранённую модель из S3.


**Параметры:**

- `user_id` (обязательный): Id пользователя
- `data_id` (обязательный): Id датасета
- `model_name` (обязательный): Название модели

**Ответы:**

- **Код 200:** Successful Response
  - Использует схему: [DeleteModelResponse](#schema-deletemodelresponse)
- **Код 422:** Validation Error
  - Использует схему: [HTTPValidationError](#schema-httpvalidationerror)

---

#### `GET /user/storage/datasets/{user_id}`

**Описание:** List User Datasets

> Возвращает список всех датасетов пользователя.


**Параметры:**

- `user_id` (обязательный): Id пользователя

**Ответы:**

- **Код 200:** Successful Response
  - Использует схему: [UserDatasets](#schema-userdatasets)
- **Код 422:** Validation Error
  - Использует схему: [HTTPValidationError](#schema-httpvalidationerror)

---

#### `GET /user/storage/models/{user_id}/{data_id}`

**Описание:** List User Models

> Возвращает список всех моделей пользователя для заданного датасета.


**Параметры:**

- `user_id` (обязательный): Id пользователя
- `data_id` (обязательный): Id датасета

**Ответы:**

- **Код 200:** Successful Response
  - Использует схему: [UserModels](#schema-usermodels)
- **Код 422:** Validation Error
  - Использует схему: [HTTPValidationError](#schema-httpvalidationerror)

---

#### `GET /user/storage/scores/{user_id}/{data_id}`

**Описание:** List User Scores

> Возвращает список метрик моделей пользователя для заданного датасета.


**Параметры:**

- `user_id` (обязательный): Id пользователя
- `data_id` (обязательный): Id датасета

**Ответы:**

- **Код 200:** Successful Response
  - Использует схему: [UserScores](#schema-userscores)
- **Код 422:** Validation Error
  - Использует схему: [HTTPValidationError](#schema-httpvalidationerror)

---

#### `GET /auth/google/login`

**Описание:** Google OAuth Login Endpoint  

> Инициирует процесс авторизации через Google.  
> Перенаправляет пользователя на страницу входа Google с запросом разрешений.  

**Параметры:**  
Нет.  

**Ответы:**

- **Код 307:** Redirect  
  - Перенаправляет пользователя на страницу авторизации Google.  
- **Код 500:** Ошибка конфигурации  
  - Возвращается, если не задан `GOOGLE_REDIRECT_URI` в `.env`.

---

#### `GET /auth/google/callback`

**Описание:** Google OAuth Callback Endpoint  

> Получает ответ от Google после успешного входа,  
> обменивает код авторизации на токен доступа и создает JWT-токен для пользователя.  
> При наличии `FRONTEND_URL` перенаправляет обратно на Streamlit с `?token=<JWT>`.

**Параметры:**  
- `state` (обязательный, query): Защита от CSRF (генерируется автоматически Google API).  
- `code` (обязательный, query): Код авторизации, который возвращает Google.  

**Ответы:**

- **Код 302:** Redirect  
  - Перенаправляет на `FRONTEND_URL` с параметром `token=<JWT>`.  
- **Код 200:** Successful Response (если не указан `FRONTEND_URL`)  
  - Возвращает JSON с полями:  
    ```json
    {
      "access_token": "<jwt_token>",
      "email": "<user_email>",
      "expires_in_hours": 2
    }
    ```
- **Код 400:** Ошибка обмена кода или `state mismatch`.  
- **Код 500:** Внутренняя ошибка при авторизации.

---

#### `GET /auth/me`

**Описание:** Get Current User Endpoint  

> Проверяет валидность JWT-токена и возвращает информацию о текущем пользователе.  

**Параметры:**

- Заголовок `Authorization` (обязательный):  
  JWT-токен в формате  
  ```
  Authorization: Bearer <jwt_token>
  ```

**Ответы:**

- **Код 200:** Successful Response  
  ```json
  {
    "status": "ok",
    "claims": {
      "sub": "user@example.com",
      "name": "User Name",
      "iat": 1762702886,
      "exp": 1762710086
    }
  }
  ```
- **Код 401:** Invalid or missing token  
  ```json
  { "detail": "Invalid token: ..." }
  ```


# Схемы данных

#### <a id='schema-availablemodels'></a> `AvailableModels`

```json
{
  "properties": {
    "models": {
      "items": {
        "$ref": "#/components/schemas/ModelDescription"
      },
      "type": "array",
      "title": "Models",
      "description": "Список доступных моделей"
    }
  },
  "type": "object",
  "required": [
    "models"
  ],
  "title": "AvailableModels"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-body_upload_user_file_dataset_management_upload__user_id__post'></a> `Body_upload_user_file_dataset_management_upload__user_id__post`

```json
{
  "properties": {
    "uploaded_file": {
      "type": "string",
      "format": "binary",
      "title": "Uploaded File"
    }
  },
  "type": "object",
  "required": [
    "uploaded_file"
  ],
  "title": "Body_upload_user_file_dataset_management_upload__user_id__post"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-columnpreprocessing'></a> `ColumnPreprocessing`

```json
{
  "properties": {
    "name": {
      "type": "string",
      "title": "Name",
      "description": "Название колонки"
    },
    "data_type": {
      "type": "string",
      "enum": [
        "numerical",
        "categorical"
      ],
      "title": "Data Type",
      "description": "Тип данных"
    },
    "fillna_policy": {
      "anyOf": [
        {
          "type": "string",
          "enum": [
            "mean",
            "mode"
          ]
        },
        {
          "type": "null"
        }
      ],
      "title": "Fillna Policy",
      "description": "Политика заполнения пропусков"
    },
    "transformations": {
      "anyOf": [
        {
          "type": "string",
          "enum": [
            "StandardScaler",
            "MinMaxScaler",
            "LabelEncoder",
            "OneHotEncoder"
          ]
        },
        {
          "type": "null"
        }
      ],
      "title": "Transformations",
      "description": "Преобразования данных"
    },
    "drop": {
      "type": "boolean",
      "title": "Drop",
      "description": "Удалить колонку"
    }
  },
  "type": "object",
  "required": [
    "name",
    "data_type",
    "fillna_policy",
    "transformations",
    "drop"
  ],
  "title": "ColumnPreprocessing"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-datasetdescription'></a> `DatasetDescription`

```json
{
  "properties": {
    "user_id": {
      "type": "string",
      "title": "User Id",
      "description": "Идентификатор пользователя"
    },
    "data_id": {
      "type": "string",
      "title": "Data Id",
      "description": "Идентификатор датасета"
    },
    "columns": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "title": "Columns",
      "description": "Список колонок"
    },
    "na_columns": {
      "additionalProperties": {
        "type": "integer"
      },
      "type": "object",
      "title": "Na Columns",
      "description": "Количество пропусков"
    },
    "col_type": {
      "additionalProperties": {
        "type": "string",
        "enum": [
          "categorical",
          "numerical"
        ]
      },
      "type": "object",
      "title": "Col Type",
      "description": "Тип колонок"
    },
    "rows": {
      "type": "integer",
      "title": "Rows",
      "description": "Количество строк"
    },
    "sample": {
      "items": {
        "additionalProperties": true,
        "type": "object"
      },
      "type": "array",
      "title": "Sample",
      "description": "Пример данных"
    }
  },
  "type": "object",
  "required": [
    "user_id",
    "data_id",
    "columns",
    "na_columns",
    "col_type",
    "rows",
    "sample"
  ],
  "title": "DatasetDescription"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-datasetinfo'></a> `DatasetInfo`

```json
{
  "properties": {
    "name": {
      "type": "string",
      "title": "Name",
      "description": "Название датасета"
    },
    "data_id": {
      "type": "string",
      "title": "Data Id",
      "description": "id датасета"
    }
  },
  "type": "object",
  "required": [
    "name",
    "data_id"
  ],
  "title": "DatasetInfo"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-datasetpreprocessing'></a> `DatasetPreprocessing`

```json
{
  "properties": {
    "dataset_preprocessing": {
      "items": {
        "$ref": "#/components/schemas/ColumnPreprocessing"
      },
      "type": "array",
      "title": "Dataset Preprocessing",
      "description": "Список преобразований данных"
    },
    "target": {
      "type": "string",
      "title": "Target",
      "description": "Целевая переменная"
    }
  },
  "type": "object",
  "required": [
    "dataset_preprocessing",
    "target"
  ],
  "title": "DatasetPreprocessing"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-deletedatasetresponse'></a> `DeleteDatasetResponse`

```json
{
  "properties": {
    "user_id": {
      "type": "string",
      "title": "User Id",
      "description": "Идентификатор пользователя"
    },
    "data_id": {
      "type": "string",
      "title": "Data Id",
      "description": "Идентификатор датасета"
    }
  },
  "type": "object",
  "required": [
    "user_id",
    "data_id"
  ],
  "title": "DeleteDatasetResponse"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-deletemodelresponse'></a> `DeleteModelResponse`

```json
{
  "properties": {
    "user_id": {
      "type": "string",
      "title": "User Id",
      "description": "Идентификатор пользователя"
    },
    "data_id": {
      "type": "string",
      "title": "Data Id",
      "description": "Идентификатор датасета"
    },
    "model_name": {
      "type": "string",
      "title": "Model Name",
      "description": "Имя модели"
    }
  },
  "type": "object",
  "required": [
    "user_id",
    "data_id",
    "model_name"
  ],
  "title": "DeleteModelResponse"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-elasticnetparams'></a> `ElasticNetParams`

```json
{
  "properties": {
    "alpha": {
      "type": "number",
      "title": "Alpha",
      "description": "Коэффициент регуляризации"
    },
    "l1_ratio": {
      "type": "number",
      "title": "L1 Ratio",
      "description": "Соотношение между L1 и L2 регуляризацией"
    }
  },
  "type": "object",
  "required": [
    "alpha",
    "l1_ratio"
  ],
  "title": "ElasticNetParams"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-fitresult'></a> `FitResult`

```json
{
  "properties": {
    "name": {
      "type": "string",
      "title": "Name",
      "description": "Название модели"
    },
    "scores": {
      "items": {
        "$ref": "#/components/schemas/ModelScore"
      },
      "type": "array",
      "title": "Scores",
      "description": "Список метрик модели"
    }
  },
  "type": "object",
  "required": [
    "name",
    "scores"
  ],
  "title": "FitResult"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-fittedmodel'></a> `FittedModel`

```json
{
  "properties": {
    "user_id": {
      "type": "string",
      "title": "User Id",
      "description": "Идентификатор пользователя"
    },
    "data_id": {
      "type": "string",
      "title": "Data Id",
      "description": "Идентификатор датасета"
    },
    "model_name": {
      "type": "string",
      "title": "Model Name",
      "description": "Имя модели"
    },
    "s3_key": {
      "type": "string",
      "title": "S3 Key",
      "description": "Ключ модели в S3"
    },
    "metrics": {
      "items": {
        "$ref": "#/components/schemas/ModelScore"
      },
      "type": "array",
      "title": "Metrics",
      "description": "Метрики модели на трейне"
    }
  },
  "type": "object",
  "required": [
    "user_id",
    "data_id",
    "model_name",
    "s3_key",
    "metrics"
  ],
  "title": "FittedModel"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-gbrhparams'></a> `GBRHParams`

```json
{
  "properties": {
    "learning_rate": {
      "type": "number",
      "title": "Learning Rate",
      "description": "Шаг градиента"
    },
    "max_depth": {
      "type": "integer",
      "title": "Max Depth",
      "description": "Максимальная глубина дерева"
    },
    "n_estimators": {
      "type": "integer",
      "title": "N Estimators",
      "description": "Количество деревьев"
    }
  },
  "type": "object",
  "required": [
    "learning_rate",
    "max_depth",
    "n_estimators"
  ],
  "title": "GBRHParams"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-httpvalidationerror'></a> `HTTPValidationError`

```json
{
  "properties": {
    "detail": {
      "items": {
        "$ref": "#/components/schemas/ValidationError"
      },
      "type": "array",
      "title": "Detail"
    }
  },
  "type": "object",
  "title": "HTTPValidationError"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-healthcheckapp'></a> `HealthCheckApp`

```json
{
  "properties": {
    "app": {
      "type": "string",
      "const": "ok",
      "title": "App",
      "description": "Статус приложения"
    }
  },
  "type": "object",
  "required": [
    "app"
  ],
  "title": "HealthCheckApp"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-healthchecks3'></a> `HealthCheckS3`

```json
{
  "properties": {
    "s3": {
      "type": "string",
      "title": "S3",
      "description": "Статус S3"
    },
    "bucket": {
      "type": "string",
      "title": "Bucket",
      "description": "Имя бакета"
    }
  },
  "type": "object",
  "required": [
    "s3",
    "bucket"
  ],
  "title": "HealthCheckS3"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-modelconfig'></a> `ModelConfig`

```json
{
  "properties": {
    "hyperparameters": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/GBRHParams"
        },
        {
          "$ref": "#/components/schemas/ElasticNetParams"
        }
      ],
      "title": "Hyperparameters",
      "description": "Гиперпараметры модели"
    },
    "model_class": {
      "type": "string",
      "enum": [
        "GradientBoostingRegressor",
        "ElasticNet"
      ],
      "title": "Model Class",
      "description": "Класс модели"
    }
  },
  "type": "object",
  "required": [
    "hyperparameters",
    "model_class"
  ],
  "title": "ModelConfig"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-modeldescription'></a> `ModelDescription`

```json
{
  "properties": {
    "name": {
      "type": "string",
      "enum": [
        "ElasticNet",
        "GradientBoostingRegressor"
      ],
      "title": "Name",
      "description": "Название модели"
    },
    "hyperparameters": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/GBRHParams"
        },
        {
          "$ref": "#/components/schemas/ElasticNetParams"
        }
      ],
      "title": "Hyperparameters",
      "description": "Гиперпараметры модели"
    }
  },
  "type": "object",
  "required": [
    "name",
    "hyperparameters"
  ],
  "title": "ModelDescription"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-modelpred'></a> `ModelPred`

```json
{
  "properties": {
    "predictions": {
      "items": {
        "type": "number"
      },
      "type": "array",
      "title": "Predictions",
      "description": "Предсказания модели"
    }
  },
  "type": "object",
  "required": [
    "predictions"
  ],
  "title": "ModelPred"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-modelscore'></a> `ModelScore`

```json
{
  "properties": {
    "name": {
      "type": "string",
      "enum": [
        "R2",
        "MSE",
        "MAE"
      ],
      "title": "Name",
      "description": "Название метрики"
    },
    "value": {
      "type": "number",
      "title": "Value",
      "description": "Значение метрики"
    }
  },
  "type": "object",
  "required": [
    "name",
    "value"
  ],
  "title": "ModelScore"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-runconfig'></a> `RunConfig`

```json
{
  "properties": {
    "preprocessing_config": {
      "$ref": "#/components/schemas/DatasetPreprocessing",
      "description": "Конфигурация предобработки данных"
    },
    "ml_config": {
      "$ref": "#/components/schemas/ModelConfig",
      "description": "Конфигурация модели"
    }
  },
  "type": "object",
  "required": [
    "preprocessing_config",
    "ml_config"
  ],
  "title": "RunConfig"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-uploaddatasetresponse'></a> `UploadDatasetResponse`

```json
{
  "properties": {
    "user_id": {
      "type": "string",
      "title": "User Id",
      "description": "Идентификатор пользователя"
    },
    "data_id": {
      "type": "string",
      "title": "Data Id",
      "description": "Идентификатор датасета"
    },
    "filename": {
      "type": "string",
      "title": "Filename",
      "description": "Имя файла"
    }
  },
  "type": "object",
  "required": [
    "user_id",
    "data_id",
    "filename"
  ],
  "title": "UploadDatasetResponse"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-userdatasets'></a> `UserDatasets`

```json
{
  "properties": {
    "user_id": {
      "type": "string",
      "title": "User Id",
      "description": "Идентификатор пользователя"
    },
    "datasets": {
      "items": {
        "$ref": "#/components/schemas/DatasetInfo"
      },
      "type": "array",
      "title": "Datasets",
      "description": "Список датасетов пользователя"
    }
  },
  "type": "object",
  "required": [
    "user_id",
    "datasets"
  ],
  "title": "UserDatasets"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-usermodels'></a> `UserModels`

```json
{
  "properties": {
    "user_id": {
      "type": "string",
      "title": "User Id",
      "description": "Идентификатор пользователя"
    },
    "data_id": {
      "type": "string",
      "title": "Data Id",
      "description": "Идентификатор датасета"
    },
    "models": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "title": "Models",
      "description": "Список моделей"
    }
  },
  "type": "object",
  "required": [
    "user_id",
    "data_id",
    "models"
  ],
  "title": "UserModels"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-userscores'></a> `UserScores`

```json
{
  "properties": {
    "user_id": {
      "type": "string",
      "title": "User Id",
      "description": "Идентификатор пользователя"
    },
    "data_id": {
      "type": "string",
      "title": "Data Id",
      "description": "Идентификатор датасета"
    },
    "scores": {
      "items": {
        "$ref": "#/components/schemas/FitResult"
      },
      "type": "array",
      "title": "Scores",
      "description": "Список результатов обучения"
    }
  },
  "type": "object",
  "required": [
    "user_id",
    "data_id",
    "scores"
  ],
  "title": "UserScores"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-userstorage'></a> `UserStorage`

```json
{
  "properties": {
    "user_id": {
      "type": "string",
      "title": "User Id",
      "description": "Идентификатор пользователя"
    },
    "usage_mb": {
      "type": "number",
      "title": "Usage Mb",
      "description": "Использование хранилища в МБ"
    }
  },
  "type": "object",
  "required": [
    "user_id",
    "usage_mb"
  ],
  "title": "UserStorage"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---

#### <a id='schema-validationerror'></a> `ValidationError`

```json
{
  "properties": {
    "loc": {
      "items": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "integer"
          }
        ]
      },
      "type": "array",
      "title": "Location"
    },
    "msg": {
      "type": "string",
      "title": "Message"
    },
    "type": {
      "type": "string",
      "title": "Error Type"
    }
  },
  "type": "object",
  "required": [
    "loc",
    "msg",
    "type"
  ],
  "title": "ValidationError"
}
```

[⬆К списку эндпоинтов](#fastapi-endpoints)


---
