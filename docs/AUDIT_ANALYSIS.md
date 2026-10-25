# WindLens analytical correctness audit

**Date:** 25 October 2026  
**Scope:** Backend pipeline from Elexon FUELHH/WINDFOR through metrics and API JSON. Frontend display logic was not re-audited (uses API values as returned).

## Pipeline map

| Stage | Module | Function |
| --- | --- | --- |
| Source TTL cache (optional) | `backend/app/services/source_cache.py` | `SourceDataCache.load`, `get_source_cache` |
| HTTP fetch FUELHH | `backend/app/clients/elexon.py` | `fetch_fuelhh_wind` (via `main.load_cached_source`) |
| HTTP fetch WINDFOR | `backend/app/clients/elexon.py` | `fetch_windfor_by_publish_window` |
| Parse FUELHH | `backend/app/services/matching.py` | `fuelhh_to_dataframe` |
| Parse WINDFOR | `backend/app/services/matching.py` | `windfor_to_dataframe` |
| Delivery window filter | `backend/app/services/matching.py` | `filter_delivery_window` |
| Hourly actuals | `backend/app/services/matching.py` | `build_hourly_actuals` |
| Cutoff instant (UTC) | `backend/app/services/cutoff.py` | `decision_cutoff_utc` |
| As-of forecast pick | `backend/app/services/selection.py` | `select_latest_eligible_forecast` |
| Match loop | `backend/app/services/matching.py` | `run_matching` |
| Metrics | `backend/app/services/metrics.py` | `compute_metrics` |
| Orchestration | `backend/app/services/analysis.py` | `analyse_from_frames`, `analyse_live` |
| API | `backend/app/main.py` | `run_analysis`, `/api/metrics`, `/api/series` |

## Source fields and units (verified vs documented)

| Dataset | Field | Documented meaning | Code usage |
| --- | --- | --- | --- |
| FUELHH | `startTime` | Start of 30-minute delivery period (UTC in API) | Parsed to UTC; drives delivery filter and hourly grouping |
| FUELHH | `generation` | Average MW over the half-hour (Elexon FUELHH docs) | `actual_mw` |
| FUELHH | `settlementDate` | UK settlement date | Cutoff calendar day-before; grouped with hourly actuals |
| WINDFOR | `startTime` | Delivery period being forecast (hourly `:00` in probe) | Exact match key to `hour_start` |
| WINDFOR | `publishTime` | Forecast version timestamp | Eligibility `<= cutoff_utc`; latest wins |
| WINDFOR | `generation` | Forecast MW (Elexon wind-generation pages) | `forecast_mw` |

**Uncertainty (unchanged):** Elexon stream schemas do not spell out whether WINDFOR `generation` is strictly the mean MW over the hour starting at `startTime`. The implementation assumes the hour **starting** at `startTime`, consistent with hourly `:00` timestamps and FUELHH hourly aggregation. This is an assumption, not a proven schema fact (`docs/investigation/API_FINDINGS.md`).

## Timestamp and alignment

- **January scope:** FUELHH is fetched with `settlementDateFrom/To` = 2026-01-01 … 2026-01-31. An additional filter keeps rows with `start_time` in `[2026-01-01 00:00 UTC, 2026-02-01 00:00 UTC)`.
- **Live check (25 Oct 2026):** 1,488 raw FUELHH rows; **1,488** remain after UTC filter; **0** hours where `settlement_date` ≠ UTC date of `hour_start` (January is GMT; UK settlement aligns with UTC calendar date for this month).
- **Cutoff:** `decision_cutoff_utc(settlement_date)` = previous calendar day at configured clock in `Europe/London`, converted to UTC. January 2026 uses GMT (no BST).
- **Publish vs delivery:** Selection never uses `publishTime` as a delivery key; only `start_time` matches delivery `hour_start`.
- **Duplicates:** Live January extract has **0** duplicate FUELHH `startTime` values and **0** duplicate matched `hour_start` keys.

**Limitation:** Using a UTC calendar month on `start_time` may diverge from UK settlement boundaries in months where settlement dates do not align with UTC dates (not observed for January 2026).

## Hourly actual aggregation

- Groups FUELHH rows by `(hour_start = floor UTC hour, settlement_date)`.
- Requires exactly **two** half-hours (`:00` and `:30`); otherwise the hour is **excluded** (not zero-filled).
- Uses the **mean** of the two half-hour `generation` values → time-weighted average MW over the clock hour when both periods are 30 minutes.

## Forecast selection

For each complete hourly actual: compute cutoff from **`settlement_date`**; select WINDFOR rows with `start_time == hour_start` and `publish_time <= cutoff_utc`; take **latest** `publish_time`.

**Live reconciliation (25 Oct 2026, cutoff 09:20 Europe/London):** 744 matched hours; **0** rows with `publish_time > cutoff_utc`; **0** mismatches when re-running `select_latest_eligible_forecast` on the filtered WINDFOR frame.

## Metrics

- `forecast_error = forecast_mw - actual_mw`
- `MAE = mean(|error|)`, `RMSE = sqrt(mean(error²))`, `Bias = mean(error)`
- Computed only on matched rows with non-null forecast and actual (`compute_metrics`).

Independent recomputation from the 744 matched live rows equals API metrics to floating-point equality (see `scripts/audit_analysis.py`).

## Dashboard numbers (default cutoff 09:20)

| Metric | Value (live Elexon, 25 Oct 2026) |
| --- | ---: |
| n | 744 |
| MAE | ~2,142.12 MW |
| RMSE | ~2,611.70 MW |
| Bias | ~+1,851.90 MW |

Rounded display (e.g. 2,142 MW) is a presentation choice; the pipeline uses full precision.

## Classification summary

| Topic | Status |
| --- | --- |
| Formulas and sample size consistency | **Confirmed correct** |
| Cutoff timezone (Europe/London → UTC) | **Confirmed correct** for tested dates |
| Latest eligible forecast selection | **Confirmed correct** (live + unit tests) |
| No post-cutoff forecasts in sample | **Confirmed correct** (live) |
| Half-hour → hour aggregation without zero-fill | **Confirmed correct** |
| FUELHH/WINDFOR units as MW | **Confirmed** per Elexon docs; field-level schema wording incomplete |
| WINDFOR hour definition | **Unresolved uncertainty** (assumption documented) |
| UTC vs UK settlement month filter | **Assumption acceptable for Jan 2026**; not proven for all months |
| `/api/series` `limit` truncates head of sorted matched frame | **Known limitation** (not a metric bug; use `limit=2000` for full month) |

**Defects found:** None requiring code changes in this audit.

## Tests and scripts

- `tests/test_audit_reconciliation.py` — invariants + live reconciliation (`@pytest.mark.integration`)
- `scripts/audit_analysis.py` — standalone live JSON reconciliation report

```powershell
$env:PYTHONPATH='backend'
python -m pytest tests -m "not integration" -q
python -m pytest tests/test_audit_reconciliation.py -m integration -q
python scripts/audit_analysis.py
```

## Source cache and correctness

Caching stores **raw FUELHH/WINDFOR lists only** (`ELEXON_SOURCE_CACHE_TTL_SECONDS`, default 3600). Cutoff selection and metrics run on every API call.

Live check (25 Oct 2026): first `run_analysis` → 2 Elexon HTTP calls (~3.5 s); second call within TTL → 0 additional HTTP calls (~0.41 s); metrics identical (MAE 2142.12 MW, n=744).
