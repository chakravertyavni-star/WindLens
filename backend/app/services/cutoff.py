"""Decision cutoff in Europe/London, compared in UTC."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd


def parse_cutoff_clock(clock: str) -> time:
    hour, minute = clock.split(":")
    return time(hour=int(hour), minute=int(minute))


def decision_cutoff_utc(
    settlement_date: date,
    *,
    cutoff_clock: str = "09:20",
    tz_name: str = "Europe/London",
) -> pd.Timestamp:
    """Cutoff on the calendar day before UK settlement date, in local time."""
    zone = ZoneInfo(tz_name)
    local_day_before = settlement_date - timedelta(days=1)
    clock = parse_cutoff_clock(cutoff_clock)
    local_dt = datetime.combine(local_day_before, clock, tzinfo=zone)
    return pd.Timestamp(local_dt.astimezone(timezone.utc))
