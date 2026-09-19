# Starts the backend and frontend dev servers in separate windows.
$root = $PSScriptRoot

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

Write-Host "Backend starting at http://localhost:8000 (docs at /docs)" -ForegroundColor Cyan
Write-Host "Frontend starting at http://localhost:5173" -ForegroundColor Cyan
