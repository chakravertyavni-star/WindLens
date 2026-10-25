"""Reproducible Elexon Insights API investigation for January 2026 wind data.

This script probes only the documented FUELHH and WINDFOR stream endpoints.
It writes a JSON summary of verified findings. It does not invent records
and it avoids downloading the full multi-week WINDFOR archive.
"""

from __future__ import annotations

import json
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
TIMEOUT_SECONDS = 60
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "docs" / "investigation" / "elexon_api_probe.json"


def fetch_json(path: str, params: dict[str, str] | None = None) -> tuple[int, object | None, str | None]:
    query = f"?{urllib.parse.urlencode(params)}" if params else ""
    url = f"{BASE_URL}{path}{query}"
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "electricity-assignment-investigation/0.1"},
    )
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS, context=context) as response:
            payload = response.read()
            return response.status, json.loads(payload.decode("utf-8")), None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, None, body[:1000]
    except Exception as exc:  # noqa: BLE001 - investigation must record any failure
        return 0, None, str(exc)


def summarise_fuelhh(rows: list[dict]) -> dict:
    dates = sorted({row.get("settlementDate") for row in rows if row.get("settlementDate")})
    periods_by_date: dict[str, set[int]] = {}
    generations = []
    start_minutes = Counter()
    datasets = Counter()
    fuel_types = Counter()
    missing_generation = 0

    for row in rows:
        date = row.get("settlementDate")
        period = row.get("settlementPeriod")
        if date and period is not None:
            periods_by_date.setdefault(date, set()).add(period)
        start_time = row.get("startTime")
        if isinstance(start_time, str) and len(start_time) >= 16:
            start_minutes[start_time[14:16]] += 1
        datasets[row.get("dataset")] += 1
        fuel_types[row.get("fuelType")] += 1
        generation = row.get("generation")
        if generation is None:
            missing_generation += 1
        else:
            generations.append(generation)

    missing_periods = {}
    for date, periods in periods_by_date.items():
        expected = set(range(1, 49))
        absent = sorted(expected - periods)
        if absent:
            missing_periods[date] = absent

    return {
        "record_count": len(rows),
        "settlement_date_count": len(dates),
        "first_settlement_date": dates[0] if dates else None,
        "last_settlement_date": dates[-1] if dates else None,
        "datasets": dict(datasets),
        "fuel_types": dict(fuel_types),
        "start_time_minute_counts": dict(start_minutes),
        "missing_generation_count": missing_generation,
        "generation_min": min(generations) if generations else None,
        "generation_max": max(generations) if generations else None,
        "dates_with_missing_settlement_periods_1_to_48": missing_periods,
        "sample_first": rows[0] if rows else None,
        "sample_last": rows[-1] if rows else None,
    }


def summarise_windfor(rows: list[dict]) -> dict:
    publish_times = sorted({row.get("publishTime") for row in rows if row.get("publishTime")})
    start_times = sorted(row.get("startTime") for row in rows if row.get("startTime"))
    start_minutes = Counter()
    datasets = Counter()
    missing_generation = 0
    horizon_hours = []

    for row in rows:
        datasets[row.get("dataset")] += 1
        start_time = row.get("startTime")
        if isinstance(start_time, str) and len(start_time) >= 16:
            start_minutes[start_time[14:16]] += 1
        if row.get("generation") is None:
            missing_generation += 1
        try:
            published = datetime.fromisoformat(row["publishTime"].replace("Z", "+00:00"))
            start = datetime.fromisoformat(row["startTime"].replace("Z", "+00:00"))
            horizon_hours.append((start - published).total_seconds() / 3600)
        except Exception:
            continue

    jan_2026_starts = [item for item in start_times if isinstance(item, str) and item.startswith("2026-01")]

    return {
        "record_count": len(rows),
        "datasets": dict(datasets),
        "unique_publish_time_count": len(publish_times),
        "publish_times": publish_times,
        "start_time_min": start_times[0] if start_times else None,
        "start_time_max": start_times[-1] if start_times else None,
        "start_time_minute_counts": dict(start_minutes),
        "january_2026_start_time_count": len(jan_2026_starts),
        "missing_generation_count": missing_generation,
        "horizon_hours_min": min(horizon_hours) if horizon_hours else None,
        "horizon_hours_max": max(horizon_hours) if horizon_hours else None,
        "fields_observed": sorted({key for row in rows for key in row.keys()}),
        "sample_first": rows[0] if rows else None,
        "sample_last": rows[-1] if rows else None,
    }


