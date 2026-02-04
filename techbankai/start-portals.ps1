# TechBank.ai - Start the three portal servers (Guest 3005, Freelancer 3006, Employee 3007)
# NETWORK MODE: Portals listen on 0.0.0.0 so other devices on your network can access them.
# Usage: .\start-portals.ps1  (from techbankai folder)
# For local-only (this PC only): .\start-portals-local.ps1

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# Your network IP (other devices use these URLs). Change below or set env: $env:TECHBANK_NETWORK_IP = "1.2.3.4"
$networkIP = $env:TECHBANK_NETWORK_IP
if (-not $networkIP) { $networkIP = "192.168.0.107" }

Write-Host ''
Write-Host 'TechBank.ai - Portal Servers (Network Mode)' -ForegroundColor Cyan
Write-Host 'Guest: 3005 | Freelancer: 3006 | Employee: 3007' -ForegroundColor Cyan
Write-Host ''
Write-Host 'On this PC:' -ForegroundColor White
Write-Host '  http://localhost:3005/guest' -ForegroundColor Gray
Write-Host '  http://localhost:3006/freelancer' -ForegroundColor Gray
Write-Host '  http://localhost:3007/employee' -ForegroundColor Gray
Write-Host ''
Write-Host 'On your network (other laptops/PCs):' -ForegroundColor Green
Write-Host "  http://${networkIP}:3005/guest" -ForegroundColor Cyan
Write-Host "  http://${networkIP}:3006/freelancer" -ForegroundColor Cyan
Write-Host "  http://${networkIP}:3007/employee" -ForegroundColor Cyan
Write-Host ''
Write-Host 'Backend: run .\start-backend.ps1 (HOST=0.0.0.0). For network CORS use CORS_ORIGINS=* in backend .env' -ForegroundColor Yellow
Write-Host 'Local-only? Run: .\start-portals-local.ps1 and .\start-backend-local.ps1' -ForegroundColor Yellow
Write-Host 'Press Ctrl+C to stop all three.' -ForegroundColor Yellow
Write-Host ''

$frontendDir = Join-Path $root "frontend"
if (-not (Test-Path $frontendDir)) {
    Write-Host 'Frontend directory not found.' -ForegroundColor Red
    exit 1
}

$nodeModulesPath = Join-Path $frontendDir "node_modules"
if (-not (Test-Path $nodeModulesPath)) {
    Write-Host 'Installing dependencies...' -ForegroundColor Yellow
    Set-Location $frontendDir
    npm install
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Write-Host 'Dependencies installed.' -ForegroundColor Green
}

Set-Location $frontendDir
npm run dev:portals
