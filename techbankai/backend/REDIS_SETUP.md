# Redis Setup Guide

This application requires Redis to be running for Celery background tasks.

## Quick Start

### Option 1: Using Docker (Recommended)

If you have Docker installed:

```powershell
docker run -d -p 6379:6379 --name redis redis:latest
```

To stop Redis:
```powershell
docker stop redis
docker rm redis
```

### Option 2: Using WSL (Windows Subsystem for Linux)

If you have WSL installed:

```bash
# In WSL terminal
sudo apt-get update
sudo apt-get install redis-server
sudo service redis-server start
```

### Option 3: Native Windows Redis

1. Download Redis for Windows from:
   - https://github.com/microsoftarchive/redis/releases
   - Or use Memurai (Redis-compatible): https://www.memurai.com/

2. Extract and run `redis-server.exe`

3. Redis will start on `localhost:6379` by default

## Verify Redis is Running

Test the connection:

```powershell
# If using Docker
docker exec -it redis redis-cli ping
# Should return: PONG

# If using WSL
redis-cli ping
# Should return: PONG

# If using native Windows
# Use Redis CLI that comes with the installation
redis-cli.exe ping
# Should return: PONG
```

## Starting the Celery Worker

Once Redis is running, start the Celery worker:

```powershell
# From the backend directory
python -m celery -A src.workers.celery_app worker --loglevel=info --pool=solo

# Or use the helper script (checks Redis first)
python -m src.workers.start_worker
```

## Troubleshooting

### Error: "Error 10061 connecting to localhost:6379"

This means Redis is not running. Start Redis using one of the methods above.

### Error: "Redis Python package not installed"

Install Redis Python client:
```powershell
pip install redis
```

### Redis Connection Refused

1. Check if Redis is running:
   ```powershell
   # Docker
   docker ps | findstr redis
   
   # WSL
   sudo service redis-server status
   ```

2. Check if port 6379 is available:
   ```powershell
   netstat -an | findstr 6379
   ```

3. Verify Redis URL in your `.env` file:
   ```
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

## Configuration

Redis connection settings can be configured via environment variables:

- `CELERY_BROKER_URL`: Redis broker URL (default: `redis://localhost:6379/0`)
- `CELERY_RESULT_BACKEND`: Redis result backend URL (default: `redis://localhost:6379/0`)

These are set in `src/config/settings.py` and can be overridden in your `.env` file.







