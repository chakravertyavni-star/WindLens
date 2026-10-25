# Learning Guide

This guide is for the person who will present the project. It explains the ideas used in *this* repository, not generic web development.

Current project status: **WindLens** (Milestone 3) is a working Vite + React dashboard on top of the FastAPI backend. Both were verified on 25 October 2026.

## 1. What problem we are solving

A UK electricity utility must buy power before its customers use it. A large part of GB generation is wind. Wind changes with the weather, so the buyer needs a forecast of national wind generation.

This product will help the buyer answer two questions:

1. What wind forecast was available when a purchasing decision had to be made?
2. How accurate were those forecasts compared with what actually happened in January 2026?

The product will not buy electricity and will not calculate the company's complete procurement volume. Demand and other fuels are out of scope.

**Interview-ready definition:** This is a decision-support and forecast-accuracy application for national UK wind generation, using Elexon WINDFOR forecasts and FUELHH actuals for January 2026 delivery periods.

## 2. What the WindLens frontend does

**Simple explanation:** WindLens is the dashboard. It asks the Python API for numbers and draws charts and tables.

**Technical explanation:** `frontend/src/App.jsx` provides sidebar navigation (Overview, Forecast Analysis, Methodology), shared cutoff draft vs applied cutoff, and optional chart date range. `useAnalysis` fetches `/api/config`, `/api/metrics`, and `/api/series`. Pages and presentational components render props only — they do not call `fetch` themselves.

| View / component | Data source |
| --- | --- |
| `OverviewPage` / `InsightBanner`, `KpiGrid` | `metricsPayload.metrics` and `.coverage` |
| `OverviewPage` / `ForecastChart` | `seriesPayload.series` (`forecast_mw`, `actual_mw`) |
| `ForecastAnalysisPage` / `ErrorChart`, `PeriodTable` | same series (`forecast_error`) |

**How to run**

```powershell
.\scripts\start-backend.ps1
.\scripts\start-frontend.ps1
```

Open http://127.0.0.1:5173 (Vite proxies `/api` to port **8001** by default).

Screenshot: `docs/screenshots/windlens-dashboard.png`.

**Interview-ready definition:** WindLens is a React SPA that consumes a REST JSON API through a dedicated client module and separates data fetching (hooks) from UI (components).

## 3. What the backend does

The backend is the engine, built with FastAPI and Pandas.

It will:

- fetch or load Elexon data
- clean timestamps
- choose the fair historical forecast
- match that forecast to the actual
- calculate accuracy metrics
- return JSON

**Simple explanation:** the backend does the thinking; the frontend does the showing.

**Technical explanation:** FastAPI will expose HTTP routes. Pandas DataFrames will hold forecasts and actuals. Pure Python functions will implement selection and metrics so they can be unit-tested without starting a web server.

## 4. What an API is

**Simple explanation:** an API is a menu of questions one program can ask another.

**Technical explanation:** the Elexon Insights API is a public HTTPS JSON service. Our future backend will also expose an API that the React app calls.

**Example:** our investigation asked:

`GET https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?settlementDateFrom=2026-01-01&settlementDateTo=2026-01-31&fuelType=WIND`

Elexon answered with 1,488 JSON objects.

**Interview-ready definition:** an API is a documented contract for requesting and receiving structured data over HTTP.

## 5. How JSON will flow between frontend and backend

```text
Browser React app
    |  GET /api/accuracy?cutoff=09:20
    v
FastAPI backend
    |  JSON { mae, rmse, bias, coverage, series: [...] }
    v
React chart components
```

JSON is just text that both JavaScript and Python understand. The frontend will not receive raw Elexon dumps. It should receive already-selected and already-matched results.

Run `uvicorn app.main:app --app-dir backend --port 8000` and open `/docs`. Routes `/api/metrics` and `/api/series` return JSON from the analysis engine.

## 6. How Pandas will process generation data

Pandas is a Python library for tables.

**Simple explanation:** think of Excel, but in code.

**Technical explanation:** each Elexon record becomes a row. Columns will include `start_time`, `publish_time`, `forecast_mw`, and `actual_mw`. We will filter, sort, join, and aggregate those columns.

**Example:** after loading FUELHH WIND rows, Pandas can group two half-hour actuals that belong to the same clock hour and average them so they can be compared with an hourly WINDFOR value.

## 7. How forecast selection works

For each delivery period:

1. Compute the configured cutoff.
2. Keep forecasts with `publishTime <= cutoff`.
3. Keep the forecast with the latest remaining `publishTime`.
4. Never keep a forecast published after delivery when judging a historical decision.

**Example:** delivery `2026-01-01T00:00:00Z`. Default cutoff is 09:20 Europe/London on 31 December 2025. A forecast published at 04:30 UTC on 31 December is eligible. A forecast published at 11:30 UTC on 31 December is not.

**Interview-ready definition:** as-of forecast selection means using the latest information that would have been available at a historical decision time, not the latest information available now.

## 8. How MAE, RMSE, and bias work

We will use:

`forecast error = forecast generation - actual generation`

| Metric | What it tells you |
| --- | --- |
| MAE | Typical size of the mistake, ignoring direction |
| RMSE | Typical size, but large mistakes count more |
| Bias | Direction. Positive means overestimates. Negative means underestimates. |

Synthetic example, not Elexon data:

| Period | Forecast | Actual | Error |
| --- | --- | --- | --- |
| A | 100 | 90 | 10 |
| B | 80 | 100 | -20 |

- MAE = (10 + 20) / 2 = 15
- RMSE = sqrt((100 + 400) / 2) = 15.81
- Bias = (10 - 20) / 2 = -5

The negative bias means these two forecasts, as a pair, underestimated.

Missing actuals will be excluded. They will not be replaced with zero.

## 9. How to run tests

```bash
python -m pytest -m "not integration"
python -m pytest -m integration
```

Ten tests existed and passed on 25 October 2026 (nine unit/API, one live Elexon).

Tests will use tiny labelled synthetic tables so we can prove the selection and metric functions without calling Elexon.

## 10. How Docker will work in this project

Docker packages the app so another computer can run the same setup.

The planned local path is Docker Compose: one container for the frontend, one for the backend. That fileset has not been written.

**Interview-ready definition:** Docker is used here for reproducible local development and later public deployment, not for a complex multi-service platform.

## 11. How to explain the project in an interview

Use this sequence:

1. Business: a utility must buy power before delivery and wind is weather-driven.
2. Scope: national wind only, January 2026, Elexon FUELHH and WINDFOR.
3. Key idea: historical decision-time forecast selection, not latest-available forecast.
4. Data facts: live API confirmed complete January actuals and historical forecasts. Forecasts are hourly; actuals are half-hourly.
5. Metrics: MAE, RMSE, bias, plus coverage.
6. Architecture: React dashboard, FastAPI/Pandas engine, no database.
7. Honesty: Milestone 1 documented and verified the data. The app itself is the next milestone.

If asked what you personally understand, explain `startTime` versus `publishTime`, why a post-cutoff forecast is invalid, and why a missing actual must not become zero.
