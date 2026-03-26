from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_utc(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)
