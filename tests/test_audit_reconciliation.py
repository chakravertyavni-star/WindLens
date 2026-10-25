"""Analytical correctness: metrics, selection, and cutoff invariants."""

from __future__ import annotations

import math
from datetime import date

import pandas as pd
import pytest

from app.services.cutoff import decision_cutoff_utc
from app.services.matching import run_matching, windfor_to_dataframe, fuelhh_to_dataframe
from app.services.metrics import compute_metrics
from app.services.selection import select_latest_eligible_forecast


def test_selects_latest_eligible_not_earliest() -> None:
    delivery = pd.Timestamp("2026-01-01T12:00:00Z")
    cutoff = pd.Timestamp("2025-12-31T12:00:00Z")
    forecasts = pd.DataFrame(
        [
            {
                "start_time": delivery,
                "publish_time": pd.Timestamp("2025-12-31T04:30:00Z"),
                "forecast_mw": 80.0,
            },
            {
                "start_time": delivery,
                "publish_time": pd.Timestamp("2025-12-31T09:30:00Z"),
                "forecast_mw": 95.0,
            },
        ],
    )
    row = select_latest_eligible_forecast(forecasts, delivery, cutoff)
    assert row is not None
    assert row["forecast_mw"] == 95.0
    assert row["publish_time"] == pd.Timestamp("2025-12-31T09:30:00Z")


def test_metrics_match_independent_series_calculation() -> None:
    matched = pd.DataFrame(
        {
            "forecast_mw": [100.0, 120.0, 80.0],
            "actual_mw": [90.0, 100.0, 100.0],
            "forecast_error": [10.0, 20.0, -20.0],
        },
    )
    result = compute_metrics(matched)
    errors = matched["forecast_mw"] - matched["actual_mw"]
    assert (errors - matched["forecast_error"]).abs().max() == 0.0
    assert result.n == 3
    assert result.mae == pytest.approx(float(errors.abs().mean()))
    assert result.bias == pytest.approx(float(errors.mean()))
    assert result.rmse == pytest.approx(math.sqrt(float((errors**2).mean())))


def test_pipeline_matched_rows_respect_cutoff(
    synthetic_fuelhh_rows,
    synthetic_windfor_rows,
) -> None:
    actuals = fuelhh_to_dataframe(synthetic_fuelhh_rows)
    forecasts = windfor_to_dataframe(synthetic_windfor_rows)
    matched, _ = run_matching(
        actuals,
        forecasts,
        cutoff_clock="09:20",
        cutoff_tz="Europe/London",
    )
    assert len(matched) == 1
    row = matched.iloc[0]
    assert row["publish_time"] <= row["cutoff_utc"]
    assert row["cutoff_utc"] == decision_cutoff_utc(date(2026, 1, 1))


def test_cutoff_uses_settlement_date_not_utc_hour_date() -> None:
    """Cutoff is day-before settlement_date (UK), verified for a winter delivery hour."""
    cutoff = decision_cutoff_utc(date(2026, 1, 15))
    assert cutoff == pd.Timestamp("2026-01-14T09:20:00Z")


@pytest.mark.integration
def test_live_metrics_equal_recomputed_from_matched() -> None:
    from app.clients.elexon import ElexonClient
    from app.config import Settings
    from app.services.analysis import analyse_from_frames
    from app.services.selection import select_latest_eligible_forecast
    from app.services.matching import windfor_to_dataframe, filter_delivery_window

    settings = Settings(
        elexon_base_url="https://data.elexon.co.uk/bmrs/api/v1",
        delivery_start=date(2026, 1, 1),
        delivery_end=date(2026, 1, 31),
        decision_cutoff_local_time="09:20",
        decision_cutoff_timezone="Europe/London",
        windfor_publish_from="2025-12-25T00:00:00Z",
        windfor_publish_to="2026-01-31T23:59:59Z",
        elexon_source_cache_ttl_seconds=3600.0,
        cors_allowed_origins=("*",),
    )
    client = ElexonClient(settings.elexon_base_url)
    fuelhh = client.fetch_fuelhh_wind(settings.delivery_start, settings.delivery_end)
    windfor = client.fetch_windfor_by_publish_window(
        settings.windfor_publish_from,
        settings.windfor_publish_to,
    )
    result = analyse_from_frames(fuelhh, windfor, settings)
    matched = result.matched
    errors = matched["forecast_mw"] - matched["actual_mw"]
    assert result.metrics.n == len(matched) == 744
    assert result.metrics.mae == pytest.approx(float(errors.abs().mean()))
    assert result.metrics.bias == pytest.approx(float(errors.mean()))
    assert result.metrics.rmse == pytest.approx(math.sqrt(float((errors**2).mean())))
    assert matched["hour_start"].duplicated().sum() == 0
    assert (matched["publish_time"] <= matched["cutoff_utc"]).all()

    forecasts = filter_delivery_window(
        windfor_to_dataframe(windfor),
        settings.delivery_start,
        settings.delivery_end,
    )
    for _, row in matched.iterrows():
        sel = select_latest_eligible_forecast(
            forecasts,
            row["hour_start"],
            row["cutoff_utc"],
        )
        assert sel is not None
        assert sel["forecast_mw"] == row["forecast_mw"]
        assert sel["publish_time"] == row["publish_time"]
