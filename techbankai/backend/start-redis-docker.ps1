# Start Redis using Docker
Write-Host "Starting Redis with Docker..." -ForegroundColor Cyan

# Check if Docker is running
Write-Host "`nChecking Docker status..." -ForegroundColor Yellow
try {
    $dockerCheck = docker ps 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Docker Desktop is not running!" -ForegroundColor Red
        Write-Host "`nPlease start Docker Desktop first:" -ForegroundColor Yellow
        Write-Host "1. Open Docker Desktop from Start menu" -ForegroundColor White
        Write-Host "2. Wait for it to fully start (whale icon in system tray)" -ForegroundColor White
        Write-Host "3. Then run this script again" -ForegroundColor White
        Write-Host "`nOr start Docker Desktop now and wait..." -ForegroundColor Cyan
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
        Write-Host "Waiting 30 seconds for Docker Desktop to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
    }
} catch {
    Write-Host "Docker Desktop is not installed or not accessible." -ForegroundColor Red
    exit 1
}

# Check if Redis container already exists
Write-Host "`nChecking for existing Redis container..." -ForegroundColor Yellow
$existingContainer = docker ps -a --filter "name=redis" --format "{{.Names}}" 2>&1

if ($existingContainer -eq "redis") {
    Write-Host "Redis container found. Checking if it's running..." -ForegroundColor Yellow
    $running = docker ps --filter "name=redis" --format "{{.Names}}" 2>&1
    
    if ($running -eq "redis") {
        Write-Host "Redis is already running!" -ForegroundColor Green
        Write-Host "Redis is available at localhost:6379" -ForegroundColor Green
    } else {
        Write-Host "Starting existing Redis container..." -ForegroundColor Yellow
        docker start redis
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Redis started successfully!" -ForegroundColor Green
            Write-Host "Redis is available at localhost:6379" -ForegroundColor Green
        } else {
            Write-Host "Failed to start Redis container." -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "Creating new Redis container..." -ForegroundColor Yellow
    docker run -d -p 6379:6379 --name redis redis:latest
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Redis started successfully!" -ForegroundColor Green
        Write-Host "Redis is available at localhost:6379" -ForegroundColor Green
    } else {
        Write-Host "Failed to create Redis container." -ForegroundColor Red
        Write-Host "Make sure Docker Desktop is running." -ForegroundColor Yellow
        exit 1
    }
}

# Test the connection
Write-Host "`nTesting Redis connection..." -ForegroundColor Yellow
$testResult = docker exec redis redis-cli ping 2>&1
if ($testResult -eq "PONG") {
    Write-Host "Redis is working correctly! (PONG received)" -ForegroundColor Green
} else {
    Write-Host "Warning: Could not verify Redis connection." -ForegroundColor Yellow
    Write-Host "Response: $testResult" -ForegroundColor Gray
}

Write-Host "`nRedis is ready to use!" -ForegroundColor Green
Write-Host "`nUseful commands:" -ForegroundColor Cyan
Write-Host "  Stop Redis:    docker stop redis" -ForegroundColor White
Write-Host "  Start Redis:   docker start redis" -ForegroundColor White
Write-Host "  Remove Redis:  docker rm -f redis" -ForegroundColor White
Write-Host "  Test Redis:    docker exec redis redis-cli ping" -ForegroundColor White

















