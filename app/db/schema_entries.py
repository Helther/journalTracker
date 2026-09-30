from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LogEntryIn(BaseModel):
    application: str = Field(min_length=1, max_length=255)
    event_time: datetime
    message: str = Field(min_length=1)

    @field_validator("event_time")
    @classmethod
    def _ensure_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("event_time must be timezone-aware (UTC)")
        return v.astimezone(timezone.utc)


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
    