"""Tests for decision cutoff calculation."""

from datetime import date

import pandas as pd

from app.services.cutoff import decision_cutoff_utc


def test_cutoff_is_previous_day_0920_london_in_january_gmt() -> None:
    # January: UK is on GMT, so 09:20 London equals 09:20 UTC.
    cutoff = decision_cutoff_utc(date(2026, 1, 1))
    assert cutoff == pd.Timestamp("2025-12-31T09:20:00Z")
