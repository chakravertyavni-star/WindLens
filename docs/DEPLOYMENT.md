# WindLens deployment guide

This document describes how to publish the existing React + FastAPI application. **No public deployment is configured or verified in this repository** until you deploy and test your own public URL.

## Architecture

| Layer | Role |
| --- | --- |
| **Browser** | WindLens SPA (static files) |
| **Edge** | nginx — serves `frontend/dist` and proxies `/api` to FastAPI |
| **API** | FastAPI on port 8001 (internal) — analysis, Elexon fetch, in-memory source cache |
| **Elexon** | Outbound HTTPS to `data.elexon.co.uk` (no API key in repo) |

**Persistent storage:** Not required. The app does not use a database or disk cache. Historical data is fetched from Elexon (or served from the in-process TTL cache). Platform volumes are optional only if you add snapshots later.

**In-memory cache:** `ELEXON_SOURCE_CACHE_TTL_SECONDS` is **per process**. Multiple Uvicorn workers or scaled containers each hold their own cache. Cold starts re-fetch Elexon after deploy or scale-out.

## Recommended hosting (assignment-friendly)

| Provider | Fit | Why |
| --- | --- | --- |
| **[Render](https://render.com)** (recommended) | **Single Docker web service** | One public URL, GitHub deploy, Dockerfile support, health checks, free compute plan for demos. Matches `deploy/Dockerfile.public` + optional `render.yaml`. |
| **Railway** | Docker Compose or separate services | Good DX; free trial then limited credit — often needs **two** services (static + API) or a custom single container like Render. |
| **Fly.io** | Separate Machines or one Dockerfile | Outbound HTTPS works; free allowances change — more setup than Render for a monolith. |
| **VPS + `docker compose`** | Two-container stack as verified locally | Full control; you manage TLS and DNS (may cost more than $0). |

Official references (checked October 2025):

- Render free web services: [Deploy for Free](https://render.com/docs/free) — 0.1 CPU / 512 MB RAM, **spin down after 15 minutes idle**, ~**1 minute** cold start, **750 instance-hours/month** per workspace, ephemeral filesystem, no persistent disks on free tier.
- Render web services: bind HTTP to **`$PORT`** (default **10000**), [Web Services](https://render.com/docs/web-services).
- Render Docker deploys: set **Dockerfile path** and context in the dashboard or Blueprint.

## How the frontend finds the API

| Mode | Configuration | Requests |
| --- | --- | --- |
| **Local dev** | `VITE_API_BASE_URL` empty; `frontend/.env.development` sets `VITE_DEV_API_PROXY` | Browser → Vite → FastAPI (`/api` proxy) |
| **Production same-origin** | `VITE_API_BASE_URL` empty at build time; reverse proxy routes `/api` | Browser → nginx → FastAPI |
| **Production split-origin** | `VITE_API_BASE_URL=https://api.example.com` at build time | Browser → API host directly (CORS required) |

The Vite dev proxy is **not** used in production builds.

## Local production-style stack (Docker Compose) — **verified**

Requires Docker Desktop:

```powershell
cd C:\websites\ELECTRICITY
docker compose up --build
```

Open **http://localhost:8080** — static app with `/api` proxied to the `backend` service.

### Verified locally (25 October 2026)

| Service | Status |
| --- | --- |
| `electricity-backend-1` | Running, healthy (internal port 8001) |
| `electricity-web-1` | Running, **8080→80** |

| URL | HTTP | Result |
| --- | ---: | --- |
| `http://localhost:8080/` | 200 | WindLens SPA |
| `http://localhost:8080/api/health` | 200 | `{"status":"ok"}` |
| `http://localhost:8080/api/config` | 200 | January 2026 window, cutoff 09:20 |
| `http://localhost:8080/api/metrics` | 200 | n=744, MAE≈2142.12, RMSE≈2611.70, bias≈+1851.90 |
| `http://localhost:8080/api/series?limit=2000` | 200 | count=744 |

Browser check: dashboard, KPIs, insight banner, Forecast Analysis table, cutoff **Recalculate**, **Historical analysis** disclaimer visible.

## Single-container public image — **verified locally (25 October 2026)**

For PaaS that expose one HTTP port (`$PORT`), use `deploy/Dockerfile.public` (nginx on `$PORT` + Uvicorn on `127.0.0.1:8001`).

```powershell
docker build -f deploy/Dockerfile.public -t windlens-public:test .
docker run --rm -p 10000:10000 -e PORT=10000 windlens-public:test
```

Verified on the same date:

| URL | HTTP |
| --- | ---: |
| `http://127.0.0.1:10000/api/health` | 200 |
| `http://127.0.0.1:10000/api/metrics` | 200 (live Elexon, n=744) |

**Not verified:** Render/Fly/Railway dashboards, TLS, or `*.onrender.com` URL (you must deploy and test).

## Publish on Render (step-by-step) — **unverified on Render**

These steps follow Render’s documented model; only local Docker above is verified in-repo.

1. **Prepare GitHub (your action)**
   - Initialize git if needed: `git init`, commit project files.
   - Run `.\scripts\check-publish-safe.ps1` — do **not** commit `.env`, `dev.env`, `frontend/.env.development`, or `frontend/.env.production`.
   - Push to a **public or private** GitHub repo (assignment may require public — your choice).

2. **Create Render account (free)** — [render.com](https://render.com). No payment method required for free web services unless you exceed included bandwidth/build minutes (see [free tier docs](https://render.com/docs/free)).

3. **New Web Service**
   - Connect the GitHub repository.
   - **Runtime:** Docker.
   - **Dockerfile path:** `deploy/Dockerfile.public`
   - **Docker context:** repository root (`.`)
   - **Plan:** Free (expect idle spin-down and cold starts).
   - **Health check path:** `/api/health`
   - Leave **`VITE_API_BASE_URL` unset** at build (default empty in Dockerfile = same-origin `/api`).

4. **Environment variables (Render dashboard)**

   | Key | Suggested value | Notes |
   | --- | --- | --- |
   | `ELEXON_SOURCE_CACHE_TTL_SECONDS` | `3600` | Optional; reduces Elexon traffic |
   | `CORS_ALLOWED_ORIGINS` | `*` | OK for same-origin monolith; restrict if you split hosts later |
   | `PORT` | *(set by Render)* | Do not override unless docs require it |

   Optional analysis overrides: see `.env.example` (`DELIVERY_*`, `DECISION_CUTOFF_*`, etc.).

5. **Deploy** — wait for build + “Live”. Open `https://<service-name>.onrender.com/`.

6. **Acceptance test (you must run on the public URL)**

   ```text
   GET https://<your-host>/api/health          → 200
   GET https://<your-host>/api/metrics         → 200, n=744 at default cutoff
   GET https://<your-host>/                     → SPA loads, disclaimer visible
   ```

   First request after idle may show Render’s loading page for ~1 minute; retry if needed.

### Optional: Render Blueprint

Repository root `render.yaml` defines a free Docker web service with `healthCheckPath: /api/health`. In Render: **New → Blueprint**, connect repo, review plan, deploy. **Unverified** until you apply it in your workspace.

## Backend-only Docker (split hosting)

```bash
docker build -f backend/Dockerfile -t windlens-api .
docker run --rm -p 8001:8001 \
  -e ELEXON_SOURCE_CACHE_TTL_SECONDS=3600 \
  -e CORS_ALLOWED_ORIGINS=https://your-static-site.example.com \
  windlens-api
```

Build frontend with `VITE_API_BASE_URL=https://your-api.example.com` and host `frontend/dist/` on any static host.

Health check: `GET /api/health` → `{"status":"ok"}` (does not call Elexon).

Analysis routes return **502** with JSON `detail` if Elexon is unreachable. No mock data is substituted.

## Environment variables (backend)

See repository `.env.example`. Secrets are not required for public Elexon Insights endpoints.

| Variable | Purpose |
| --- | --- |
| `ELEXON_BASE_URL` | Elexon API base (default public Insights URL) |
| `DELIVERY_START_DATE` / `DELIVERY_END_DATE` | Analysis window |
| `DECISION_CUTOFF_*` | Analytical cutoff (not a market gate) |
| `WINDFOR_PUBLISH_FROM` / `WINDFOR_PUBLISH_TO` | WINDFOR download window |
| `ELEXON_SOURCE_CACHE_TTL_SECONDS` | Raw source cache TTL (`0` = always fetch) |
| `CORS_ALLOWED_ORIGINS` | `*` or comma-separated HTTPS origins for split hosting |

Load order: repository root `.env`, then process environment (platform overrides).

## Frontend (production build)

```bash
cd frontend
cp .env.production.example .env.production
# Edit VITE_API_BASE_URL only if API is on another host
npm ci
npm run build
```

Deploy `frontend/dist/` to any static host when not using the single-container image.

## CORS

- **Same-origin** (nginx proxy or single host): CORS is irrelevant for browser calls to `/api`.
- **Split-origin:** Set `CORS_ALLOWED_ORIGINS` on the API to your static site origin(s).

## Validation checklist

```powershell
# Backend
$env:PYTHONPATH='backend'
python -m pytest tests -m "not integration" -q

# Frontend
cd frontend
npm test
npm run build

# Publish safety (no secrets printed)
.\scripts\check-publish-safe.ps1

# Local two-container stack
docker compose up --build

# Local single-container (PaaS-style)
docker build -f deploy/Dockerfile.public -t windlens-public:test .
docker run --rm -p 10000:10000 -e PORT=10000 windlens-public:test
```

After production build, confirm `frontend/dist` does not embed `127.0.0.1` unless you intentionally set `VITE_API_BASE_URL`.

## Repository hazards (review before publish)

| Item | Action |
| --- | --- |
| `.env`, `dev.env`, `frontend/.env.development`, `frontend/.env.production` | Listed in `.gitignore` — never commit |
| Elexon API key | Not used |
| `frontend/dist/` | Gitignored — build in CI or on the host |
| Hardcoded localhost in production bundle | Use empty `VITE_API_BASE_URL` for same-origin deploy |
| `CORS_ALLOWED_ORIGINS=*` | Acceptable for monolith demo; restrict for split-origin production |

## Disclaimers in the UI

Do not remove the **Historical analysis** / non-trading disclaimers from the header or methodology copy when deploying publicly.
