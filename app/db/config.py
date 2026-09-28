from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBConfig(BaseSettings):
    """
    Настройки подключения и инициализации БД.
    Читаются из переменных окружения:
        DB_HOST, DB_PORT, DB_ADMIN_USER, DB_ADMIN_PASSWORD,
        DB_APP_USER, DB_APP_PASSWORD, DB_NAME, DB_WAIT_TIMEOUT
    """
    # TODO

    host: str = "localhost"
    port: int = 5432

    admin_user: str = "postgres"
    admin_password: SecretStr = SecretStr("")

    app_user: str = "log_service"
    app_password: SecretStr = SecretStr("log_service")

    database: str = "log_service_db"

    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=100)
    echo: bool = False
    statement_timeout_ms: int = Field(default=30_000, ge=0)
    db_wait_timeout_s: int = Field(default=120, ge=0)
    