"""FastAPI application for wind forecast accuracy analysis."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.clients.elexon import ElexonClient
from app.config import Settings, get_settings
from app.services.analysis import analyse_from_frames
from app.services.source_cache import SourcePayload, get_source_cache, source_cache_key
from app.services.timestamps import to_utc_iso

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="UK Wind Forecast Accuracy API",
        description="January 2026 national WINDFOR vs FUELHH analysis with as-of forecast selection.",
        version="0.1.0",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allowed_origins),
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    return application


app = create_app()


@lru_cache
def cached_settings() -> Settings:
    return get_settings()


def _fetch_source_payload(settings: Settings, client: ElexonClient | None = None) -> SourcePayload:
    elexon = client or ElexonClient(settings.elexon_base_url)
    return SourcePayload(
        fuelhh=elexon.fetch_fuelhh_wind(settings.delivery_start, settings.delivery_end),
        windfor=elexon.fetch_windfor_by_publish_window(
            settings.windfor_publish_from,
            settings.windfor_publish_to,
        ),
    )


def load_cached_source(
    settings: Settings,
    client: ElexonClient | None = None,
    cache=None,
) -> SourcePayload:
    """Load FUELHH/WINDFOR from TTL cache or Elexon."""
    store = cache if cache is not None else get_source_cache(settings)
    key = source_cache_key(settings)
    return store.load(key, lambda: _fetch_source_payload(settings, client))


def run_analysis(
    settings: Settings,
    cutoff: str | None = None,
    *,
    client: ElexonClient | None = None,
    cache=None,
):
    """Analyse with the effective cutoff; source rows may come from the in-memory cache."""
    effective = cutoff or settings.decision_cutoff_local_time
    payload = load_cached_source(settings, client=client, cache=cache)
    return analyse_from_frames(
        payload.fuelhh,
        payload.windfor,
        settings,
        cutoff_clock=effective,
    )


def _series_records(matched) -> list[dict[str, Any]]:
    if matched.empty:
        return []
    rows = []
    for _, row in matched.iterrows():
        rows.append(
            {
                "hour_start": to_utc_iso(row["hour_start"]),
                "settlement_date": row["settlement_date"].isoformat(),
                "forecast_mw": row["forecast_mw"],
                "actual_mw": row["actual_mw"],
                "forecast_error": row["forecast_error"],
                "publish_time": to_utc_iso(row["publish_time"]),
                "cutoff_utc": to_utc_iso(row["cutoff_utc"]),
            },
        )
    return rows


@app.get("/api/health")
def health() -> dict[str, str]:
    """Liveness probe — does not call Elexon."""
    return {"status": "ok"}


@app.get("/api/config")
def config() -> dict[str, Any]:
    s = cached_settings()
    return {
        "delivery_start": s.delivery_start.isoformat(),
        "delivery_end": s.delivery_end.isoformat(),
        "decision_cutoff_local_time": s.decision_cutoff_local_time,
        "decision_cutoff_timezone": s.decision_cutoff_timezone,
        "windfor_publish_from": s.windfor_publish_from,
        "windfor_publish_to": s.windfor_publish_to,
        "elexon_base_url": s.elexon_base_url,
    }


@app.get("/api/metrics")
def metrics(
    cutoff: str | None = Query(None, description="Override cutoff clock HH:MM"),
) -> dict[str, Any]:
    settings = cached_settings()
    try:
        result = run_analysis(settings, cutoff)
    except Exception as exc:
        logger.exception("Analysis failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "metrics": result.metrics.as_dict(),
        "coverage": result.coverage_dict(),
        "cutoff_used": cutoff or settings.decision_cutoff_local_time,
    }


@app.get("/api/coverage")
def coverage() -> dict[str, Any]:
    settings = cached_settings()
    try:
        result = run_analysis(settings)
    except Exception as exc:
        logger.exception("Analysis failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return result.coverage_dict()


@app.get("/api/series")
def series(
    limit: int = Query(500, ge=1, le=2000),
    cutoff: str | None = Query(None, description="Override cutoff clock HH:MM"),
) -> dict[str, Any]:
    settings = cached_settings()
    try:
        result = run_analysis(settings, cutoff)
    except Exception as exc:
        logger.exception("Analysis failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    records = _series_records(result.matched.head(limit))
    return {
        "count": len(records),
        "series": records,
        "cutoff_used": cutoff or settings.decision_cutoff_local_time,
    }
