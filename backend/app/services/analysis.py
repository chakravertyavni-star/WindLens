"""Orchestrate load, filter, match, and metrics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from app.clients.elexon import ElexonClient
from app.config import Settings
from app.services.matching import (
    filter_delivery_window,
    fuelhh_to_dataframe,
    run_matching,
    windfor_to_dataframe,
)
from app.services.metrics import MetricResult, compute_metrics


@dataclass
class AnalysisResult:
    matched: pd.DataFrame
    unmatched_hours: pd.DataFrame
    metrics: MetricResult
    actual_half_hours: int
    hourly_actuals_complete: int
    forecast_rows_january: int

    def coverage_dict(self) -> dict:
        return {
            "actual_half_hours_in_window": self.actual_half_hours,
            "hourly_actuals_with_both_half_hours": self.hourly_actuals_complete,
            "forecast_rows_january_delivery": self.forecast_rows_january,
            "matched_hourly_pairs": len(self.matched),
            "unmatched_hours": len(self.unmatched_hours),
            "metrics_sample_size": self.metrics.n,
        }


def analyse_from_frames(
    fuelhh_rows: list[dict],
    windfor_rows: list[dict],
    settings: Settings,
    *,
    delivery_start: date | None = None,
    delivery_end: date | None = None,
    cutoff_clock: str | None = None,
    cutoff_tz: str | None = None,
) -> AnalysisResult:
    d0 = delivery_start or settings.delivery_start
    d1 = delivery_end or settings.delivery_end
    clock = cutoff_clock or settings.decision_cutoff_local_time
    tz = cutoff_tz or settings.decision_cutoff_timezone

    actuals = fuelhh_to_dataframe(fuelhh_rows)
    forecasts = windfor_to_dataframe(windfor_rows)
    actuals = filter_delivery_window(actuals, d0, d1)
    forecasts = filter_delivery_window(forecasts, d0, d1)

    from app.services.matching import build_hourly_actuals

    hourly = build_hourly_actuals(actuals)
    matched, unmatched = run_matching(
        actuals,
        forecasts,
        cutoff_clock=clock,
        cutoff_tz=tz,
    )
    metrics = compute_metrics(matched)
    return AnalysisResult(
        matched=matched,
        unmatched_hours=unmatched,
        metrics=metrics,
        actual_half_hours=len(actuals),
        hourly_actuals_complete=len(hourly),
        forecast_rows_january=len(forecasts),
    )


def analyse_live(settings: Settings, client: ElexonClient | None = None) -> AnalysisResult:
    client = client or ElexonClient(settings.elexon_base_url)
    fuelhh = client.fetch_fuelhh_wind(settings.delivery_start, settings.delivery_end)
    windfor = client.fetch_windfor_by_publish_window(
        settings.windfor_publish_from,
        settings.windfor_publish_to,
    )
    return analyse_from_frames(fuelhh, windfor, settings)
