"""UTC time helpers for consistent, timezone-aware timestamps."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(UTC)


def utc_now_iso_z() -> str:
    """Return current UTC timestamp in ISO-8601 with trailing Z."""
    return utc_now().isoformat().replace("+00:00", "Z")
