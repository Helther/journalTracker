from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model_entries import LogEntry, ApplicationCounter
from app.db.schema_entries import LogEntryIn


class LogService:
    """Единая точка доступа к БД для логов и счётчиков.

    SQL-запросы тут. Сессия приходит извне,
    commit/rollback делает контекст-менеджер Database.session().
    Счётчики обновляются триггерами в БД.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --------------------------------------------------------------- INSERT

    async def insert(self, entries: list[LogEntryIn]) -> int:
        """Один INSERT ... VALUES (...),(...),... триггер обновит счётчики."""
        if not entries:
            return 0

        stmt = insert(LogEntry).values(
            [
                {
                    "application": e.application,
                    "event_time": e.event_time,
                    "message": e.message,
                }
                for e in entries
            ]
        )
        result = await self.session.execute(stmt)
        return int(result.rowcount or 0)

    # ----------------------------------------------------------------- LIST

    async def list_logs(
        self,
        application: str,
        dt_from: datetime | None,
        dt_to: datetime | None,
        limit: int,
        offset: int,
        descending: bool,
    ) -> tuple[list[LogEntry], int]:
        """Список записей + общее количество.
        Индексы:
          - ix_log_entries_app_time (application, event_time DESC)
            покрывает и COUNT (index-only scan), и выборку c сортировкой;
          - Sort-узел в плане не появляется при order by event_time DESC.

        Доп. ключ id в ORDER BY для стабильной пагинации при
        одинаковых event_time.
        """
        conditions = [LogEntry.application == application]
        if dt_from is not None:
            conditions.append(LogEntry.event_time >= dt_from)
        if dt_to is not None:
            conditions.append(LogEntry.event_time <= dt_to)

        total = (
            await self.session.execute(
                select(func.count())
                .select_from(LogEntry)
                .where(*conditions)
            )
        ).scalar_one()

        order_col = (
            LogEntry.event_time.desc() if descending
            else LogEntry.event_time.asc()
        )
        id_col = LogEntry.id.desc() if descending else LogEntry.id.asc()

        stmt = (
            select(LogEntry)
            .where(*conditions)
            .order_by(order_col, id_col)
            .limit(limit)
            .offset(offset)
        )
        items = list((await self.session.execute(stmt)).scalars().all())
        return items, int(total)

    # --------------------------------------------------------------- DELETE

    async def delete_logs(
        self,
        application: str,
        dt_from: datetime | None,
        dt_to: datetime | None,
    ) -> int:
        """
        AFTER DELETE-триггер уменьшит счётчик в этой же транзакции.
        """
        conditions = [LogEntry.application == application]
        if dt_from is not None:
            conditions.append(LogEntry.event_time >= dt_from)
        if dt_to is not None:
            conditions.append(LogEntry.event_time <= dt_to)

        stmt = delete(LogEntry).where(*conditions)
        result = await self.session.execute(stmt)
        return int(result.rowcount or 0)

    # -------------------------------------------------------------- TRUNCATE

    async def truncate_all(self) -> int:
        """Полная очистка.

        AFTER TRUNCATE-триггер сам очистит application_counters.
        """
        total = (
            await self.session.execute(
                select(func.count()).select_from(LogEntry)
            )
        ).scalar_one()

        await self.session.execute(text("TRUNCATE log_entries"))
        return int(total)

    # -------------------------------------------------------------- COUNTERS
    async def list_counters(self) -> list[ApplicationCounter]:
        stmt = select(ApplicationCounter).order_by(ApplicationCounter.application)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_counter(self, application: str) -> ApplicationCounter | None:
        stmt = select(ApplicationCounter).where(
            ApplicationCounter.application == application
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()
    