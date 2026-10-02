from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class LogEntry(Base):
    __tablename__ = "log_entries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    application: Mapped[str] = mapped_column(String(255), nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Индекс совпадает с DDL в app/db/schema.py
    __table_args__ = (
        Index("ix_log_entries_app_time", "application", "event_time",
              postgresql_ops={"event_time": "DESC"}),
        Index("ix_log_entries_time", "event_time"),
    )

class ApplicationCounter(Base):
    __tablename__ = "application_counters"

    application: Mapped[str] = mapped_column(String(255), primary_key=True)
    entries_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    