def main() -> int:
    findings: dict = {
        "investigated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "probes": {},
    }

    fuelhh_status, fuelhh_rows, fuelhh_error = fetch_json(
        "/datasets/FUELHH/stream",
        {
            "settlementDateFrom": "2026-01-01",
            "settlementDateTo": "2026-01-31",
            "fuelType": "WIND",
        },
    )
    findings["probes"]["fuelhh_january_2026_wind"] = {
        "status": fuelhh_status,
        "error": fuelhh_error,
        "summary": summarise_fuelhh(fuelhh_rows) if isinstance(fuelhh_rows, list) else None,
    }

    windfor_status, windfor_rows, windfor_error = fetch_json(
        "/datasets/WINDFOR/stream",
        {
            "publishDateTimeFrom": "2025-12-31T00:00:00Z",
            "publishDateTimeTo": "2025-12-31T23:59:59Z",
        },
    )
    findings["probes"]["windfor_publish_day_2025_12_31"] = {
        "status": windfor_status,
        "error": windfor_error,
        "summary": summarise_windfor(windfor_rows) if isinstance(windfor_rows, list) else None,
    }

    late_status, late_rows, late_error = fetch_json(
        "/datasets/WINDFOR/stream",
        {
            "publishDateTimeFrom": "2026-01-30T00:00:00Z",
            "publishDateTimeTo": "2026-01-30T06:00:00Z",
        },
    )
    findings["probes"]["windfor_publish_window_2026_01_30_early"] = {
        "status": late_status,
        "error": late_error,
        "summary": summarise_windfor(late_rows) if isinstance(late_rows, list) else None,
    }

    latest_status, latest_rows, latest_error = fetch_json("/datasets/WINDFOR/stream")
    findings["probes"]["windfor_latest_unfiltered"] = {
        "status": latest_status,
        "error": latest_error,
        "summary": summarise_windfor(latest_rows) if isinstance(latest_rows, list) else None,
    }

    invalid_status, _, invalid_error = fetch_json(
        "/datasets/FUELHH/stream",
        {
            "settlementDateFrom": "2026-01-01",
            "settlementDateTo": "2026-01-01",
            "publishDateTimeFrom": "2026-01-01T00:00:00Z",
            "fuelType": "WIND",
        },
    )
    findings["probes"]["fuelhh_invalid_combined_filters"] = {
        "status": invalid_status,
        "error": invalid_error,
        "note": "Docs say settlement-date filters cannot be combined with publish-date filters.",
    }

    undocumented_status, undocumented_rows, undocumented_error = fetch_json(
        "/datasets/WINDFOR/stream",
        {
            "publishDateTimeFrom": "2025-12-31T00:00:00Z",
            "publishDateTimeTo": "2025-12-31T06:00:00Z",
            "startTime": "2026-01-01T00:00:00Z",
        },
    )
    findings["probes"]["windfor_undocumented_start_time_filter"] = {
        "status": undocumented_status,
        "error": undocumented_error,
        "record_count": len(undocumented_rows) if isinstance(undocumented_rows, list) else None,
        "note": "startTime is not a documented WINDFOR/stream query parameter. Any effect is unverified and must not be relied on.",
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(findings, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    print(json.dumps({key: value.get("status") for key, value in findings["probes"].items()}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
