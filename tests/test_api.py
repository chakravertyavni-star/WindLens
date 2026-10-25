"""FastAPI route tests with mocked analysis."""

from datetime import date
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.services.analysis import AnalysisResult
from app.services.metrics import MetricResult


def _fake_result() -> AnalysisResult:
    matched = pd.DataFrame(
        {
            "hour_start": [pd.Timestamp("2026-01-01T12:00:00Z")],
            "settlement_date": [date(2026, 1, 1)],
            "actual_mw": [110.0],
            "forecast_mw": [90.0],
            "publish_time": [pd.Timestamp("2025-12-31T04:30:00Z")],
            "cutoff_utc": [pd.Timestamp("2025-12-31T09:20:00Z")],
            "forecast_error": [-20.0],
        },
    )
    return AnalysisResult(
        matched=matched,
        unmatched_hours=pd.DataFrame(),
        metrics=MetricResult(n=1, mae=20.0, rmse=20.0, bias=-20.0),
        actual_half_hours=2,
        hourly_actuals_complete=1,
        forecast_rows_january=2,
    )


@patch("app.main.run_analysis", return_value=_fake_result())
@patch("app.main.cached_settings")
def test_health(mock_settings, mock_analyse) -> None:
    mock_settings.return_value = Settings(
        elexon_base_url="https://example.test",
        delivery_start=date(2026, 1, 1),
        delivery_end=date(2026, 1, 31),
        decision_cutoff_local_time="09:20",
        decision_cutoff_timezone="Europe/London",
        windfor_publish_from="2025-12-25T00:00:00Z",
        windfor_publish_to="2026-01-31T23:59:59Z",
        elexon_source_cache_ttl_seconds=3600.0,
        cors_allowed_origins=("*",),
    )
    client = TestClient(app)
    assert client.get("/api/health").json() == {"status": "ok"}


@patch("app.main.run_analysis", return_value=_fake_result())
@patch("app.main.cached_settings")
def test_metrics_endpoint(mock_settings, mock_analyse) -> None:
    mock_settings.return_value = Settings(
        elexon_base_url="https://example.test",
        delivery_start=date(2026, 1, 1),
        delivery_end=date(2026, 1, 31),
        decision_cutoff_local_time="09:20",
        decision_cutoff_timezone="Europe/London",
        windfor_publish_from="2025-12-25T00:00:00Z",
        windfor_publish_to="2026-01-31T23:59:59Z",
        elexon_source_cache_ttl_seconds=3600.0,
        cors_allowed_origins=("*",),
    )
    client = TestClient(app)
    body = client.get("/api/metrics").json()
    assert body["metrics"]["n"] == 1
    assert body["metrics"]["mae"] == 20.0
    assert body["coverage"]["matched_hourly_pairs"] == 1
