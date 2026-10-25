# Start Vite dev server from FRONTEND (Windows PowerShell).
# Run from anywhere: .\scripts\start-frontend.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Frontend = Join-Path $Root "frontend"

if (-not (Test-Path (Join-Path $Frontend "package.json"))) {
    throw "frontend/package.json not found at $Frontend"
}

Write-Host "WindLens frontend -> npm run dev (see terminal for port, usually 5173 or 5174)"
Write-Host "API proxy target is set in frontend/.env.development (VITE_DEV_API_PROXY)"
Set-Location $Frontend
npm run dev
