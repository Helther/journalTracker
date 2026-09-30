from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.session import get_session
from app.db.schema_entries import (
    DeleteResult,
    InsertResult,
    LogEntryIn,
    LogPage,
)
from app.service import LogService

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])

BATCH_MAX_SIZE = 1000


@router.post("", status_code=201, response_model=InsertResult)
async def insert_logs(
    payload: Annotated[
        list[LogEntryIn],
        Body(min_length=1, max_length=BATCH_MAX_SIZE),
    ],
    session: AsyncSession = Depends(get_session),
) -> InsertResult:
    """Вставка записи или батча (одна транзакция, всё или ничего)."""
    service = LogService(session)
    inserted = await service.insert(payload)
    return InsertResult(inserted=inserted)


@router.get("", response_model=LogPage)
async def list_logs(
    application: Annotated[str, Query(min_length=1, max_length=255)],
    dt_from: Annotated[datetime | None, Query(alias="from")] = None,
    dt_to: Annotated[datetime | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    session: AsyncSession = Depends(get_session),
) -> LogPage:
    if dt_from and dt_to and dt_from > dt_to:
        raise HTTPException(status_code=400, detail="'from' must be <= 'to'")

    service = LogService(session)
    items, total = await service.list_logs(
        application=application,
        dt_from=dt_from,
        dt_to=dt_to,
        limit=limit,
        offset=offset,
        descending=(order == "desc"),
    )
    return LogPage(items=items, total=total, limit=limit, offset=offset)


@router.delete("", response_model=DeleteResult)
async def delete_logs(
    application: Annotated[str, Query(min_length=1, max_length=255)],
    dt_from: Annotated[datetime | None, Query(alias="from")] = None,
    dt_to: Annotated[datetime | None, Query(alias="to")] = None,
    session: AsyncSession = Depends(get_session)
) -> DeleteResult:
    if dt_from and dt_to and dt_from > dt_to:
        raise HTTPException(status_code=400, detail="'from' must be <= 'to'")
    
    service = LogService(session)
    deleted_row_count: int = await service.delete_logs(application, dt_from, dt_to)
    return DeleteResult(deleted=deleted_row_count)


@router.delete("/all", response_model=DeleteResult)
async def delete_all_logs(
    session: AsyncSession = Depends(get_session)
) -> DeleteResult:
    service = LogService(session)
    deleted_row_count: int = await service.truncate_all()
    return DeleteResult(deleted=deleted_row_count)
