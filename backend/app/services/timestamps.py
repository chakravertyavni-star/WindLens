"""Parse and normalise Elexon timestamps."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def parse_utc(value: str | None) -> pd.Timestamp:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise ValueError("Missing timestamp")
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts


def to_utc_iso(ts: pd.Timestamp) -> str:
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts.isoformat().replace("+00:00", "Z")
