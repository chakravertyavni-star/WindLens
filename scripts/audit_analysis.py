"""Independent reconciliation of WindLens metrics against matched series."""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.clients.elexon import ElexonClient  # noqa: E402
from app.config import Settings  # noqa: E402
from app.main import load_cached_source, run_analysis  # noqa: E402
from app.services.matching import filter_delivery_window, fuelhh_to_dataframe, windfor_to_dataframe  # noqa: E402
from app.services.metrics import compute_metrics  # noqa: E402
from app.services.selection import select_latest_eligible_forecast  # noqa: E402
from app.services.source_cache import get_source_cache, reset_source_cache_for_tests  # noqa: E402


class CountingElexonClient(ElexonClient):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.http_round_trips = 0

    def fetch_fuelhh_wind(self, settlement_date_from, settlement_date_to):
        self.http_round_trips += 1
        return super().fetch_fuelhh_wind(settlement_date_from, settlement_date_to)

    def fetch_windfor_by_publish_window(self, publish_datetime_from, publish_datetime_to):
        self.http_round_trips += 1
        return super().fetch_windfor_by_publish_window(
            publish_datetime_from,
            publish_datetime_to,
        )


def main() -> int:
    settings = Settings.from_env()
    reset_source_cache_for_tests()
    cache = get_source_cache(settings)
    counting = CountingElexonClient(settings.elexon_base_url)

    t0 = time.perf_counter()
    result = run_analysis(settings, client=counting, cache=cache)
    first_elapsed = time.perf_counter() - t0
    trips_after_first = counting.http_round_trips

    t1 = time.perf_counter()
    result_cached = run_analysis(settings, client=counting, cache=cache)
    second_elapsed = time.perf_counter() - t1
    trips_after_second = counting.http_round_trips

    matched = result.matched
    payload = load_cached_source(settings, client=counting, cache=cache)
    fuelhh_rows = payload.fuelhh
    windfor_rows = payload.windfor

    raw_count = len(fuelhh_rows)
    actuals = fuelhh_to_dataframe(fuelhh_rows)
    filtered = filter_delivery_window(actuals, settings.delivery_start, settings.delivery_end)
    forecasts = filter_delivery_window(
        windfor_to_dataframe(windfor_rows),
        settings.delivery_start,
        settings.delivery_end,
    )

    errors = matched["forecast_mw"] - matched["actual_mw"]
    err_col = matched["forecast_error"]
    max_err_diff = float((errors - err_col).abs().max()) if len(matched) else 0.0

    mae_ind = float(errors.abs().mean()) if len(errors) else None
    rmse_ind = float(math.sqrt((errors**2).mean())) if len(errors) else None
    bias_ind = float(errors.mean()) if len(errors) else None

    dup_hours = matched["hour_start"].duplicated().sum()
    dup_starts_actual = actuals["start_time"].duplicated().sum()

    cutoff_violations = 0
    selection_mismatch = 0
    for _, row in matched.iterrows():
        if row["publish_time"] > row["cutoff_utc"]:
            cutoff_violations += 1
        sel = select_latest_eligible_forecast(
            forecasts,
            row["hour_start"],
            row["cutoff_utc"],
        )
        if sel is None or float(sel["forecast_mw"]) != float(row["forecast_mw"]):
            selection_mismatch += 1
        elif sel["publish_time"] != row["publish_time"]:
            selection_mismatch += 1

    metrics2 = compute_metrics(matched)

    report = {
        "fuelhh_raw_rows": raw_count,
        "fuelhh_after_utc_window_filter": len(filtered),
        "actual_half_hours_in_result": result.actual_half_hours,
        "hourly_complete": result.hourly_actuals_complete,
        "matched_pairs": len(matched),
        "unmatched_hours": len(result.unmatched_hours),
        "metrics_api": result.metrics.as_dict(),
        "metrics_cached_second_run": result_cached.metrics.as_dict(),
        "metrics_recomputed_from_matched": metrics2.as_dict(),
        "independent_mae_rmse_bias": {
            "mae": mae_ind,
            "rmse": rmse_ind,
            "bias": bias_ind,
        },
        "cache_elexon_http_round_trips_first_run": trips_after_first,
        "cache_elexon_http_round_trips_second_run": trips_after_second,
        "cache_first_run_seconds": round(first_elapsed, 3),
        "cache_second_run_seconds": round(second_elapsed, 3),
        "max_forecast_error_column_diff": max_err_diff,
        "duplicate_hour_start_in_matched": int(dup_hours),
        "duplicate_fuelhh_start_time": int(dup_starts_actual),
        "publish_after_cutoff_violations": cutoff_violations,
        "selection_recheck_mismatches": selection_mismatch,
        "metrics_n_equals_matched_len": result.metrics.n == len(matched),
    }

    print(json.dumps(report, indent=2))
    ok = (
        report["metrics_n_equals_matched_len"]
        and max_err_diff < 1e-9
        and cutoff_violations == 0
        and selection_mismatch == 0
        and report["metrics_api"] == metrics2.as_dict()
        and report["metrics_api"] == report["metrics_cached_second_run"]
        and mae_ind == result.metrics.mae
        and trips_after_first == 2
        and trips_after_second == 2
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
