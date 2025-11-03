from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import cached_property

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
    s3_max_attempts: int = Field(5, description="Максимальное кол-во попыток подключения к S3")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @cached_property
    def s3_endpoint(self) -> str:
        return f"http://{self.s3_host}:{self.s3_port}"

settings = Settings()