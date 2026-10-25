# WindLens frontend

Vite + React dashboard for the FastAPI wind forecast accuracy API.

## Setup

```bash
cd frontend
npm install
cp .env.example .env
```

From repo root, start the backend first:

```powershell
.\scripts\start-backend.ps1
```

## Development

```powershell
cd C:\websites\ELECTRICITY\frontend
npm run dev
```

Vite proxies `/api` to `VITE_DEV_API_PROXY` in `.env.development` (default **http://127.0.0.1:8001**).

## Production build

Set `VITE_API_BASE_URL` to your API origin, then:

```bash
npm run build
npm run preview
```

## Tests

```bash
npm test
```
