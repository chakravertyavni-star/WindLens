"""Live Elexon integration — real API, not synthetic."""

from datetime import date

import pytest

from app.clients.elexon import ElexonClient
from app.config import Settings
from app.services.analysis import analyse_from_frames


@pytest.mark.integration
def test_january_2026_live_pipeline_produces_matches() -> None:
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
    assert result.actual_half_hours == 1488
    assert result.hourly_actuals_complete == 744
    assert result.forecast_rows_january > 0
    assert result.metrics.n > 0
    assert result.metrics.mae is not None
    assert result.metrics.rmse is not None
    assert result.metrics.bias is not None
