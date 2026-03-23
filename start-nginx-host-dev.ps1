# Start nginx reverse proxy on port 80 → Vite :3005 + API (Docker).
# Requires Docker Desktop. Backend and frontend must run on the host first.
#
# Usage (from repo root):
#   .\start-nginx-host-dev.ps1
#   .\start-nginx-host-dev.ps1 -BackendPort 8002

param(
    [int] $BackendPort = 8000
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

$dockerExe = "${env:ProgramFiles}\Docker\Docker\resources\bin\docker.exe"
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    if (Test-Path $dockerExe) {
        $env:PATH = "$(Split-Path $dockerExe -Parent);$env:PATH"
    } else {
        Write-Host "Docker not found. Install Docker Desktop (winget install Docker.DockerDesktop), or use native nginx:" -ForegroundColor Yellow
        Write-Host "  nginx\nginx.host-dev-native.conf (edit api_dev port if needed)" -ForegroundColor Cyan
        exit 1
    }
}

$env:BACKEND_UPSTREAM = "host.docker.internal:$BackendPort"
$env:FRONTEND_UPSTREAM = "host.docker.internal:3005"

Write-Host "Starting nginx proxy on http://localhost (port 80)..." -ForegroundColor Green
Write-Host "  Frontend upstream: $($env:FRONTEND_UPSTREAM)" -ForegroundColor Gray
Write-Host "  Backend upstream:  $($env:BACKEND_UPSTREAM)" -ForegroundColor Gray
Write-Host ""
Write-Host "Ensure frontend runs with:  cd frontend; npm run dev:behind-proxy" -ForegroundColor Yellow
Write-Host "Ensure backend runs on port $BackendPort with --host 0.0.0.0" -ForegroundColor Yellow
Write-Host ""

Set-Location $root
docker compose -f docker-compose.host-dev.yml up
