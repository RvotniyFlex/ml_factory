from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    s3_access_key: str = Field(description="Access key S3")
    s3_secret_key: str = Field(description="Secret key S3")
    s3_bucket: str = Field(description="Название бакета с S3 ML моделями")
    s3_region: str = Field(description="Регион S3")
    s3_host: str = Field(description="Хост S3")
    s3_port: int = Field(description="Порт S3")
    s3_connect_timeout: int = Field(5, description="Время подключения к S3")
    s3_read_timeout: int = Field(10, description="Время чтения из S3")
    s3_max_pool: int = Field(5, description="Максимальное кол-во подключений S3")
    s3_max_attempts: int = Field(
        5, description="Максимальное кол-во попыток подключения к S3"
    )
    google_client_id: str = Field(
        description="Айди приложения авторизации oauth Google"
    )
    google_client_id: str = Field(description="Секрет Google разработчика")
    google_redirect_uri: str = Field(description="Ссылка для авторизации")
    jwt_secret: str = Field(description="Внутренний хэш авторизации")
    jwt_algorithm: str = Field(
        description="Способ создания внутреннего ключа авторизации"
    )
    jwt_expire_hours: int = Field(2, description="Сколько часов работает ключ")
    session_secret: str = Field(description="Секрет сессии пользователя")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @cached_property
    def s3_endpoint(self) -> str:
        return f"http://{self.s3_host}:{self.s3_port}"


settings = Settings()
