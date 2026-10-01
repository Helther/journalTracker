from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, BeforeValidator
from typing_extensions import Annotated
from typing import Any

def parse_datetime_or_unix(v: Any) -> Any:
    """Приводит int/float/str к timezone-aware datetime в UTC.

    Принимает:
      - int / float - Unix epoch в секундах
      - str с числом - тоже Unix;
      - ISO 8601 строку - отдаёт дальше, Pydantic распарсит сам;
      - datetime - пропускает как есть;
      - None - пропускает (для опциональных query-параметров).
    """
    if v is None or isinstance(v, datetime):
        return v

    if isinstance(v, bool):
        raise ValueError("must be Unix seconds or ISO 8601 datetime")

    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v, tz=timezone.utc)

    if isinstance(v, str):
        s = v.strip()
        if not s:
            raise ValueError("must not be empty")
        try:
            return datetime.fromtimestamp(float(s), tz=timezone.utc)
        except ValueError:
            return v

    return v

# Публичный тип для использования в схемах и query-параметрах.
UnixOrIsoDatetime = Annotated[datetime, BeforeValidator(parse_datetime_or_unix)]

class LogEntryIn(BaseModel):
    application: str = Field(min_length=1, max_length=255)
    event_time: UnixOrIsoDatetime
    message: str = Field(min_length=1)
    
class LogEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application: str
    event_time: datetime
    message: str


class LogPage(BaseModel):
    items: list[LogEntryOut]
    total: int
    limit: int
    offset: int


class InsertResult(BaseModel):
    inserted: int


class DeleteResult(BaseModel):
    deleted: int

class CounterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    application: str
    entries_count: int
    updated_at: datetime
