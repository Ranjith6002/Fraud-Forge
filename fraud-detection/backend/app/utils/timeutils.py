"""Small, dependency-free time helpers."""
from datetime import datetime, timezone
from typing import Any, Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: Any) -> Optional[datetime]:
    """Return a timezone-aware UTC datetime, or None if `value` is not a datetime.

    Naive datetimes (e.g. read back from SQLite) are assumed to already be UTC.
    """
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
