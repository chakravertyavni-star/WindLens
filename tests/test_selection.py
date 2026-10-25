"""Tests for as-of forecast selection."""

import pandas as pd

from app.services.selection import select_latest_eligible_forecast


def test_selects_latest_before_cutoff_not_after() -> None:
    delivery = pd.Timestamp("2026-01-01T12:00:00Z")
    cutoff = pd.Timestamp("2025-12-31T09:20:00Z")
    forecasts = pd.DataFrame(
        [
            {
                "start_time": delivery,
                "publish_time": pd.Timestamp("2025-12-31T04:30:00Z"),
                "forecast_mw": 90.0,
            },
            {
                "start_time": delivery,
                "publish_time": pd.Timestamp("2025-12-31T11:30:00Z"),
                "forecast_mw": 999.0,
            },
        ],
    )
    row = select_latest_eligible_forecast(forecasts, delivery, cutoff)
    assert row is not None
    assert row["forecast_mw"] == 90.0


def test_rejects_forecast_after_cutoff() -> None:
    delivery = pd.Timestamp("2026-01-01T12:00:00Z")
    cutoff = pd.Timestamp("2025-12-31T09:20:00Z")
    forecasts = pd.DataFrame(
        [
            {
                "start_time": delivery,
                "publish_time": pd.Timestamp("2025-12-31T11:30:00Z"),
                "forecast_mw": 50.0,
            },
        ],
    )
    assert select_latest_eligible_forecast(forecasts, delivery, cutoff) is None
