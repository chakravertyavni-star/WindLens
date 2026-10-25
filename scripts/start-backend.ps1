# Start FastAPI for local WindLens development (Windows PowerShell).
# Run from anywhere: .\scripts\start-backend.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$DevEnv = Join-Path $Root "dev.env"

$Port = 8001
if (Test-Path $DevEnv) {
    Get-Content $DevEnv | ForEach-Object {
        if ($_ -match '^\s*BACKEND_PORT\s*=\s*(\d+)\s*$') {
            $Port = [int]$Matches[1]
        }
    }
}
if ($env:BACKEND_PORT) {
    $Port = [int]$env:BACKEND_PORT
}

Write-Host "WindLens backend -> http://127.0.0.1:$Port (docs: /docs)"
Write-Host "Working directory: $Root"
Write-Host "If bind fails with WinError 10013 or 10048, set BACKEND_PORT in dev.env and match FRONTEND/.env.development"

Set-Location $Root
$env:PYTHONPATH = "backend"
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port $Port --reload
