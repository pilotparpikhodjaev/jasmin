from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    db_url: str = Field(
        default="postgresql+asyncpg://otp:otp-secret@postgres:5432/otp", alias="BILLING_DB_URL"
    )
    db_pool_min: int = Field(default=1, alias="BILLING_DB_POOL_MIN")
    db_pool_max: int = Field(default=5, alias="BILLING_DB_POOL_MAX")
    port: int = Field(default=8081, alias="BILLING_PORT")

    jasmin_amqp_host: str = Field(default="rabbitmq", alias="BILLING_JASMIN_AMQP_HOST")
    jasmin_amqp_port: int = Field(default=5672, alias="BILLING_JASMIN_AMQP_PORT")
    jasmin_amqp_user: str = Field(default="guest", alias="BILLING_JASMIN_AMQP_USER")
    jasmin_amqp_password: str = Field(default="guest", alias="BILLING_JASMIN_AMQP_PASSWORD")
    jasmin_amqp_vhost: str = Field(default="/", alias="BILLING_JASMIN_AMQP_VHOST")

    log_level: str = Field(default="INFO", alias="BILLING_LOG_LEVEL")


@lru_cache
def get_settings() -> Settings:
    return Settings()

