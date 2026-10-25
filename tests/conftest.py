"""Shared pytest fixtures. Synthetic data only — not Elexon observations."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from app.config import Settings


@pytest.fixture
def default_settings() -> Settings:
    return Settings(
        elexon_base_url="https://example.test/bmrs/api/v1",
        delivery_start=date(2026, 1, 1),
        delivery_end=date(2026, 1, 31),
        decision_cutoff_local_time="09:20",
        decision_cutoff_timezone="Europe/London",
        windfor_publish_from="2025-12-25T00:00:00Z",
        windfor_publish_to="2026-01-31T23:59:59Z",
        elexon_source_cache_ttl_seconds=3600.0,
        cors_allowed_origins=("*",),
    )


@pytest.fixture
def synthetic_fuelhh_rows() -> list[dict]:
    """Two half-hours for 2026-01-01 12:00 and 12:30 UTC — label: synthetic."""
    return [
        {
            "dataset": "FUELHH",
            "publishTime": "2026-01-01T12:30:00Z",
            "startTime": "2026-01-01T12:00:00Z",
            "settlementDate": "2026-01-01",
            "settlementPeriod": 25,
            "fuelType": "WIND",
            "generation": 100,
        },
        {
            "dataset": "FUELHH",
            "publishTime": "2026-01-01T13:00:00Z",
            "startTime": "2026-01-01T12:30:00Z",
            "settlementDate": "2026-01-01",
            "settlementPeriod": 26,
            "fuelType": "WIND",
            "generation": 120,
        },
    ]


@pytest.fixture
def synthetic_windfor_rows() -> list[dict]:
    """Two publishes for same hour — label: synthetic."""
    return [
        {
            "dataset": "WINDFOR",
            "publishTime": "2025-12-31T04:30:00Z",
            "startTime": "2026-01-01T12:00:00Z",
            "generation": 90,
        },
        {
            "dataset": "WINDFOR",
            "publishTime": "2025-12-31T11:30:00Z",
            "startTime": "2026-01-01T12:00:00Z",
            "generation": 999,
        },
    ]
