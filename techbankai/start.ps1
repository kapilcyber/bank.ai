# TechBank.ai - One command to run backend + frontend
# Usage: .\start.ps1  (from techbankai folder)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "`n╔════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   TechBank.ai - Starting Backend + Frontend         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════╝`n" -ForegroundColor Green

# Start backend in a new PowerShell window
$backendScript = Join-Path $root "start-backend.ps1"
if (-not (Test-Path $backendScript)) {
    Write-Host "start-backend.ps1 not found." -ForegroundColor Red
    exit 1
}
Write-Host "Starting backend in a new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$backendScript`"" -WorkingDirectory $root

# Give backend a few seconds to start
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start frontend in current window
$frontendScript = Join-Path $root "start-frontend.ps1"
if (-not (Test-Path $frontendScript)) {
    Write-Host "start-frontend.ps1 not found." -ForegroundColor Red
    exit 1
}
& $frontendScript
