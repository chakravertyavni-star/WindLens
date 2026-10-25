# Progress Checklist

Last updated: 25 October 2026

## Milestone 3 - WindLens React dashboard

| Item | Status | Evidence |
| --- | --- | --- |
| Vite + React app in `frontend/` | Implemented | `npm run build` succeeded |
| API client module | Implemented | `frontend/src/api/windApi.js` |
| KPI cards from `/api/metrics` | Tested | Browser: MAE 2,142 MW live |
| Forecast vs actual chart | Tested | Recharts + `/api/series` 744 rows |
| Cutoff control | Tested | `?cutoff=` on metrics and series; MAE at 15:30 ≠ 09:20 |
| Loading / error / retry | Implemented | `StatusBanner.jsx` |
| Delivery period table | Implemented | Sort + search |
| Forecast error chart | Implemented | From `forecast_error` field |
| Forecast evolution UI | Planned | Backend lacks full vintage history |
| Vitest | Tested | 3 passed |
| Backend Pytest regression | Tested | 9 passed (not integration) |
| Browser verification | Tested | http://127.0.0.1:5173 on 25 Oct 2026 |
| Screenshot in docs | Implemented | `docs/screenshots/windlens-dashboard.png` |
| Docker / public deploy | Planned | — |

## Milestone 2 - Backend

Completed (see `backend/README.md`).

## Dev environment (Windows)

- Default API port **8001** via `dev.env` + `scripts/start-backend.ps1`
- Vite proxy: `frontend/.env.development` → `VITE_DEV_API_PROXY`
- Verified: `/api/config` via proxy on 5175, live metrics on 8001 (25 Oct 2026)

## Commands verified this milestone

```powershell
.\scripts\start-backend.ps1
.\scripts\start-frontend.ps1
python -m pytest -m "not integration"
cd frontend; npm test; npm run build
```

## Next milestone

Docker Compose (backend + frontend), optional production static hosting, and frontend component tests if desired.
