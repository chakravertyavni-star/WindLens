# UK Wind Generation Forecast Accuracy (WindLens)

Decision-support and forecast-accuracy project for a UK electricity utility. National Elexon wind forecasts (`WINDFOR`) and actuals (`FUELHH`, `fuelType=WIND`) for **January 2026** delivery periods.

## Current status

Working WindLens dashboard, FastAPI analysis engine, documented correctness audit, and in-process Elexon source cache. **Public deployment is not live** — see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) to publish.

## Windows local development (PowerShell)

Use **two terminals**. Do **not** run `npm` inside `backend\` (Python only).

### One-time setup (repo root: `C:\websites\ELECTRICITY`)

```powershell
cd C:\websites\ELECTRICITY
python -m pip install -r requirements.txt
Copy-Item dev.env.example dev.env
Copy-Item .env.example .env
cd frontend
npm install
```

### Terminal 1 — FastAPI backend

```powershell
cd C:\websites\ELECTRICITY
.\scripts\start-backend.ps1
```

Default URL: **http://127.0.0.1:8001** (Swagger: `/docs`, health: `/api/health`).

Port **8001** avoids common Windows issues on **8000** (`dev.env` + `frontend/.env.development` must match).

### Terminal 2 — React frontend

```powershell
cd C:\websites\ELECTRICITY
.\scripts\start-frontend.ps1
```

Open the URL Vite prints (often **http://127.0.0.1:5173**).

### How the API URL works

| Environment | Mechanism |
| --- | --- |
| **Dev** | Empty `VITE_API_BASE_URL`; Vite proxies `/api` → `VITE_DEV_API_PROXY` (default `http://127.0.0.1:8001`) |
| **Production build** | Set `VITE_API_BASE_URL` in `.env.production` **or** leave empty when nginx (or similar) proxies `/api` on the same host |

See `frontend/.env.production.example`.

### Tests and build

```powershell
cd C:\websites\ELECTRICITY
$env:PYTHONPATH='backend'
python -m pytest -m "not integration"
cd frontend
npm test
npm run build
```

### Local production-style stack (Docker)

Requires Docker Desktop:

```powershell
cd C:\websites\ELECTRICITY
docker compose up --build
```

App: **http://localhost:8080** (nginx → static UI + `/api` → backend).

## Deployment

Full guide: **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** — local Docker (verified), Render single-container steps (unverified until you deploy), repository safety checks, and environment variables.

Backend details: [backend/README.md](backend/README.md).

## Documentation

- `docs/PROJECT_REPORT.pdf` — printable report
- `docs/AUDIT_ANALYSIS.md` — analytical correctness audit
- `docs/LEARNING_GUIDE.md` — beginner explanation
- `docs/PROGRESS.md` — checklist

## Generate the PDF

```powershell
python -m pip install -r requirements-docs.txt
python scripts/generate_report.py
```
