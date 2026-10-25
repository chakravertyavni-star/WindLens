# Frontend data flow (WindLens)

Status: **implemented** in `frontend/src/`.

```mermaid
flowchart LR
    U[User browser] --> APP[React App.jsx]
    APP --> HOOK[useAnalysis hook]
    HOOK --> API[windApi.js]
    API -->|GET /api/config| BE[FastAPI]
    API -->|GET /api/metrics?cutoff=| BE
    API -->|GET /api/series?cutoff=&limit=2000| BE
    BE --> ELEXON[Elexon or analysis engine]
    HOOK --> KPI[KpiGrid]
    HOOK --> CHART[ForecastChart / ErrorChart]
    HOOK --> TABLE[PeriodTable]
    APP --> PAGES[Overview / ForecastAnalysis / Methodology]
    APP --> SETTINGS[AnalysisSettings]
    SETTINGS -->|Recalculate| HOOK
```

## Beginner-friendly explanation

The React page does not talk to Elexon directly. It asks our Python API for JSON. One hook (`useAnalysis`) loads configuration once, then loads metrics and series whenever you click **Recalculate** with a new cutoff time.

The chart and table read the same `series` array. Date filters on the chart only hide points visually; the KPI cards always reflect the full matched sample returned by `/api/metrics` for that cutoff.

## Interview-ready definition

WindLens is a React single-page application that consumes a REST JSON API, separates fetch logic in `windApi.js`, and keeps presentation in presentational components fed by hooks.
