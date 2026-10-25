# WindLens

**UK wind-generation forecast accuracy analytics for energy procurement decision support.**

WindLens compares national Elexon wind **forecasts** (`WINDFOR`) with **actual** half-hourly wind generation (`FUELHH`, fuel type WIND) for **January 2026**. Forecast errors (MAE, RMSE, bias) help procurement and operations teams understand historical forecasting uncertainty and the risk of relying on day-ahead wind outlooks when planning wholesale purchases.

This is a **decision-support prototype** based on **historical** January 2026 data. It does **not** execute electricity trades, submit bids, or publish operational live forecasts for the current market day.

---

## Table of contents

- [Live application and source code](#live-application-and-source-code)
- [Problem statement and objectives](#problem-statement-and-objectives)
- [Data sources and processing](#data-sources-and-processing)
- [Metrics and methodology](#metrics-and-methodology)
- [January 2026 results](#january-2026-results)
- [Features](#features)
- [Technology stack](#technology-stack)
- [Repository structure](#repository-structure)
- [Run locally](#run-locally)
- [API reference](#api-reference)
- [Testing and verification](#testing-and-verification)
- [Deployment](#deployment)
- [Limitations and future improvements](#limitations-and-future-improvements)
- [AI tools and development assistance](#ai-tools-and-development-assistance)
- [Further documentation](#further-documentation)

---

## Live application and source code

| Resource | URL |
| --- | --- |
| **Live application (Render)** | [https://windlens-dt0z.onrender.com/](https://windlens-dt0z.onrender.com/) |
| **Public repository** | [https://github.com/chakravertyavni-star/WindLens](https://github.com/chakravertyavni-star/WindLens) |
| **API health** | [https://windlens-dt0z.onrender.com/api/health](https://windlens-dt0z.onrender.com/api/health) |
| **API metrics (default cutoff)** | [https://windlens-dt0z.onrender.com/api/metrics](https://windlens-dt0z.onrender.com/api/metrics) |

The public deployment is hosted on **[Render](https://render.com)** as a single Docker web service (nginx + FastAPI). It is **not** deployed on Vercel or Heroku.

---

## Problem statement and objectives

UK suppliers often procure day-ahead wholesale energy before customers consume it. National wind output is large and weather-driven, so **forecast error** directly affects procurement cost and balancing risk.

WindLens addresses a specific analytical question for **national UK wind** in **January 2026**:

1. Which Elexon wind forecast would have been **available** at a defined decision time before each settlement period?
2. How did that forecast compare to **realised** wind generation?
3. How large and how biased were the errors in aggregate?

The tool quantifies those errors so teams can discuss forecast reliability—it does not automate purchasing or replace official market gate-closure rules.

---

## Data sources and processing

### Elexon API (implemented in `backend/app/clients/elexon.py`)

Base URL (configurable via `ELEXON_BASE_URL`, default):

`https://data.elexon.co.uk/bmrs/api/v1`

| Dataset | HTTP path | Query parameters used in code |
| --- | --- | --- |
| **FUELHH** (actuals) | `/datasets/FUELHH/stream` | `settlementDateFrom`, `settlementDateTo`, `fuelType=WIND` |
| **WINDFOR** (forecasts) | `/datasets/WINDFOR/stream` | `publishDateTimeFrom`, `publishDateTimeTo` |

No API key is required for these public Insights stream endpoints.

### FUELHH → wind actuals

- Rows are filtered to **`fuelType=WIND`** at fetch time.
- JSON fields used: `startTime`, `publishTime`, `settlementDate`, `settlementPeriod`, `generation` (MW).
- Records are restricted to the configured delivery window (`DELIVERY_START_DATE`–`DELIVERY_END_DATE`, default January 2026).

### WINDFOR → forecasts

- Fetched by **publication window** (`WINDFOR_PUBLISH_FROM` / `WINDFOR_PUBLISH_TO`), then filtered locally to the delivery window on `startTime`.
- JSON fields used: `startTime`, `publishTime`, `generation` (MW, treated as forecast MW for the period starting at `startTime`).

### Hourly actual aggregation

Half-hourly FUELHH points are grouped by UTC **hour start** (`start_time` floored to the hour). For each hour, the **mean** of the `:00` and `:30` half-hours is taken. **If either half-hour is missing, that hour is excluded**—it is not zero-filled (`backend/app/services/matching.py`).

### Forecast selection (publication cutoff)

For each complete hourly actual, the app computes a **decision cutoff** in UTC:

- Default clock: **`09:20`** in **`Europe/London`** (`DECISION_CUTOFF_LOCAL_TIME`, `DECISION_CUTOFF_TIMEZONE`).
- Applied on the **calendar day before** the UK **settlement date** for that hour (`backend/app/services/cutoff.py`).

Among WINDFOR rows whose `startTime` equals the delivery hour:

- Keep rows with `publishTime` **≤** cutoff (UTC).
- Select the row with the **latest** `publishTime`.

Forecasts published **after** the cutoff are excluded. This cutoff is an **analytical assumption** for “as-of” reconstruction—not an official Elexon or NESO gate-closure rule.

### Caching

Raw FUELHH and WINDFOR payloads are cached in memory for `ELEXON_SOURCE_CACHE_TTL_SECONDS` (default 3600). Analysis results are recomputed per request; changing the cutoff does not require refetching Elexon if the cache is warm.

---

## Metrics and methodology

**Forecast error** (per matched hour):

```text
forecast_error = forecast_mw − actual_mw
```

| Metric | Definition |
| --- | --- |
| **MAE** | Mean of \|forecast_error\| (MW) |
| **RMSE** | Square root of mean(forecast_error²) (MW) |
| **Bias** | Mean of forecast_error (MW) |

Metrics are computed only on **matched** hourly pairs with both values present (`backend/app/services/metrics.py`). If `n = 0`, MAE/RMSE/bias are `null`.

**Coverage** (returned with `/api/metrics` and `/api/coverage`):

- `actual_half_hours_in_window` — FUELHH half-hours in the delivery filter
- `hourly_actuals_with_both_half_hours` — hours with both :00 and :30
- `forecast_rows_january_delivery` — WINDFOR rows in the delivery window
- `matched_hourly_pairs` — hours with a selected forecast
- `unmatched_hours` — hours with no eligible forecast
- `metrics_sample_size` — same as metric `n`

Changing the cutoff changes which forecast is selected and therefore changes metrics and coverage.

---

## January 2026 results

At the **default cutoff 09:20 Europe/London**, with delivery **2026-01-01** to **2026-01-31** (verified by integration tests, audit script, and local Docker checks):

| Measure | Value |
| --- | ---: |
| Half-hour actual records (in window) | 1,488 |
| Complete hourly actual values | 744 |
| Forecast rows in January delivery window | 18,080 |
| Matched hourly forecast/actual pairs | 744 |
| Unmatched hours | 0 |
| **MAE** | ≈ **2,142.12 MW** |
| **RMSE** | ≈ **2,611.70 MW** |
| **Bias** | ≈ **+1,851.90 MW** |

**Positive bias** means forecasts were **higher** than actual generation on average under this project’s sign convention (forecast minus actual).

These figures describe **historical January 2026** performance under the stated cutoff and matching rules. They are **not** current live operating conditions. The live Render site **recomputes** analysis from Elexon when you call the API; headline numbers should match the defaults above when Elexon data and configuration are unchanged.

---

## Features

Implemented in the React dashboard (`frontend/src/`):

| Area | Description |
| --- | --- |
| **Overview** | Insight banner, four KPI cards (MAE, RMSE, bias, sample size), forecast vs actual chart (Recharts), coverage summary |
| **Analysis settings** | Editable decision cutoff (HH:MM); **Recalculate** refetches `/api/metrics` and `/api/series` with `?cutoff=` |
| **Date range filter** | Client-side filter on settlement dates for the **overview chart only** (headline metrics still use all matched hours for the cutoff) |
| **Forecast analysis** | Sortable/paginated table of hourly matched pairs |
| **Methodology** | Explains cutoff, metrics, and disclaimers |
| **Navigation** | Sidebar: Overview, Forecast Analysis, Methodology |
| **Header** | “Historical analysis” emphasis (non-trading disclaimer) |

Backend routes used by the UI: `/api/config`, `/api/metrics`, `/api/series`. OpenAPI docs are at `/docs` when the API is running.

---

## Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | React 19, Vite 6, Recharts |
| Backend | Python 3.12+, FastAPI, Uvicorn |
| Data | pandas, httpx (Elexon HTTP) |
| Config | python-dotenv (`.env` at repo root) |
| Tests | pytest (backend), Vitest (frontend) |
| Local / production containers | Docker, Docker Compose, nginx |

---

## Repository structure

```text
ELECTRICITY/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── clients/elexon.py    # Elexon stream client
│   │   ├── config.py            # Environment settings
│   │   ├── main.py              # HTTP routes
│   │   └── services/            # Matching, metrics, cache, cutoff
│   └── Dockerfile
├── frontend/                # React SPA
│   ├── src/                     # Pages, charts, API client
│   ├── Dockerfile               # nginx + static build (Compose)
│   └── package.json
├── deploy/                  # Public single-container image (Render)
│   ├── Dockerfile.public
│   ├── start-public.sh
│   └── nginx.public.conf.template
├── tests/                   # pytest suite
├── scripts/                 # Dev starters, audit, report generation
├── docs/                    # Report, deployment guide, audit, diagrams
├── docker-compose.yml       # Local nginx (8080) + backend (8001)
├── render.yaml              # Optional Render Blueprint
├── requirements.txt
├── .env.example
└── README.md
```

---

## Run locally

### Prerequisites

- **Docker Desktop** (recommended full stack), or
- **Python 3.12+** and **Node.js 20+** for split dev servers
- Network access to `data.elexon.co.uk`

### Full application with Docker Compose

From the repository root:

```powershell
docker compose up --build
```

| Service | URL |
| --- | --- |
| **Application** | [http://localhost:8080](http://localhost:8080) (nginx → SPA + `/api` proxy) |
| **Health (via proxy)** | [http://localhost:8080/api/health](http://localhost:8080/api/health) |
| **Metrics (via proxy)** | [http://localhost:8080/api/metrics](http://localhost:8080/api/metrics) |

### Split development (optional)

**One-time setup:**

```powershell
python -m pip install -r requirements.txt
Copy-Item dev.env.example dev.env
Copy-Item .env.example .env
cd frontend
npm install
```

**Terminal 1 — backend** (default port **8001**):

```powershell
.\scripts\start-backend.ps1
```

**Terminal 2 — frontend** (Vite, typically [http://127.0.0.1:5173](http://127.0.0.1:5173)):

```powershell
.\scripts\start-frontend.ps1
```

Vite proxies `/api` to `VITE_DEV_API_PROXY` in `frontend/.env.development` (default `http://127.0.0.1:8001`).

### Backend tests

```powershell
$env:PYTHONPATH='backend'
python -m pytest tests -m "not integration" -q
python -m pytest tests -m integration -q
```

### Frontend tests and production build

```powershell
cd frontend
npm test
npm run build
```

Output: `frontend/dist/` (not committed; Docker/Render builds embed this).

### Analysis audit (live Elexon)

```powershell
$env:PYTHONPATH='backend'
python scripts/audit_analysis.py
```

Prints JSON reconciliation checks (metrics, duplicates, cutoff violations).

---

## API reference

All analysis routes call Elexon on cache miss and return **502** with a JSON `detail` if fetch or analysis fails. **`/api/health` does not call Elexon.**

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Liveness: `{"status":"ok"}` |
| `GET` | `/api/config` | Delivery window, cutoff, WINDFOR publish window, Elexon base URL |
| `GET` | `/api/metrics` | MAE, RMSE, bias, coverage; optional `cutoff` (HH:MM) |
| `GET` | `/api/coverage` | Coverage counts only (default cutoff) |
| `GET` | `/api/series` | Matched hourly rows; query `limit` (1–2000, default 500), optional `cutoff` |

**Examples:**

```http
GET /api/health
GET /api/metrics
GET /api/metrics?cutoff=15:30
GET /api/series?limit=2000&cutoff=09:20
```

Series item fields include: `hour_start`, `settlement_date`, `forecast_mw`, `actual_mw`, `forecast_error`, `publish_time`, `cutoff_utc` (ISO UTC strings).

Interactive schema: run the backend and open `/docs`.

---

## Testing and verification

### Re-run on 25 October 2026 (this README update)

| Check | Result |
| --- | --- |
| Backend unit (`pytest -m "not integration"`) | **23 passed**, 2 deselected |
| Backend integration (`pytest -m integration`) | **2 passed** |
| Frontend (`npm test`) | **5 passed** |
| Frontend (`npm run build`) | **Succeeded** |
| `scripts/audit_analysis.py` | **Succeeded** (MAE/RMSE/bias match audit expectations) |
| Live Render `/api/health` | **HTTP 200** |

Earlier local verification (Docker Compose on port 8080, browser dashboard) is recorded in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

---

## Deployment

**Production hosting:** [Render](https://render.com) at [https://windlens-dt0z.onrender.com/](https://windlens-dt0z.onrender.com/).

| File | Role |
| --- | --- |
| `deploy/Dockerfile.public` | Single container: Vite build + nginx on `$PORT` + Uvicorn on 127.0.0.1:8001 |
| `deploy/start-public.sh` | Starts Uvicorn and nginx |
| `deploy/nginx.public.conf.template` | Same-origin `/api` proxy |
| `render.yaml` | Optional Blueprint (Docker web service, health `/api/health`) |
| `docker-compose.yml` | Local two-service stack (not used on Render) |

Health check path on Render: **`/api/health`**.

Details, env vars, and local verification notes: **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**.

---

## Limitations and future improvements

- **Historical scope:** January 2026 delivery window only; not a live trading or real-time forecasting product.
- **Cutoff assumption:** Default 09:20 Europe/London is configurable but not an official market rule.
- **Elexon dependency:** Availability, schema, and data quality determine whether analysis succeeds (502 on failure; no mock substitution).
- **Incomplete hours:** Missing half-hours are dropped, not imputed.
- **WINDFOR semantics:** Code assumes forecast MW aligns with the hour starting at `startTime`; Elexon schema does not fully document this (see [docs/investigation/API_FINDINGS.md](docs/investigation/API_FINDINGS.md)).
- **Settlement vs UTC date:** Matching uses Elexon `settlementDate` with UTC hour starts; edge cases around DST months are not in scope for January 2026.
- **Cache:** In-memory, per process; cold starts and multiple instances each maintain separate caches.
- **Procurement:** Analytics only—no order execution, scheduling, or market submission.

---

## AI tools and development assistance

Parts of this repository—including documentation, deployment configuration, tests, and UI structure—were developed with **AI-assisted coding in Cursor**, with behaviour validated by **pytest**, **Vitest**, the **audit script**, and manual Docker/browser checks. AI suggestions were not treated as correct without those checks.

---

## Further documentation

| Document | Description |
| --- | --- |
| [docs/PROJECT_REPORT.pdf](docs/PROJECT_REPORT.pdf) | Printable technical report |
| [docs/AUDIT_ANALYSIS.md](docs/AUDIT_ANALYSIS.md) | Analytical pipeline audit |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Docker and Render deployment |
| [docs/LEARNING_GUIDE.md](docs/LEARNING_GUIDE.md) | Conceptual walkthrough |
| [backend/README.md](backend/README.md) | Backend-focused notes |

Generate or refresh the PDF:

```powershell
python -m pip install -r requirements-docs.txt
python scripts/generate_report.py
```
