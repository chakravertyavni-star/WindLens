"""Tests for hourly aggregation and matching pipeline."""

from app.services.analysis import analyse_from_frames
from app.services.matching import build_hourly_actuals, fuelhh_to_dataframe


def test_hourly_actual_requires_both_half_hours(synthetic_fuelhh_rows) -> None:
    actuals = fuelhh_to_dataframe(synthetic_fuelhh_rows)
    hourly = build_hourly_actuals(actuals)
    assert len(hourly) == 1
    assert hourly.iloc[0]["actual_mw"] == 110.0


def test_synthetic_pipeline_uses_pre_cutoff_forecast(
    synthetic_fuelhh_rows,
    synthetic_windfor_rows,
    default_settings,
) -> None:
    result = analyse_from_frames(
        synthetic_fuelhh_rows,
        synthetic_windfor_rows,
        default_settings,
    )
    assert len(result.matched) == 1
    row = result.matched.iloc[0]
    assert row["forecast_mw"] == 90.0
    assert row["actual_mw"] == 110.0
    assert row["forecast_error"] == -20.0
    assert result.metrics.n == 1
    assert result.metrics.mae == 20.0
