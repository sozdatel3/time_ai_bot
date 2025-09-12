from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_mixin

MOSCOW_OFFSET = timedelta(hours=3)


@declarative_mixin
class TimestampMixin:
    MSK = timezone(timedelta(hours=3))
    # Заменяем DATETIME('now', '+3 hours') на datetime.utcnow
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(TimestampMixin.MSK),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(TimestampMixin.MSK),
        onupdate=lambda: datetime.now(TimestampMixin.MSK),
    )
