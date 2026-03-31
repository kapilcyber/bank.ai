#Requires -Version 5.1
<#
.SYNOPSIS
  Starts native nginx on :8080 → main Vite :3005, portals :3008/:3006/:3007, API :8002 (no Docker).

.PARAMETER Reload
  If nginx is already running with this setup, reload config instead of starting.

.PARAMETER Stop
  Stop nginx (same prefix as last start from this install).

.EXAMPLE
  .\scripts\start-nginx-local-reverse-proxy.ps1
#>
param(
    [switch] $Reload,
    [switch] $Stop
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$conf = Join-Path $root "nginx\nginx.host-dev-native.conf"

if (-not (Test-Path $conf)) {
    Write-Host "Missing config: $conf" -ForegroundColor Red
    exit 1
}

function Find-NginxInstall {
    $candidates = @()
    if (Get-Command nginx -ErrorAction SilentlyContinue) {
        $cmd = (Get-Command nginx).Source
        $dir = Split-Path $cmd -Parent
        if (Test-Path (Join-Path $dir "conf\mime.types")) { return @{ Exe = $cmd; Prefix = $dir } }
    }
    $wingetRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if (Test-Path $wingetRoot) {
        Get-ChildItem -Path $wingetRoot -Recurse -Filter "nginx.exe" -ErrorAction SilentlyContinue | ForEach-Object {
            $exe = $_.FullName
            $prefix = $_.Directory.FullName
            if (Test-Path (Join-Path $prefix "conf\mime.types")) {
                $candidates += @{ Exe = $exe; Prefix = $prefix }
            }
        }
    }
    if ($candidates.Count -eq 0) { return $null }
    return $candidates | Select-Object -First 1
}

$install = Find-NginxInstall
if (-not $install) {
    Write-Host "nginx.exe not found. Install with: winget install nginxinc.nginx" -ForegroundColor Red
    Write-Host "Then re-open PowerShell (PATH) or run this script again." -ForegroundColor Yellow
    exit 1
}

$nginxExe = $install.Exe
$prefix = $install.Prefix

Push-Location $prefix
try {
    if ($Stop) {
        Write-Host "Stopping nginx (prefix: $prefix)..." -ForegroundColor Yellow
        Start-Process -FilePath $nginxExe -ArgumentList "-p `"$prefix`" -s stop" -NoNewWindow -Wait | Out-Null
        exit 0
    }

    $testProc = Start-Process -FilePath $nginxExe -ArgumentList "-p `"$prefix`" -c `"$conf`" -t" -NoNewWindow -Wait -PassThru
    if ($testProc.ExitCode -ne 0) {
        Write-Host "nginx -t failed." -ForegroundColor Red
        exit 1
    }

    if ($Reload) {
        Write-Host "Reloading nginx..." -ForegroundColor Green
        Start-Process -FilePath $nginxExe -ArgumentList "-p `"$prefix`" -c `"$conf`" -s reload" -NoNewWindow -Wait | Out-Null
        exit 0
    }

    $ips = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown" } |
        Select-Object -ExpandProperty IPAddress

    Write-Host ""
    Write-Host "nginx: $nginxExe" -ForegroundColor Gray
    Write-Host "prefix: $prefix" -ForegroundColor Gray
    Write-Host "config: $conf" -ForegroundColor Gray
    Write-Host ""
    Write-Host "http://127.0.0.1:8080/" -ForegroundColor Green
    foreach ($ip in $ips) { Write-Host "http://$ip:8080/" -ForegroundColor Green }
    Write-Host "  /guest /freelancer /employee" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "Needs: backend :8002, npm run dev:behind-proxy, npm run dev:portals:proxy" -ForegroundColor Yellow
    Write-Host "Firewall: New-NetFirewallRule -DisplayName 'nginx dev HTTP 8080' -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow  (Admin)" -ForegroundColor DarkYellow
    Write-Host "Reload config: .\scripts\start-nginx-local-reverse-proxy.ps1 -Reload" -ForegroundColor DarkGray
    Write-Host "Stop:        .\scripts\start-nginx-local-reverse-proxy.ps1 -Stop" -ForegroundColor DarkGray
    Write-Host ""

    Start-Process -FilePath $nginxExe -ArgumentList "-p `"$prefix`" -c `"$conf`"" -NoNewWindow -Wait | Out-Null
}
finally {
    Pop-Location
}
