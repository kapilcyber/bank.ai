# TechBank.ai - Start portal servers in LOCAL mode (this PC only)
# Portals listen on localhost only. Use start-portals.ps1 for network access.
# Usage: .\start-portals-local.ps1  (from techbankai folder)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host ''
Write-Host 'TechBank.ai - Portal Servers (Local Only)' -ForegroundColor Cyan
Write-Host 'Guest: 3005 | Freelancer: 3006 | Employee: 3007' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Access only from this PC:' -ForegroundColor Yellow
Write-Host '  http://localhost:3005/guest' -ForegroundColor Cyan
Write-Host '  http://localhost:3006/freelancer' -ForegroundColor Cyan
Write-Host '  http://localhost:3007/employee' -ForegroundColor Cyan
Write-Host ''
Write-Host 'For network access (other devices), run: .\start-portals.ps1' -ForegroundColor Gray
Write-Host 'Press Ctrl+C to stop all three.' -ForegroundColor Yellow
Write-Host ''
Write-Host 'If links show "closed" or "can''t connect": run this script first so the servers are running.' -ForegroundColor Gray
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
npm run dev:portals:local
