"""Tests for MAE, RMSE, and bias — synthetic numbers only."""

import pandas as pd

from app.services.metrics import compute_metrics


def test_metrics_synthetic_example_from_assignment() -> None:
    matched = pd.DataFrame(
        {
            "forecast_mw": [100.0, 80.0],
            "actual_mw": [90.0, 100.0],
        },
    )
    result = compute_metrics(matched)
    assert result.n == 2
    assert result.mae == 15.0
    assert result.bias == -5.0
    assert abs(result.rmse - 15.811388) < 0.001


def test_metrics_empty_returns_none_values() -> None:
    result = compute_metrics(pd.DataFrame(columns=["forecast_mw", "actual_mw"]))
    assert result.n == 0
    assert result.mae is None
