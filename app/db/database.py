"""Класс Database: соединение, инициализация пользователя/БД/схемы,
фабрика сессий.

Использование:

    cfg = DBConfig()
    db = Database(cfg)
    await db.init()                    # один раз при старте (или из CLI)
    async with db.session() as s:      # рабочая сессия
        ...
    await db.dispose()

Или как асинхронный контекст-менеджер:

    async with Database(cfg) as db:
        async with db.session() as s:
            ...
"""

from __future__ import annotations

import logging
import re
from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.config import DBConfig
from app.db.schema import DDL_STATEMENTS

logger = logging.getLogger(__name__)

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")


class Database:
    """Всё, что связано с PostgreSQL: подключение, инициализация, сессии."""

    def __init__(self, config: DBConfig) -> None:
        self.config = config
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

        self._assert_identifier(config.app_user, "app_user")
        self._assert_identifier(config.database, "database")

    @property
    def app_dsn(self) -> str:
        """DSN для приложения (async-драйвер asyncpg)."""
        c = self.config
        pwd = c.app_password.get_secret_value()
        return (
            f"postgresql+asyncpg://{c.app_user}:{pwd}"
            f"@{c.host}:{c.port}/{c.database}"
        )

    def _admin_dsn(self, database: str = "postgres") -> str:
        """DSN для администратора. asyncpg понимает только 'postgresql://'."""
        c = self.config
        pwd = c.admin_password.get_secret_value()
        auth = f"{c.admin_user}:{pwd}" if pwd else c.admin_user
        return f"postgresql://{auth}@{c.host}:{c.port}/{database}"


    def connect(self) -> None:
        """Создать engine и фабрику сессий. Идемпотентно."""
        if self._engine is not None:
            return

        self._engine = create_async_engine(
            self.app_dsn,
            echo=self.config.echo,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_pre_ping=True,
            pool_recycle=1800,
            connect_args={
                "server_settings": {
                    "application_name": "log-service",
                    "statement_timeout": str(self.config.statement_timeout_ms),
                    "timezone": "UTC",
                },
            },
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        logger.info(
            "DB engine created: %s@%s:%s/%s",
            self.config.app_user, self.config.host, self.config.port,
            self.config.database,
        )

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("DB engine disposed")

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Транзакционная сессия: commit при успехе, rollback при исключении."""
        if self._session_factory is None:
            raise RuntimeError("Database.connect() must be called first")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def healthcheck(self) -> bool:
        if self._engine is None:
            return False
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            logger.exception("DB healthcheck failed")
            return False

    async def init(self) -> None:
        """Полная инициализация: роль → БД → engine → схема.

        Требует прав суперпользователя (или CREATEDB + CREATEROLE).
        Идемпотентна — повторный вызов ничего не ломает.
        """
        await self._init_role()
        await self._init_database()
        self.connect()
        await self._init_schema()

    async def _init_role(self) -> None:
        """Создать роль приложения, если её нет."""
        conn = await asyncpg.connect(self._admin_dsn())
        try:
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_roles WHERE rolname = $1",
                self.config.app_user,
            )
            if exists:
                logger.info("Role %s already exists", self.config.app_user)
                return

            pwd = self._q_literal(self.config.app_password.get_secret_value())
            await conn.execute(
                f'CREATE ROLE "{self.config.app_user}" '
                f"WITH LOGIN PASSWORD {pwd}"
            )
            logger.info("Created role %s", self.config.app_user)
        finally:
            await conn.close()

    async def _init_database(self) -> None:
        """Создать БД, если её нет. CREATE DATABASE нельзя в транзакции —
        поэтому asyncpg.execute (simple query) без явного BEGIN."""
        conn = await asyncpg.connect(self._admin_dsn())
        try:
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                self.config.database,
            )
            if exists:
                logger.info("Database %s already exists", self.config.database)
                return

            await conn.execute(
                f'CREATE DATABASE "{self.config.database}" '
                f'OWNER "{self.config.app_user}" '
                f"ENCODING 'UTF8'"
            )
            logger.info("Created database %s", self.config.database)
        finally:
            await conn.close()

    async def _init_schema(self) -> None:
        """Создать таблицы, индексы и триггеры. Идемпотентно."""
        assert self._engine is not None
        async with self._engine.begin() as conn:
            for stmt in DDL_STATEMENTS:
                await conn.execute(text(stmt))
        logger.info("Schema initialized (%d statements)", len(DDL_STATEMENTS))


    @staticmethod
    def _assert_identifier(value: str, name: str) -> None:
        if not _IDENT_RE.match(value):
            raise ValueError(
                f"Invalid identifier {name}={value!r}: "
                "must match ^[A-Za-z_][A-Za-z0-9_]{0,62}$"
            )

    @staticmethod
    def _q_literal(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    async def __aenter__(self) -> "Database":
        self.connect()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.dispose()
        