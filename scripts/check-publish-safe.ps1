# Pre-push safety scan (no secret values printed). Run from repo root before making the repo public.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "WindLens publish safety check (repo root: $Root)"

$ignorePatterns = @(
    "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache",
    "frontend\dist", ".git"
)

function Should-Skip($path) {
    foreach ($p in $ignorePatterns) {
        if ($path -match [regex]::Escape($p)) { return $true }
    }
    return $false
}

$issues = @()

$mustIgnore = @(
    ".env",
    "dev.env",
    "frontend/.env.development",
    "frontend/.env.production",
    "frontend/.env.local"
)

foreach ($rel in $mustIgnore) {
    $full = Join-Path $Root ($rel -replace "/", "\")
    if (Test-Path $full) {
        if (Test-Path (Join-Path $Root ".git")) {
            git check-ignore -q ($rel -replace "\\", "/") 2>$null
            if ($LASTEXITCODE -ne 0) {
                $issues += "Not gitignored (do not commit): $rel"
            }
        } else {
            Write-Host "NOTE: No git repo yet - never upload $rel to a public GitHub repo."
        }
    }
}

$patterns = @(
    "(?i)api[_-]?key\s*=",
    "(?i)password\s*=",
    "(?i)secret\s*=",
    "BEGIN (RSA |OPENSSH )?PRIVATE KEY"
)

Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { -not (Should-Skip $_.FullName) } |
    ForEach-Object {
        $rel = $_.FullName.Substring($Root.Length + 1)
        if ($rel -match "\.(png|pdf|jpg|woff|ico)$") { return }
        try {
            $content = Get-Content -LiteralPath $_.FullName -Raw -ErrorAction Stop
            foreach ($pat in $patterns) {
                if ($content -match $pat) {
                    $issues += "Suspicious pattern in file: $rel"
                    break
                }
            }
        } catch { }
    }

$distJs = Get-ChildItem -Path (Join-Path $Root "frontend\dist\assets\*.js") -ErrorAction SilentlyContinue | Select-Object -First 1
if ($distJs) {
    $js = Get-Content $distJs.FullName -Raw
    if ($js -match "127\.0\.0\.1|localhost:800") {
        $issues += "frontend/dist JS may embed localhost - rebuild with empty VITE_API_BASE_URL"
    }
}

if ($issues.Count -eq 0) {
    Write-Host "OK: No publish blockers detected by this script."
    exit 0
}

Write-Host "Review these items before publishing:"
$issues | ForEach-Object { Write-Host " - $_" }
exit 1
