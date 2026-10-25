"""Tests for Elexon source-data TTL cache and run_analysis integration."""

from __future__ import annotations

import threading
import time

import pytest

from app.config import Settings
from app.main import run_analysis
from app.services.source_cache import (
    SourceDataCache,
    SourcePayload,
    reset_source_cache_for_tests,
    source_cache_key,
)
class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class CountingClient:
    def __init__(self, fuelhh: list, windfor: list) -> None:
        self.fuelhh = fuelhh
        self.windfor = windfor
        self.fetch_calls = 0
        self._lock = threading.Lock()

    def fetch_fuelhh_wind(self, _start, _end):
        with self._lock:
            self.fetch_calls += 1
        return self.fuelhh

    def fetch_windfor_by_publish_window(self, _a, _b):
        return self.windfor


@pytest.fixture
def cache_settings(default_settings) -> Settings:
    return Settings(
        elexon_base_url=default_settings.elexon_base_url,
        delivery_start=default_settings.delivery_start,
        delivery_end=default_settings.delivery_end,
        decision_cutoff_local_time=default_settings.decision_cutoff_local_time,
        decision_cutoff_timezone=default_settings.decision_cutoff_timezone,
        windfor_publish_from=default_settings.windfor_publish_from,
        windfor_publish_to=default_settings.windfor_publish_to,
        elexon_source_cache_ttl_seconds=300.0,
        cors_allowed_origins=("*",),
    )


@pytest.fixture(autouse=True)
def _reset_global_cache():
    reset_source_cache_for_tests()
    yield
    reset_source_cache_for_tests()


def test_repeated_load_within_ttl_fetches_once(
    cache_settings,
    synthetic_fuelhh_rows,
    synthetic_windfor_rows,
) -> None:
    clock = FakeClock()
    cache = SourceDataCache(300.0, clock=clock)
    key = source_cache_key(cache_settings)
    calls = {"n": 0}

    def fetch():
        calls["n"] += 1
        return SourcePayload(synthetic_fuelhh_rows, synthetic_windfor_rows)

    cache.load(key, fetch)
    cache.load(key, fetch)
    assert calls["n"] == 1


def test_expired_entry_refetches(cache_settings, synthetic_fuelhh_rows, synthetic_windfor_rows) -> None:
    clock = FakeClock()
    cache = SourceDataCache(100.0, clock=clock)
    key = source_cache_key(cache_settings)
    calls = {"n": 0}

    def fetch():
        calls["n"] += 1
        return SourcePayload(synthetic_fuelhh_rows, synthetic_windfor_rows)

    cache.load(key, fetch)
    clock.advance(100.0)
    cache.load(key, fetch)
    assert calls["n"] == 2


def test_failed_fetch_not_cached(cache_settings) -> None:
    cache = SourceDataCache(300.0, clock=FakeClock())
    key = source_cache_key(cache_settings)
    calls = {"n": 0}

    def fetch():
        calls["n"] += 1
        raise RuntimeError("Elexon unavailable")

    with pytest.raises(RuntimeError, match="Elexon unavailable"):
        cache.load(key, fetch)
    with pytest.raises(RuntimeError, match="Elexon unavailable"):
        cache.load(key, fetch)
    assert calls["n"] == 2


def test_different_cutoffs_same_cache_recompute_metrics(
    cache_settings,
    synthetic_fuelhh_rows,
    synthetic_windfor_rows,
) -> None:
    """Extend synthetic data so two cutoffs select different forecasts."""
    fuelhh = synthetic_fuelhh_rows
    windfor = [
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
    client = CountingClient(fuelhh, windfor)
    cache = SourceDataCache(300.0, clock=FakeClock())

    early = run_analysis(cache_settings, "09:20", client=client, cache=cache)
    late = run_analysis(cache_settings, "15:30", client=client, cache=cache)

    assert client.fetch_calls == 1
    assert early.matched.iloc[0]["forecast_mw"] == 90.0
    assert late.matched.iloc[0]["forecast_mw"] == 999.0
    assert early.metrics.mae != late.metrics.mae


def test_run_analysis_reuses_cache_across_calls(
    cache_settings,
    synthetic_fuelhh_rows,
    synthetic_windfor_rows,
) -> None:
    client = CountingClient(synthetic_fuelhh_rows, synthetic_windfor_rows)
    cache = SourceDataCache(300.0, clock=FakeClock())

    run_analysis(cache_settings, client=client, cache=cache)
    run_analysis(cache_settings, client=client, cache=cache)
    assert client.fetch_calls == 1


def test_concurrent_miss_single_fetch(
    cache_settings,
    synthetic_fuelhh_rows,
    synthetic_windfor_rows,
) -> None:
    cache = SourceDataCache(300.0, clock=FakeClock())
    key = source_cache_key(cache_settings)
    calls = {"n": 0}
    gate = threading.Event()

    def fetch():
        calls["n"] += 1
        gate.wait(timeout=2.0)
        return SourcePayload(synthetic_fuelhh_rows, synthetic_windfor_rows)

    def worker():
        cache.load(key, fetch)

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for t in threads:
        t.start()
    deadline = time.monotonic() + 2.0
    while calls["n"] < 1 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert calls["n"] == 1
    gate.set()
    for t in threads:
        t.join(timeout=3.0)


def test_invalidate_forces_refetch(cache_settings, synthetic_fuelhh_rows, synthetic_windfor_rows) -> None:
    clock = FakeClock()
    cache = SourceDataCache(3600.0, clock=clock)
    key = source_cache_key(cache_settings)
    calls = {"n": 0}

    def fetch():
        calls["n"] += 1
        return SourcePayload(synthetic_fuelhh_rows, synthetic_windfor_rows)

    cache.load(key, fetch)
    cache.invalidate(key)
    cache.load(key, fetch)
    assert calls["n"] == 2


def test_ttl_zero_disables_cache(cache_settings, synthetic_fuelhh_rows, synthetic_windfor_rows) -> None:
    cache = SourceDataCache(0.0, clock=FakeClock())
    key = source_cache_key(cache_settings)
    calls = {"n": 0}

    def fetch():
        calls["n"] += 1
        return SourcePayload(synthetic_fuelhh_rows, synthetic_windfor_rows)

    cache.load(key, fetch)
    cache.load(key, fetch)
    assert calls["n"] == 2
