from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.session import get_session
from app.db.schema_entries import CounterOut
from app.service import LogService

router = APIRouter(prefix="/api/v1/counters", tags=["counters"])


@router.get("", response_model=list[CounterOut])
async def list_counters(
    application: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    session: AsyncSession = Depends(get_session),
) -> list[CounterOut]:
    service = LogService(session)
    if application is not None:
        counter = await service.get_counter(application)
        if counter is None:
            raise HTTPException(status_code=404, detail="application not found")
        return [CounterOut.model_validate(counter)]
    counters = await service.list_counters()
    return [CounterOut.model_validate(c) for c in counters]


@router.get("/{application}", response_model=CounterOut)
async def get_counter(
    application: str,
    session: AsyncSession = Depends(get_session),
) -> CounterOut:
    service = LogService(session)
    counter = await service.get_counter(application)
    if counter is None:
        raise HTTPException(status_code=404, detail="application not found")
    return CounterOut.model_validate(counter)