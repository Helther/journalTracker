import os

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class DBConfig(BaseSettings):
    """
    Настройки подключения и инициализации БД.
    Читаются из переменных окружения:
        DB_HOST, DB_PORT, DB_ADMIN_USER, DB_ADMIN_PASSWORD,
        DB_APP_USER, DB_APP_PASSWORD, DB_NAME
    """

    host: str = os.environ.get('DB_HOST', "localhost")
    port: int = os.environ.get('DB_PORT', 5432)

    admin_user: str = os.environ.get('DB_ADMIN_USER', "postgres")
    admin_password: SecretStr = SecretStr(os.environ.get('DB_ADMIN_PASSWORD', "postgres"))
    # TODO fix role persmissions
    app_user: str = admin_user
    app_password: SecretStr = admin_password

    database: str = os.environ.get('DB_NAME', "log_service_db")

    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=100)
    echo: bool = False
    statement_timeout_ms: int = Field(default=30_000, ge=0)
    db_wait_timeout_s: int = Field(default=120, ge=0)
    