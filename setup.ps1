Write-Host "== NetGuard AI setup (Windows) ==" -ForegroundColor Cyan

$root = $PSScriptRoot

Write-Host "`n[1/4] Creating backend virtual environment..." -ForegroundColor Yellow
Set-Location "$root\backend"
python -m venv .venv
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

Write-Host "`n[2/4] Installing backend dependencies..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "`n[3/4] Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location "$root\frontend"
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
npm install

Write-Host "`n[4/4] Done." -ForegroundColor Green
Set-Location $root
Write-Host "Run '.\run.ps1' to start both servers, or see README.md for manual steps." -ForegroundColor Cyan
