from decimal import Decimal
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Server
    port: int = Field(default=8080, alias="API_GATEWAY_PORT")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # Jasmin
    jasmin_http_url: str = Field(default="http://jasmin:8990", alias="API_GATEWAY_JASMIN_HTTP_URL")
    jasmin_jcli_url: str = Field(default="http://jasmin:8991", alias="API_GATEWAY_JASMIN_JCLI_URL")
    jasmin_user: str = Field(default="otp_api", alias="API_GATEWAY_JASMIN_USER")
    jasmin_password: str = Field(default="otp_api_secret", alias="API_GATEWAY_JASMIN_PASSWORD")

    # Billing Service
    billing_url: str = Field(default="http://billing-service:8081", alias="API_GATEWAY_BILLING_URL")

    # Routing Service
    routing_service_url: str = Field(default="http://routing-service:8082", alias="API_GATEWAY_ROUTING_URL")

    # Redis
    redis_host: str = Field(default="redis", alias="API_GATEWAY_REDIS_HOST")
    redis_port: int = Field(default=6379, alias="API_GATEWAY_REDIS_PORT")
    redis_db: int = Field(default=0, alias="API_GATEWAY_REDIS_DB")

    # JWT Authentication
    jwt_secret_key: str = Field(default="change-me-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_days: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_DAYS")
    jwt_refresh_token_expire_days: int = Field(default=90, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")

    # Defaults
    default_currency: str = Field(default="UZS", alias="API_GATEWAY_DEFAULT_CURRENCY")
    default_price_per_part: Decimal = Field(default=Decimal("50.0"), alias="API_GATEWAY_DEFAULT_PRICE_PER_SMS")
    rate_limit_rps: int = Field(default=50, alias="API_GATEWAY_RATE_LIMIT_RPS")

    default_sender: str = Field(default="OTP", alias="API_GATEWAY_DEFAULT_SENDER")
    default_dlr_callback: str | None = Field(
        default="http://api-gateway:8080/api/webhooks/dlr", alias="API_GATEWAY_DEFAULT_DLR_CALLBACK"
    )

    # Admin
    admin_api_token: str = Field(default="change-me", alias="API_GATEWAY_ADMIN_TOKEN")


@lru_cache
def get_settings() -> Settings:
    return Settings()

