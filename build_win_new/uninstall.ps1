<#
.SYNOPSIS
    Geometry AI Server v1.0.0.0707 - Uninstall script
#>

$Host.UI.RawUI.WindowTitle = "Geometry AI Server - Uninstall"

if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "[!] Run as Administrator" -ForegroundColor Red
    pause; exit 1
}

Write-Host ""
Write-Host "  Geometry AI Server v1.0.0.0707 - Uninstall" -ForegroundColor Cyan
Write-Host ""

$AppDir = Join-Path $env:ProgramFiles "GeometryAI"

Write-Host "[1/4] Stopping services..." -ForegroundColor Cyan
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "GeometryAI Server" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "GeometryAI Open WebUI" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "  Services stopped" -ForegroundColor Green

Write-Host "[2/4] Removing firewall rules..." -ForegroundColor Cyan
try {
    Remove-NetFirewallRule -DisplayName "Geometry AI Server" -ErrorAction SilentlyContinue
    Remove-NetFirewallRule -DisplayName "Geometry AI Server (8080)" -ErrorAction SilentlyContinue
    Write-Host "  Firewall rules removed" -ForegroundColor Green
} catch {}

$confirmData = Read-Host "Delete vector database and logs? (y/N)"
if ($confirmData -eq "y" -or $confirmData -eq "Y") {
    if (Test-Path $AppDir) {
        Remove-Item -Recurse -Force (Join-Path $AppDir "chroma_db") -ErrorAction SilentlyContinue
        Remove-Item -Recurse -Force (Join-Path $AppDir "logs") -ErrorAction SilentlyContinue
        Remove-Item -Recurse -Force (Join-Path $AppDir "models_cache") -ErrorAction SilentlyContinue
    }
    Write-Host "  Runtime data deleted" -ForegroundColor Green
}

$confirmDir = Read-Host "Delete entire installation directory? (y/N)"
if ($confirmDir -eq "y" -or $confirmDir -eq "Y") {
    if (Test-Path $AppDir) {
        Remove-Item -Recurse -Force $AppDir -ErrorAction SilentlyContinue
    }
    Write-Host "  Installation directory deleted" -ForegroundColor Green
}

try {
    $DesktopPath = [Environment]::GetFolderPath("Desktop")
    $ShortcutPath = Join-Path $DesktopPath "Geometry AI Server.url"
    if (Test-Path $ShortcutPath) { Remove-Item -Force $ShortcutPath }
}

Write-Host ""
Write-Host "[OK] Uninstall complete" -ForegroundColor Green
pause
