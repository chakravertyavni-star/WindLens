# Backend



FastAPI service for January 2026 national wind forecast accuracy (WINDFOR vs FUELHH).



## Run locally



From the repository root:



```powershell

cd C:\websites\ELECTRICITY

.\scripts\start-backend.ps1

```



Default bind: **127.0.0.1:8001** (see `dev.env.example`). Open http://127.0.0.1:8001/docs



## Endpoints



| Route | Purpose |

| --- | --- |

| `GET /api/health` | Liveness |

| `GET /api/config` | Active delivery window and cutoff settings |

| `GET /api/coverage` | Matched / unmatched counts |

| `GET /api/metrics` | MAE, RMSE, bias, and coverage |

| `GET /api/series` | Matched hourly forecast vs actual series |



## Elexon source cache



Each analysis needs the same historical **FUELHH** and **WINDFOR** rows. Without caching, every `/api/metrics`, `/api/coverage`, and `/api/series` call downloaded both datasets again.



**Strategy:** `app/services/source_cache.py` stores raw JSON lists in a process-local TTL cache keyed by:



- `ELEXON_BASE_URL`

- delivery start/end dates

- WINDFOR publish window (`WINDFOR_PUBLISH_FROM` / `WINDFOR_PUBLISH_TO`)



**Not cached:** cutoff-specific results. Changing `?cutoff=` still runs forecast selection and metrics on the cached source rows.



**Configuration:** `ELEXON_SOURCE_CACHE_TTL_SECONDS` (default **3600**). Set **0** to disable caching.



**Expiration:** Entries expire after TTL based on a monotonic clock. No service restart required. Tests and operators can call `SourceDataCache.invalidate()` on a dedicated instance; the production singleton refreshes automatically when TTL elapses or when TTL env changes (new singleton).



**Errors:** Failed Elexon fetches are **not** stored. Concurrent waiters see the same exception. The next request retries the download.



**Concurrency:** Per-key **single-flight** loading — simultaneous cache misses share one in-flight HTTP fetch instead of duplicating downloads.



**Limitations:** In-memory only (not shared across workers/processes). Each Uvicorn worker has its own cache. No Redis.



Implementation entry point: `run_analysis()` in `app/main.py` → `load_cached_source()`.

## Production

- **Docker:** `docker build -f backend/Dockerfile -t windlens-api .` (repo root).
- **Bind:** `0.0.0.0:8001` in the Dockerfile; local dev scripts use `127.0.0.1`.
- **Health:** `GET /api/health` (liveness; does not call Elexon).
- **Errors:** analysis routes return **502** with JSON `detail` if Elexon fails.
- **CORS:** `CORS_ALLOWED_ORIGINS` in `.env` (see repo `.env.example`).
- **Guide:** [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md).

## Tests



```bash

python -m pytest -m "not integration"

python -m pytest -m integration

```



Cache behaviour: `tests/test_source_cache.py`.


