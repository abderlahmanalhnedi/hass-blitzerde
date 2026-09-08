"""Pure helpers for Blitzer.de report freshness."""

from __future__ import annotations

from datetime import datetime, timedelta


def minutes_since(stamp: object, now: datetime) -> int | None:
    """Return the report age in minutes for the upstream human timestamp.

    The upstream map uses HH:MM for reports from today and DD.MM.YYYY for
    older reports. A HH:MM value slightly ahead of the local clock is treated
    as yesterday, which avoids negative ages around midnight/server skew.
    """
    if not isinstance(stamp, str):
        return None

    text = stamp.strip()
    if not text:
        return None

    try:
        if ":" in text:
            hour, minute = (int(part) for part in text.split(":", 1))
            then = now.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0,
            )
            if then > now:
                then -= timedelta(days=1)
        else:
            day, month, year = (
                int(part) for part in text.split(".", 2)
            )
            then = now.replace(
                year=year,
                month=month,
                day=day,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
    except (TypeError, ValueError):
        return None

    return max(
        0,
        int((now - then).total_seconds() // 60),
    )


def is_new_report(
    stamp: object,
    now: datetime,
    window_minutes: int,
) -> bool:
    """Return whether a report falls inside the configured freshness window."""
    if window_minutes <= 0:
        return False
    age = minutes_since(stamp, now)
    return age is not None and age < window_minutes
