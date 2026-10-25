"""Build hourly actuals from half-hourly FUELHH and match to selected forecasts."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

import pandas as pd

from app.services.cutoff import decision_cutoff_utc
from app.services.selection import select_latest_eligible_forecast


def fuelhh_to_dataframe(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(
            columns=[
                "start_time",
                "publish_time",
                "settlement_date",
                "settlement_period",
                "actual_mw",
            ],
        )
    frame = pd.DataFrame(rows)
    frame["start_time"] = pd.to_datetime(frame["startTime"], utc=True)
    frame["publish_time"] = pd.to_datetime(frame["publishTime"], utc=True)
    frame["settlement_date"] = pd.to_datetime(frame["settlementDate"]).dt.date
    frame["settlement_period"] = frame["settlementPeriod"].astype(int)
    frame["actual_mw"] = frame["generation"].astype(float)
    return frame[
        [
            "start_time",
            "publish_time",
            "settlement_date",
            "settlement_period",
            "actual_mw",
        ]
    ]


def windfor_to_dataframe(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["start_time", "publish_time", "forecast_mw"])
    frame = pd.DataFrame(rows)
    frame["start_time"] = pd.to_datetime(frame["startTime"], utc=True)
    frame["publish_time"] = pd.to_datetime(frame["publishTime"], utc=True)
    frame["forecast_mw"] = frame["generation"].astype(float)
    return frame[["start_time", "publish_time", "forecast_mw"]]


def filter_delivery_window(
    frame: pd.DataFrame,
    delivery_start: date,
    delivery_end: date,
    time_column: str = "start_time",
) -> pd.DataFrame:
    start = pd.Timestamp(datetime.combine(delivery_start, time.min, tzinfo=timezone.utc))
    end_exclusive = pd.Timestamp(
        datetime.combine(delivery_end + timedelta(days=1), time.min, tzinfo=timezone.utc),
    )
    return frame[(frame[time_column] >= start) & (frame[time_column] < end_exclusive)].copy()


def build_hourly_actuals(actuals: pd.DataFrame) -> pd.DataFrame:
    """
    Average the :00 and :30 half-hours that share the same UTC hour start.

    If either half is missing, the hour is excluded (not zero-filled).
    """
    if actuals.empty:
        return pd.DataFrame(
            columns=["hour_start", "settlement_date", "actual_mw"],
        )
    working = actuals.copy()
    working["hour_start"] = working["start_time"].dt.floor("h")
    half = working["start_time"].dt.minute
    if not set(half.unique()).issubset({0, 30}):
        raise ValueError("FUELHH start_time minutes must be 0 or 30 for hourly aggregation")

    grouped = working.groupby(["hour_start", "settlement_date"], as_index=False)
    counts = grouped["actual_mw"].count().rename(columns={"actual_mw": "half_hour_count"})
    means = grouped["actual_mw"].mean()
    hourly = means.merge(counts, on=["hour_start", "settlement_date"])
    hourly = hourly[hourly["half_hour_count"] == 2].drop(columns=["half_hour_count"])
    hourly = hourly.rename(columns={"actual_mw": "actual_mw"})
    return hourly


def run_matching(
    actuals: pd.DataFrame,
    forecasts: pd.DataFrame,
    *,
    cutoff_clock: str,
    cutoff_tz: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns (matched_pairs, coverage_summary_rows).

    matched_pairs columns include hour_start, settlement_date, actual_mw,
    forecast_mw, publish_time, cutoff_utc, forecast_error.
    """
    hourly = build_hourly_actuals(actuals)
    matched_rows: list[dict] = []
    unmatched: list[dict] = []

    for _, row in hourly.iterrows():
        hour_start: pd.Timestamp = row["hour_start"]
        settlement_date: date = row["settlement_date"]
        cutoff = decision_cutoff_utc(
            settlement_date,
            cutoff_clock=cutoff_clock,
            tz_name=cutoff_tz,
        )
        selected = select_latest_eligible_forecast(forecasts, hour_start, cutoff)
        if selected is None:
            unmatched.append(
                {
                    "hour_start": hour_start,
                    "settlement_date": settlement_date,
                    "reason": "no_eligible_forecast",
                },
            )
            continue
        forecast_mw = float(selected["forecast_mw"])
        actual_mw = float(row["actual_mw"])
        matched_rows.append(
            {
                "hour_start": hour_start,
                "settlement_date": settlement_date,
                "actual_mw": actual_mw,
                "forecast_mw": forecast_mw,
                "publish_time": selected["publish_time"],
                "cutoff_utc": cutoff,
                "forecast_error": forecast_mw - actual_mw,
            },
        )

    matched = pd.DataFrame(matched_rows)
    coverage = pd.DataFrame(unmatched)
    return matched, coverage
