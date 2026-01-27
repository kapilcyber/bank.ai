# Redis Startup Script for Windows
# This script helps you start Redis on Windows

Write-Host "Checking Redis setup options..." -ForegroundColor Cyan

# Option 1: Try Docker (Recommended if Docker Desktop is running)
Write-Host "`n[Option 1] Checking Docker..." -ForegroundColor Yellow
$dockerRunning = $false
try {
    $dockerCheck = docker ps 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dockerRunning = $true
        Write-Host "Docker is running!" -ForegroundColor Green
        
        # Check if Redis container already exists
        $redisExists = docker ps -a --filter "name=redis" --format "{{.Names}}" 2>&1
        if ($redisExists -eq "redis") {
            Write-Host "Redis container found. Starting it..." -ForegroundColor Yellow
            docker start redis
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Redis started successfully!" -ForegroundColor Green
                Write-Host "Redis is running on localhost:6379" -ForegroundColor Green
                exit 0
            }
        } else {
            Write-Host "Creating and starting Redis container..." -ForegroundColor Yellow
            docker run -d -p 6379:6379 --name redis redis:latest
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Redis started successfully!" -ForegroundColor Green
                Write-Host "Redis is running on localhost:6379" -ForegroundColor Green
                exit 0
            }
        }
    }
} catch {
    Write-Host "Docker is not running or not available." -ForegroundColor Red
}

# Option 2: Check if Redis is already running on port 6379
Write-Host "`n[Option 2] Checking if Redis is already running..." -ForegroundColor Yellow
$portCheck = netstat -an | findstr ":6379"
if ($portCheck) {
    Write-Host "Port 6379 is in use. Redis might already be running!" -ForegroundColor Green
    Write-Host "You can verify with: docker exec -it redis redis-cli ping" -ForegroundColor Cyan
    exit 0
}

# Option 3: Instructions for manual setup
Write-Host "`n[Option 3] Manual Setup Required" -ForegroundColor Yellow
Write-Host "`nTo start Redis on Windows, choose one of these options:" -ForegroundColor Cyan
Write-Host ""
Write-Host "A) Start Docker Desktop, then run:" -ForegroundColor White
Write-Host "   docker run -d -p 6379:6379 --name redis redis:latest" -ForegroundColor Gray
Write-Host ""
Write-Host "B) Use WSL (if installed):" -ForegroundColor White
Write-Host "   wsl sudo apt-get update" -ForegroundColor Gray
Write-Host "   wsl sudo apt-get install redis-server" -ForegroundColor Gray
Write-Host "   wsl sudo service redis-server start" -ForegroundColor Gray
Write-Host ""
Write-Host "C) Install native Windows Redis:" -ForegroundColor White
Write-Host "   Download from: https://github.com/microsoftarchive/redis/releases" -ForegroundColor Gray
Write-Host "   Or use Memurai: https://www.memurai.com/" -ForegroundColor Gray
Write-Host ""
Write-Host "D) Use Chocolatey (if installed):" -ForegroundColor White
Write-Host "   choco install redis-64" -ForegroundColor Gray
Write-Host ""







