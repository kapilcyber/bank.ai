# TechBank.ai Backend - LOCAL mode (this PC only)
# Binds to 127.0.0.1 so only this machine can reach the API.
# For network access (other devices), use: .\start-backend.ps1

Write-Host "`n╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   TechBank.ai Backend - LOCAL (this PC only)     ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$backendDir = Join-Path $PSScriptRoot "backend"
if (-not (Test-Path $backendDir)) {
    Write-Host "Backend directory not found!" -ForegroundColor Red
    exit 1
}

Set-Location $backendDir

$venvPath = Join-Path $backendDir "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) { exit 1 }
}
& "$venvPath\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) { exit 1 }

$envFile = Join-Path $backendDir ".env"
if (-not (Test-Path $envFile)) {
    Write-Host ".env file not found! Run .\start-backend.ps1 once to create it." -ForegroundColor Red
    exit 1
}

$fastapiInstalled = python -c "import fastapi" 2>&1
if ($LASTEXITCODE -ne 0) {
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "Backend is already running on http://127.0.0.1:8000" -ForegroundColor Yellow
        exit 0
    }
} catch { }

# Bind to localhost only
$env:HOST = "127.0.0.1"
$env:PORT = "8000"

Write-Host "Starting backend (local only: 127.0.0.1:8000)..." -ForegroundColor Green
Write-Host "  http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop.`n" -ForegroundColor Yellow

python -m src.main
