# Quick Redis Fix for Windows

## The Problem
You tried to use Linux commands (`sudo apt-get install redis-server`) in PowerShell on Windows. These commands don't work on Windows.

## The Solution

### Option 1: Use Docker (Easiest - Recommended)

1. **Start Docker Desktop** (if not already running)
   - Look for Docker Desktop in your Start menu and launch it
   - Wait for it to fully start (whale icon in system tray)

2. **Run this command in PowerShell:**
   ```powershell
   docker run -d -p 6379:6379 --name redis redis:latest
   ```

3. **Verify it's running:**
   ```powershell
   docker ps
   ```
   You should see a container named "redis" running.

4. **Test the connection:**
   ```powershell
   docker exec -it redis redis-cli ping
   ```
   Should return: `PONG`

### Option 2: Use WSL (If you have a Linux distribution)

If you have Ubuntu or another Linux distro in WSL:

```powershell
wsl
# Now you're in WSL, run:
sudo apt-get update
sudo apt-get install redis-server
sudo service redis-server start
```

### Option 3: Install Redis for Windows

1. Download Redis for Windows from:
   - https://github.com/microsoftarchive/redis/releases
   - Or use Memurai: https://www.memurai.com/

2. Extract and run `redis-server.exe`

## Quick Commands Reference

**Start Redis (Docker):**
```powershell
docker run -d -p 6379:6379 --name redis redis:latest
```

**Stop Redis (Docker):**
```powershell
docker stop redis
```

**Start existing Redis container:**
```powershell
docker start redis
```

**Check if Redis is running:**
```powershell
docker ps | findstr redis
```

**Test Redis connection:**
```powershell
docker exec -it redis redis-cli ping
```







